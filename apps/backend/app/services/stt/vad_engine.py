import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

FRAME_MS = 30
FRAME_SIZE = int(16000 * FRAME_MS / 1000)


class VADEngine:
    """Voice Activity Detection engine with hysteresis and smoothing.

    Processes 30 ms PCM float32 frames and returns state transitions:
        ``"silence"``     – no speech
        ``"speech_start"``– speech just began (after debounce)
        ``"speech_active"``– speech ongoing
        ``"speech_end"``  – speech just ended (after trailing silence)
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = config or {}
        self.start_threshold: float = cfg.get("start_threshold", 0.6)
        self.end_threshold: float = cfg.get("end_threshold", 0.4)
        self.min_speech_frames: int = max(
            1, int(cfg.get("min_speech_duration_ms", 400) / FRAME_MS)
        )
        self.min_silence_frames: int = max(
            1, int(cfg.get("min_silence_duration_ms", 1000) / FRAME_MS)
        )
        self.smoothing_window: int = cfg.get("smoothing_window", 15)

        self._state: str = "silence"
        self._speech_count: int = 0
        self._silence_count: int = 0
        self._prob_buffer: list[float] = []
        self._noise_floor: float = 1e-6
        self._frame_buffer: np.ndarray = np.array([], dtype=np.float32)
        self._vad = None
        self._try_init_webrtc()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._state = "silence"
        self._speech_count = 0
        self._silence_count = 0
        self._prob_buffer.clear()
        self._frame_buffer = np.array([], dtype=np.float32)
        self._noise_floor = 1e-6

    def process(self, audio: np.ndarray) -> list[str]:
        """Feed raw float32 audio (any length).  Returns list of state
        transitions that occurred while consuming internal frames."""
        self._frame_buffer = np.concatenate([self._frame_buffer, audio])
        transitions: list[str] = []

        while len(self._frame_buffer) >= FRAME_SIZE:
            frame = self._frame_buffer[:FRAME_SIZE]
            self._frame_buffer = self._frame_buffer[FRAME_SIZE:]
            new_state = self._process_frame(frame)
            if new_state != self._state:
                self._state = new_state
                transitions.append(new_state)

        return transitions

    @property
    def state(self) -> str:
        return self._state

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _try_init_webrtc(self) -> None:
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad(2)
            logger.info("VAD: using webrtcvad")
        except ImportError:
            logger.info("VAD: webrtcvad not available, using energy-based fallback")

    def _get_probability(self, frame: np.ndarray) -> float:
        if self._vad is not None:
            return self._webrtc_prob(frame)
        return self._energy_prob(frame)

    def _webrtc_prob(self, frame: np.ndarray) -> float:
        int16 = (frame * 32767).astype(np.int16)
        try:
            return 1.0 if self._vad.is_speech(int16.tobytes(), 16000) else 0.0
        except Exception:
            return 0.0

    def _energy_prob(self, frame: np.ndarray) -> float:
        energy = float(np.mean(frame ** 2))
        if energy < self._noise_floor * 2:
            self._noise_floor = self._noise_floor * 0.9 + energy * 0.1
        else:
            self._noise_floor = self._noise_floor * 0.999 + energy * 0.001

        if energy <= self._noise_floor * 1.5:
            return 0.0
        ratio = energy / (self._noise_floor + 1e-10)
        prob = min(1.0, (ratio - 1.5) / 4.0)
        return max(0.0, prob)

    def _smoothed_prob(self, frame: np.ndarray) -> float:
        raw = self._get_probability(frame)
        self._prob_buffer.append(raw)
        if len(self._prob_buffer) > self.smoothing_window:
            self._prob_buffer.pop(0)
        return sum(self._prob_buffer) / len(self._prob_buffer)

    def _process_frame(self, frame: np.ndarray) -> str:
        prob = self._smoothed_prob(frame)

        if self._state in ("silence", "speech_end"):
            if prob >= self.start_threshold:
                self._speech_count += 1
                if self._speech_count >= self.min_speech_frames:
                    self._speech_count = 0
                    self._silence_count = 0
                    return "speech_start"
            else:
                self._speech_count = 0
            return self._state

        if prob >= self.end_threshold:
            self._silence_count = 0
            return "speech_active"

        self._silence_count += 1
        if self._silence_count >= self.min_silence_frames:
            self._speech_count = 0
            self._silence_count = 0
            return "speech_end"

        return "speech_active"
