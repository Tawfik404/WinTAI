import logging
import uuid
from typing import Callable, Optional

import numpy as np

from app.services.stt.moonshine_service import MoonshineSTT
from app.services.stt.vad_engine import VADEngine, FRAME_SIZE
from app.services.stt.audio_buffer import AudioBuffer

logger = logging.getLogger(__name__)

_VAD_CONFIG: dict = {
    "start_threshold": 0.65,
    "end_threshold": 0.45,
    "min_speech_duration_ms": 350,
    "min_silence_duration_ms": 900,
    "smoothing_window": 15,
}


class STTSession:
    """Holds state for one STT session with VAD-based auto-segmentation.

    Audio flows through:
        incoming frames
            → VAD engine (per-frame probability + hysteresis)
            → audio buffer (accumulates during speech)
            → on speech_end → flush to Moonshine for transcription
    """

    def __init__(
        self,
        session_id: str,
        moonshine: MoonshineSTT,
        on_event: Callable[[str, str], None],
    ) -> None:
        self.session_id = session_id
        self._moonshine = moonshine
        self._on_event = on_event
        self.vad = VADEngine(_VAD_CONFIG)
        self.buffer = AudioBuffer()
        self.is_listening = False
        self.is_speech = False
        self._current_stream = None
        self._transcripts: list[str] = []

    def start(self) -> None:
        self.is_listening = True
        logger.info("VAD session started [session=%s]", self.session_id)

    def add_audio(self, audio_data: list[float], sample_rate: int = 16000) -> None:
        if not self.is_listening:
            return

        audio = np.array(audio_data, dtype=np.float32)
        states = self.vad.process(audio)
        self.buffer.add(audio)

        for state in states:
            if state == "speech_start":
                self.is_speech = True
                self.buffer.start_speech()
                self._ensure_stream()
                self._emit("speech_started", "")

            elif state == "speech_end":
                self._finalize_segment()
                self.is_speech = False
                self._emit("speech_ended", "")

    def stop(self) -> Optional[str]:
        """Manually stop the session and return accumulated transcripts."""
        if not self.is_listening:
            return None

        self.is_listening = False

        if self.is_speech:
            self._finalize_segment()
            self.is_speech = False

        self._close_stream()
        full = " ".join(self._transcripts) if self._transcripts else None
        logger.info(
            "VAD session stopped [session=%s] transcripts=%d",
            self.session_id,
            len(self._transcripts),
        )
        return full

    def get_final_texts(self) -> list[str]:
        return list(self._transcripts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_stream(self) -> None:
        if self._current_stream is not None:
            return
        self._current_stream = self._moonshine.create_stream(self._on_event)
        self._current_stream.start()

    def _finalize_segment(self) -> None:
        audio = self.buffer.end_speech()
        if audio is None or len(audio) == 0:
            return

        duration = len(audio) / 16000
        if duration < 0.3:
            logger.debug("Segment too short (%.2fs), discarding", duration)
            return

        if self._current_stream is None:
            logger.warning("No active stream for segment — creating one-shot")
            text = self._moonshine.transcribe(audio.tolist())
            if text:
                self._transcripts.append(text)
                self._emit("transcript", text)
            return

        stream = self._current_stream
        self._current_stream = None

        stream.add_audio(audio.tolist(), 16000)
        transcript = stream.stop()
        stream.close()

        if transcript and transcript.lines:
            parts = [line.text.strip() for line in transcript.lines if line.text]
            text = " ".join(parts)
            if text:
                self._transcripts.append(text)
                self._emit("transcript", text)

    def _close_stream(self) -> None:
        if self._current_stream is not None:
            try:
                self._current_stream.stop()
                self._current_stream.close()
            except Exception:
                logger.exception("Error closing stream")
            self._current_stream = None

    def _emit(self, event_type: str, text: str) -> None:
        try:
            self._on_event(event_type, text)
        except Exception:
            logger.exception("Error emitting event %s", event_type)


class STTManager:
    """Manages the lifecycle of a single active STT session.

    Only one session may exist at any time.  Creating a new session
    while one is active implicitly replaces it.
    """

    def __init__(self, moonshine: MoonshineSTT) -> None:
        self._moonshine = moonshine
        self._session: Optional[STTSession] = None

    @property
    def active(self) -> bool:
        return self._session is not None

    @property
    def is_listening(self) -> bool:
        return self._session is not None and self._session.is_listening

    def get_status(self) -> dict:
        return {
            "model_loaded": self._moonshine.is_loaded(),
            "session_active": self.active,
            "is_listening": self.is_listening,
            "is_speech": self._session.is_speech if self._session else False,
            "transcripts": self._session.get_final_texts() if self._session else [],
        }

    def start_session(
        self,
        on_event: Callable[[str, str], None],
    ) -> STTSession:
        self._cancel_session()
        session_id = uuid.uuid4().hex[:12]
        self._session = STTSession(
            session_id=session_id,
            moonshine=self._moonshine,
            on_event=on_event,
        )
        logger.info("VAD session created [session=%s]", session_id)
        return self._session

    def stop_session(self) -> Optional[str]:
        if not self._session:
            return None
        transcript = self._session.stop()
        self._session = None
        return transcript

    def add_audio(self, audio_data: list[float], sample_rate: int = 16000) -> None:
        if self._session and self._session.is_listening:
            self._session.add_audio(audio_data, sample_rate)

    def _cancel_session(self) -> None:
        if self._session:
            try:
                self._session.stop()
            except Exception:
                logger.exception("Error cancelling session")
            self._session = None
