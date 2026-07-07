import numpy as np
from typing import Optional


class AudioBuffer:
    """Accumulates audio frames during a speech segment.

    Maintains a rolling pre-buffer so that when speech onset is
    detected the very beginning of the utterance is not lost.
    """

    def __init__(self, pre_buffer_ms: int = 400, sample_rate: int = 16000) -> None:
        self._sample_rate = sample_rate
        self._pre_buffer_size = int(sample_rate * pre_buffer_ms / 1000)
        self._pre_buffer: np.ndarray = np.array([], dtype=np.float32)
        self._speech_buffer: np.ndarray = np.array([], dtype=np.float32)
        self._in_speech = False

    @property
    def duration_ms(self) -> float:
        return len(self._speech_buffer) / self._sample_rate * 1000

    def add(self, audio: np.ndarray) -> None:
        if not self._in_speech:
            self._pre_buffer = np.concatenate([self._pre_buffer, audio])
            if len(self._pre_buffer) > self._pre_buffer_size:
                self._pre_buffer = self._pre_buffer[-self._pre_buffer_size:]
        else:
            self._speech_buffer = np.concatenate([self._speech_buffer, audio])

    def start_speech(self) -> None:
        self._in_speech = True
        self._speech_buffer = self._pre_buffer.copy()

    def end_speech(self) -> Optional[np.ndarray]:
        if not self._in_speech:
            return None
        self._in_speech = False
        result = self._speech_buffer.copy()
        self._speech_buffer = np.array([], dtype=np.float32)
        self._pre_buffer = np.array([], dtype=np.float32)
        return result

    def cancel(self) -> None:
        self._in_speech = False
        self._speech_buffer = np.array([], dtype=np.float32)
        self._pre_buffer = np.array([], dtype=np.float32)
