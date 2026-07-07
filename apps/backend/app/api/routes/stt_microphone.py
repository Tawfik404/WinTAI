import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.stt.microphone_manager import MicrophoneManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stt")


class SelectMicrophoneRequest(BaseModel):
    deviceId: str


def _get_manager(request: Request) -> MicrophoneManager:
    if not hasattr(request.app.state, "microphone_manager"):
        request.app.state.microphone_manager = MicrophoneManager()
    return request.app.state.microphone_manager


@router.get("/microphones")
async def list_microphones(request: Request):
    manager = _get_manager(request)
    devices = manager.enumerate()
    return JSONResponse(content=devices)


@router.get("/microphone")
async def get_microphone(request: Request):
    manager = _get_manager(request)
    device_id = manager.get_device_id()
    return JSONResponse(content={"id": device_id})


@router.put("/microphone")
async def set_microphone(body: SelectMicrophoneRequest, request: Request):
    manager = _get_manager(request)
    device_id = body.deviceId

    if device_id != "default":
        found = any(d["id"] == device_id for d in manager.enumerate())
        if not found:
            logger.warning("Invalid microphone detected: %s", device_id)

    manager.set_device_id(device_id)
    logger.info("Microphone changed: %s", device_id)
    return JSONResponse(content={"deviceId": device_id})
