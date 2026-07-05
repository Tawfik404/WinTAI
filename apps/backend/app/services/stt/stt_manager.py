import logging
import uuid
from typing import Callable, Optional

from app.services.stt.moonshine_service import MoonshineSTT

logger = logging.getLogger(__name__)


class STTSession:
    """Holds the state for one STT recording session."""

    def __init__(self, session_id: str, stream: object) -> None:
        self.session_id = session_id
        self.stream = stream
        self.is_listening = False
        self.final_texts: list[str] = []
        self.partial_text: str = ""

    def start(self) -> None:
        self.stream.start()
        self.is_listening = True
        logger.info("Recording started [session=%s]", self.session_id)

    def stop(self) -> Optional[str]:
        if not self.is_listening:
            return None
        self.is_listening = False
        transcript = self.stream.stop()
        self.stream.close()
        if transcript and transcript.lines:
            for line in transcript.lines:
                text = (line.text or "").strip()
                if text:
                    self.final_texts.append(text)
        full = " ".join(self.final_texts) if self.final_texts else None
        logger.info("Recording stopped [session=%s]", self.session_id)
        return full

    def add_audio(self, audio_data: list[float], sample_rate: int = 16000) -> None:
        self.stream.add_audio(audio_data, sample_rate)


class STTManager:
    """Manages the lifecycle of a single active STT recording session.

    Only one session may exist at any time.  Creating a new session
    while one is active implicitly replaces it.
    """

    def __init__(self, moonshine: MoonshineSTT) -> None:
        self._moonshine = moonshine
        self._session: Optional[STTSession] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
            "partial": self._session.partial_text if self._session else "",
            "final": " ".join(self._session.final_texts) if self._session else "",
        }

    def start_session(
        self,
        on_event: Callable[[str, str], None],
    ) -> STTSession:
        """Create a new recording session.

        If a session is already active it is cancelled first.
        ``on_event`` receives ``(event_type, text)`` from Moonshine.

        Returns the ``STTSession`` (caller should invoke ``start()``).
        """
        self._cancel_session()

        stream = self._moonshine.create_stream(on_event)
        session_id = uuid.uuid4().hex[:12]
        self._session = STTSession(session_id=session_id, stream=stream)
        logger.info("Session created [session=%s]", session_id)
        return self._session

    def stop_session(self) -> Optional[str]:
        """Stop the active session and return the full transcript."""
        if not self._session:
            return None
        transcript = self._session.stop()
        self._session = None
        return transcript

    def add_audio(self, audio_data: list[float], sample_rate: int = 16000) -> None:
        if self._session and self._session.is_listening:
            self._session.add_audio(audio_data, sample_rate)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cancel_session(self) -> None:
        if self._session:
            try:
                if self._session.is_listening:
                    self._session.stream.stop()
                self._session.stream.close()
            except Exception:
                logger.exception("Error cancelling session [session=%s]", self._session.session_id)
            self._session = None
