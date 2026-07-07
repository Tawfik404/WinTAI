import asyncio
import json
import logging
import struct
from typing import Optional, TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse

from app.services.stt import STTStatus

if TYPE_CHECKING:
    from app.services.stt import MoonshineSTT, STTManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stt")


def _get_manager(request: Request) -> "STTManager":
    return request.app.state.stt_manager


def _get_moonshine(request: Request) -> "MoonshineSTT":
    return request.app.state.moonshine_stt


# ------------------------------------------------------------------
# HTTP endpoints
# ------------------------------------------------------------------


@router.post("/start")
async def start_session(request: Request) -> JSONResponse:
    """Start a new VAD-based STT recording session."""
    moonshine = _get_moonshine(request)
    if not moonshine.is_loaded():
        return JSONResponse(
            status_code=503,
            content={"error": "Moonshine model not loaded"},
        )

    manager = _get_manager(request)
    session = manager.start_session(on_event=lambda _t, _x: None)
    session.start()
    return JSONResponse(content={"session_id": session.session_id})


@router.post("/stop")
async def stop_session(request: Request) -> JSONResponse:
    """Stop the active STT session and return accumulated transcripts."""
    manager = _get_manager(request)
    transcript = manager.stop_session()
    return JSONResponse(content={"transcript": transcript or ""})


@router.get("/status")
async def get_status(request: Request) -> STTStatus:
    """Return current STT service status."""
    moonshine = _get_moonshine(request)
    manager = _get_manager(request)

    status = STTStatus(
        status="idle",
        is_loaded=moonshine.is_loaded(),
        model_name="medium-streaming-en",
        session_active=manager.active,
    )

    if manager.is_listening:
        status.status = "listening"
    elif manager.active:
        status.status = "processing"
    elif not moonshine.is_loaded():
        status.status = "error"

    return status


# ------------------------------------------------------------------
# WebSocket endpoint (VAD-powered)
# ------------------------------------------------------------------


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time STT via WebSocket with VAD auto-segmentation.

    **Protocol:**

    *Client → Server:*
    - Binary frame: raw PCM float32 mono audio (16 kHz)
    - Text (JSON) ``{"type": "start"}``: begin a VAD listening session
    - Text (JSON) ``{"type": "stop"}``: end the session

    *Server → Client (VAD events):*
    - ``{"type": "status",          "status": "listening",             "session_id": "..."}``
    - ``{"type": "speech_started",  "session_id": "..."}``
    - ``{"type": "speech_ended",    "session_id": "..."}``
    - ``{"type": "transcript",      "text": "...",                     "session_id": "..."}``
    - ``{"type": "done",            "text": "...",                     "session_id": "..."}``
    - ``{"type": "error",           "error": "..."}``
    """
    await websocket.accept()

    moonshine: MoonshineSTT = websocket.app.state.moonshine_stt
    manager: STTManager = websocket.app.state.stt_manager

    if not moonshine.is_loaded():
        await websocket.send_json(
            {"type": "error", "error": "Moonshine model not loaded"}
        )
        await websocket.close(code=1011)
        return

    session: Optional[STTManager] = None
    _ws_open = True

    async def _async_send(event_type: str, text: str) -> None:
        if not _ws_open:
            return
        try:
            await websocket.send_json(
                {
                    "type": event_type,
                    "text": text,
                    "session_id": session.session_id if session else "",
                }
            )
        except Exception:
            pass

    def _sync_send(event_type: str, text: str) -> None:
        try:
            asyncio.get_running_loop().create_task(
                _async_send(event_type, text)
            )
        except RuntimeError:
            pass

    try:
        while True:
            raw = await websocket.receive()

            if "bytes" in raw:
                if session and session.is_listening:
                    try:
                        audio = _bytes_to_float32(raw["bytes"])
                        session.add_audio(audio)
                    except Exception:
                        logger.warning("Failed to decode audio (len=%d)", len(raw["bytes"]))

            elif "text" in raw:
                try:
                    data = json.loads(raw["text"])
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"type": "error", "error": "Invalid JSON"}
                    )
                    continue

                cmd = data.get("type", "")

                if cmd == "start":
                    try:
                        if session:
                            manager.stop_session()
                        session = manager.start_session(on_event=_sync_send)
                        session.start()
                        await websocket.send_json(
                            {
                                "type": "status",
                                "status": "listening",
                                "session_id": session.session_id,
                            }
                        )
                        logger.info("VAD session started [ws]")
                    except Exception as exc:
                        logger.error("Failed to start STT session: %s", exc)
                        await websocket.send_json(
                            {"type": "error", "error": f"Failed to start: {exc}"}
                        )
                        if session:
                            manager.stop_session()
                            session = None

                elif cmd == "stop":
                    if session:
                        transcript = manager.stop_session()
                        await websocket.send_json(
                            {
                                "type": "done",
                                "text": transcript or "",
                                "session_id": session.session_id,
                            }
                        )
                        logger.info("VAD session stopped [ws]")
                        session = None

                elif cmd == "status":
                    await websocket.send_json(
                        {
                            "type": "status",
                            "status": "listening"
                            if (session and session.is_listening)
                            else "idle",
                            "session_id": session.session_id if session else "",
                        }
                    )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        _ws_open = False
        if session:
            manager.stop_session()
        session = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _bytes_to_float32(data: bytes) -> list[float]:
    """Convert raw bytes to float32 samples in [-1.0, 1.0].

    Supports both:
    - 32-bit float PCM (``len % 4 == 0``)
    - 16-bit int PCM  (``len % 2 == 0`` and ``len % 4 != 0``)

    When the length is divisible by both (e.g. 8 bytes),
    float32 is chosen because the browser always sends
    ``Float32Array`` buffers.
    """
    if not data:
        return []

    n = len(data)

    if n % 4 == 0:
        count = n // 4
        samples = list(struct.unpack(f"<{count}f", data))
    elif n % 2 == 0:
        count = n // 2
        samples = [max(-1.0, min(1.0, s / 32768.0)) for s in struct.unpack(f"<{count}h", data)]
    else:
        logger.warning("_bytes_to_float32: odd-length buffer (%d bytes)", n)
        return []

    for i in range(len(samples)):
        s = samples[i]
        if s != s or s > 1e18 or s < -1e18:
            samples[i] = 0.0
    return samples


