import io
import wave
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR = _REPO_ROOT / "models" / "tts"


def _find_default_model() -> str:
    if _MODELS_DIR.is_dir():
        onnx_files = sorted(_MODELS_DIR.glob("*.onnx"))
        if onnx_files:
            return str(onnx_files[0])
    return ""


class PiperTTS:
    def __init__(
        self,
        model_path: str | None = None,
    ):
        resolved = model_path or os.environ.get("PIPER_MODEL", "") or _find_default_model()
        self.model_path = resolved
        self._voice: object | None = None
        self._load_error: str | None = None

    @property
    def available(self) -> bool:
        if self._voice is not None:
            return True
        if self._load_error:
            return False
        if not self.model_path or not Path(self.model_path).is_file():
            self._load_error = f"Model not found: {self.model_path}"
            logger.warning(
                "Piper model not found. Place .onnx files in %s or set PIPER_MODEL env var.",
                _MODELS_DIR,
            )
            return False
        try:
            from piper import PiperVoice
            self._voice = PiperVoice.load(self.model_path)
            logger.info("Piper model loaded: %s", self.model_path)
            return True
        except Exception as e:
            self._load_error = str(e)
            logger.error("Failed to load Piper model: %s", e)
            return False

    def speak(self, text: str) -> bytes | None:
        if not self.available:
            return None
        try:
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav:
                self._voice.synthesize_wav(text, wav)
            wav_data = buf.getvalue()
            logger.info(
                "Piper synthesized %d bytes for: %s",
                len(wav_data),
                text[:50],
            )
            return wav_data
        except Exception as e:
            logger.error("Piper synthesis error: %s", e)
            return None

    def speak_to_file(self, text: str, output_path: str) -> str | None:
        if not self.available:
            return None
        try:
            with wave.open(output_path, "wb") as wav:
                self._voice.synthesize_wav(text, wav)
            logger.info("Piper wrote %s", output_path)
            return output_path
        except Exception as e:
            logger.error("Piper file synthesis error: %s", e)
            return None
