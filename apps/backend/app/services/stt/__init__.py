from app.services.stt.models import STTStatus, STTError, PartialTranscript, FinalTranscript

__all__ = [
    "MoonshineSTT",
    "STTManager",
    "STTStatus",
    "STTError",
    "PartialTranscript",
    "FinalTranscript",
    "VADEngine",
    "AudioBuffer",
]


def __getattr__(name: str):
    if name == "MoonshineSTT":
        from app.services.stt.moonshine_service import MoonshineSTT

        return MoonshineSTT
    if name == "STTManager":
        from app.services.stt.stt_manager import STTManager

        return STTManager
    if name == "VADEngine":
        from app.services.stt.vad_engine import VADEngine

        return VADEngine
    if name == "AudioBuffer":
        from app.services.stt.audio_buffer import AudioBuffer

        return AudioBuffer
    raise AttributeError(name)
