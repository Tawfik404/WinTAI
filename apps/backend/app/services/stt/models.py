from pydantic import BaseModel
from typing import Optional


class STTStatus(BaseModel):
    status: str
    is_loaded: bool = False
    model_name: str = ""
    sample_rate: int = 16000
    session_active: bool = False


class STTError(BaseModel):
    type: str = "error"
    error: str


class PartialTranscript(BaseModel):
    type: str = "partial"
    text: str
    session_id: str = ""


class FinalTranscript(BaseModel):
    type: str = "final"
    text: str
    session_id: str = ""


class STTDone(BaseModel):
    type: str = "done"
    text: str
    session_id: str = ""
