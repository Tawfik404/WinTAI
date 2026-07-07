import logging
from pathlib import Path
from typing import Callable, Optional

from moonshine_voice import ModelArch, get_model_for_language, Transcriber
from moonshine_voice.transcriber import TranscriptEventListener

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Repository root is 5 levels up from this file:
#   apps/backend/app/services/stt/moonshine_service.py
_repo_root = Path(__file__).resolve().parents[5]
STT_MODEL_DIR = _repo_root / "models" / "stt"


class MoonshineSTT:
    """Singleton wrapper around the Moonshine Transcriber.

    The Moonshine model is loaded exactly once in ``initialize()`` and
    never reloaded until the backend restarts. Every call to
    ``create_stream()`` returns a fresh ``Stream`` attached to the same
    underlying model handle.
    """

    def __init__(self) -> None:
        self._transcriber = None
        self._loaded = False
        self._model_path: str = ""
        self._model_arch: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Download (if missing) and load the Moonshine model.

        Raises ``RuntimeError`` when loading fails.
        """
        if self._loaded:
            return

        settings = get_settings()
        language = settings.stt_language
        model_arch = settings.stt_model_arch
        requested_arch = ModelArch(model_arch) if model_arch is not None else ModelArch.MEDIUM_STREAMING


        try:
            STT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model_path, model_arch_val = self._resolve_model_path(
                language, requested_arch
            )
            
            # Try to load the model. If it's corrupted, Transcriber initialization will fail.
            try:
                self._transcriber = Transcriber(
                    model_path=model_path,
                    model_arch=model_arch_val,
                )
            except Exception as load_exc:
                logger.warning(
                    "Failed to load Moonshine model from %s, attempting to re-download. Error: %s",
                    model_path,
                    load_exc
                )
                # Delete corrupted folder and try downloading again
                import shutil
                try:
                    shutil.rmtree(model_path, ignore_errors=True)
                except Exception:
                    pass
                
                # Re-resolve (this will trigger get_model_for_language download since the files are gone)
                model_path, model_arch_val = self._resolve_model_path_force_download(
                    language, model_arch_val
                )
                self._transcriber = Transcriber(
                    model_path=model_path,
                    model_arch=model_arch_val,
                )
                
            self._model_path = str(model_path)
            self._model_arch = int(model_arch_val)
            self._loaded = True
            logger.info("Model loaded: %s (arch=%s)", self._model_path, self._model_arch)
        except Exception as exc:
            logger.exception("Failed to load Moonshine model")
            raise RuntimeError(
                f"Moonshine STT model could not be loaded: {exc}"
            )

    def _resolve_model_path(
        self,
        language: str,
        requested_arch: ModelArch,
    ) -> tuple[str, ModelArch]:
        """Try the requested model first, download if not cached, fallback to tiny-en."""
        # Check if requested arch is already cached and valid
        if self._model_cached(requested_arch):
            model_dir = self._model_dir(requested_arch)
            logger.info("Using cached Moonshine model: %s (arch=%s)", model_dir, requested_arch)
            return str(model_dir), requested_arch

        # If not cached, download it automatically
        return self._resolve_model_path_force_download(language, requested_arch)

    def _resolve_model_path_force_download(
        self,
        language: str,
        target_arch: ModelArch,
    ) -> tuple[str, ModelArch]:
        """Download the model using get_model_for_language API."""
        logger.info("Downloading and caching Moonshine model: arch=%s", target_arch)
        try:
            return get_model_for_language(
                wanted_language=language,
                wanted_model_arch=target_arch,
                cache_root=STT_MODEL_DIR,
            )
        except Exception as exc:
            logger.exception("Failed to download target arch %s, trying TINY fallback", target_arch)
            if target_arch != ModelArch.TINY:
                try:
                    return get_model_for_language(
                        wanted_language=language,
                        wanted_model_arch=ModelArch.TINY,
                        cache_root=STT_MODEL_DIR,
                    )
                except Exception as inner_exc:
                    raise RuntimeError(f"Failed to download fallback TINY model: {inner_exc}") from inner_exc
            raise RuntimeError(f"Failed to download Moonshine model: {exc}") from exc


    @staticmethod
    def _model_name(arch: ModelArch) -> str:
        """Return the model folder name for a given architecture."""
        mapping = {
            ModelArch.TINY: "tiny-en",
            ModelArch.BASE: "base-en",
            ModelArch.TINY_STREAMING: "tiny-streaming-en",
            ModelArch.BASE_STREAMING: "base-streaming-en",
            ModelArch.SMALL_STREAMING: "small-streaming-en",
            ModelArch.MEDIUM_STREAMING: "medium-streaming-en",
        }
        return mapping.get(arch, "tiny-en")

    def _model_dir(self, arch: ModelArch) -> Path:
        """Return the on-disk model directory for *arch*."""
        name = self._model_name(arch)
        return STT_MODEL_DIR / "download.moonshine.ai" / "model" / name / "quantized" / name

    def _model_components(self, arch: ModelArch) -> list[str]:
        """Return the required component filenames for *arch*.

        Matches ``get_components_for_model_info`` in the Moonshine package
        so the cache check is authoritative and the Transcriber always
        has every file it needs.
        """
        if arch in (
            ModelArch.TINY_STREAMING,
            ModelArch.BASE_STREAMING,
            ModelArch.SMALL_STREAMING,
            ModelArch.MEDIUM_STREAMING,
        ):
            return [
                "adapter.ort", "cross_kv.ort", "decoder_kv.ort",
                "encoder.ort", "frontend.ort", "streaming_config.json",
                "tokenizer.bin", "decoder_kv_with_attention.ort",
            ]
        return [
            "encoder_model.ort", "decoder_model_merged.ort",
            "tokenizer.bin", "decoder_with_attention.ort",
        ]

    def _model_cached(self, arch: ModelArch) -> bool:
        """Return True when model files for *arch* exist on disk."""
        model_dir = self._model_dir(arch)
        if not model_dir.is_dir():
            return False
        return all((model_dir / c).is_file() for c in self._model_components(arch))

    def is_loaded(self) -> bool:
        return self._loaded

    def create_stream(self, callback: Callable[[str, str], None]) -> object:
        """Create a new streaming session.

        ``callback`` is called with ``(event_type, text)`` for every
        Moonshine transcript event:

        * ``"partial"`` – interim text for an active line
        * ``"final"``   – completed line (phrase boundary)

        Returns the opaque ``Stream`` handle. Caller must invoke
        ``stream.start()`` before feeding audio and ``stream.stop()`` /
        ``stream.close()`` when done.
        """
        if not self._transcriber:
            raise RuntimeError("Moonshine model not loaded")

        listener = _StreamListener(callback)
        stream = self._transcriber.create_stream()
        stream.add_listener(listener)
        return stream

    def transcribe(self, audio_data: list[float], sample_rate: int = 16000) -> str:
        """One-shot non-streaming transcription.

        Accepts PCM float32 audio and returns the full transcript text.
        Not used in the real-time STT flow; available for convenience.
        """
        if not self._transcriber:
            raise RuntimeError("Moonshine model not loaded")

        transcript = self._transcriber.transcribe_without_streaming(
            audio_data=audio_data,
            sample_rate=sample_rate,
        )
        if transcript and transcript.lines:
            parts = [line.text for line in transcript.lines if line.text]
            return " ".join(parts)
        return ""


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


class _StreamListener(TranscriptEventListener):
    """Bridges Moonshine transcript events to a simple (type, text) callback."""

    def __init__(self, callback: Callable[[str, str], None]) -> None:
        self.callback = callback

    def on_line_text_changed(self, event) -> None:
        text = (event.line.text or "").strip()
        if text:
            self.callback("partial", text)

    def on_line_completed(self, event) -> None:
        text = (event.line.text or "").strip()
        if text:
            self.callback("final", text)
