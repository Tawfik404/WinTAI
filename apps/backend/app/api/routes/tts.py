import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class TtsRequest(BaseModel):
    text: str


@router.post("/api/tts")
async def synthesize(body: TtsRequest, request: Request) -> Response:
    piper = getattr(request.app.state, "piper", None)
    if not piper or not piper.available:
        logger.warning("TTS unavailable, falling back")
        return Response(
            content=b"",
            media_type="audio/wav",
            headers={"X-TTS-Unavailable": "1"},
        )

    wav_data = piper.speak(body.text)
    if wav_data is None:
        return Response(
            content=b"",
            media_type="audio/wav",
            headers={"X-TTS-Unavailable": "1"},
        )

    return Response(content=wav_data, media_type="audio/wav")
