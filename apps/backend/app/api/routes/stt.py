import json
import logging
import struct
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse

from app.services.stt import STTManager, STTStatus, MoonshineSTT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stt")


def _get_manager(request: Request) -> STTManager:
    return request.app.state.stt_manager


def _get_moonshine(request: Request) -> MoonshineSTT:
    return request.app.state.moonshine_stt


# ------------------------------------------------------------------
# HTTP endpoints
# ------------------------------------------------------------------


@router.post("/start")
async def start_session(request: Request) -> JSONResponse:
    """Start a new STT recording session.

    Returns ``{"session_id": "..."}`` on success or an error response
    when the Moonshine model is not loaded.
    """
    moonshine = _get_moonshine(request)
    if not moonshine.is_loaded():
        return JSONResponse(
            status_code=503,
            content={"error": "Moonshine model not loaded"},
        )

    manager = _get_manager(request)

    # Dummy callback — HTTP clients don't receive streaming events.
    def _noop(event_type: str, text: str) -> None:
        pass

    session = manager.start_session(on_event=_noop)
    session.start()
    return JSONResponse(content={"session_id": session.session_id})


@router.post("/stop")
async def stop_session(request: Request) -> JSONResponse:
    """Stop the active STT session and return the final transcript."""
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
# WebSocket endpoint
# ------------------------------------------------------------------


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time STT via WebSocket.

    **Protocol:**

    *Client → Server:*
    - Binary frame: raw PCM float32 mono audio (any sample rate;
      resampled to 16000 Hz by Moonshine internally)
    - Text (JSON) ``{"type": "start"}``: begin the session
    - Text (JSON) ``{"type": "stop"}``: finalize the current session

    *Server → Client:*
    - Text (JSON) ``{"type": "partial", "text": "...", "session_id": "..."}``
    - Text (JSON) ``{"type": "final",   "text": "...", "session_id": "..."}``
    - Text (JSON) ``{"type": "done",    "text": "...", "session_id": "..."}``
    - Text (JSON) ``{"type": "error",   "error": "..."}``
    """
    await websocket.accept()

    moonshine: MoonshineSTT = websocket.app.state.moonshine_stt
    manager: STTManager = websocket.app.state.stt_manager

    if not moonshine.is_loaded():
        await websocket.send_json({"type": "error", "error": "Moonshine model not loaded"})
        await websocket.close(code=1011)
        return

    session = None

    async def _send_event(event_type: str, text: str) -> None:
        try:
            msg = {
                "type": event_type,
                "text": text,
                "session_id": session.session_id if session else "",
            }
            await websocket.send_json(msg)
        except Exception:
            pass

    try:
        while True:
            message = await websocket.receive()

            # --- Binary: raw audio ---
            if message.get("type") == "websocket.receive" and "bytes" in message:
                raw = message["bytes"]
                if session and session.is_listening:
                    try:
                        audio = _bytes_to_float32(raw)
                        session.add_audio(audio)
                    except Exception:
                        logger.warning(
                            "Failed to process audio frame (len=%d)", len(raw),
                        )

            # --- Text: control commands ---
            elif message.get("type") == "websocket.receive" and "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "error": "Invalid JSON"})
                    continue

                cmd = data.get("type", "")

                if cmd == "start":
                    try:
                        if session:
                            manager.stop_session()
                        session = manager.start_session(on_event=_send_event)
                        session.start()
                        await websocket.send_json({
                            "type": "status",
                            "status": "listening",
                            "session_id": session.session_id,
                        })
                        logger.info("Recording started [ws]")
                    except Exception as exc:
                        logger.error("Failed to start STT session: %s", exc)
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Failed to start: {exc}",
                        })
                        if session:
                            try:
                                manager.stop_session()
                            except Exception:
                                pass
                            session = None

                elif cmd == "stop":
                    if session:
                        transcript = manager.stop_session()
                        await websocket.send_json({
                            "type": "done",
                            "text": transcript or "",
                            "session_id": session.session_id,
                        })
                        logger.info("Recording stopped [ws]")
                        session = None

                elif cmd == "status":
                    await websocket.send_json({
                        "type": "status",
                        "status": "listening" if (session and session.is_listening) else "idle",
                        "session_id": session.session_id if session else "",
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        if session:
            manager.stop_session()
        session = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _bytes_to_float32(data: bytes) -> list[float]:
    """Convert raw bytes (little-endian float32) to a Python float list.

    Accepts both 32-bit float and 16-bit int PCM and normalises to
    float32 [-1.0, 1.0].  NaN / Inf values are clamped to 0.0 so that
    the Moonshine native library never receives invalid floats.
    """
    if not data:
        return []

    # Detect format: if length is divisible by 2 but not by 4, assume int16
    if len(data) % 4 != 0 and len(data) % 2 == 0:
        count = len(data) // 2
        fmt = "<h"
        divisor = 32768.0
    else:
        count = len(data) // 4
        fmt = "<f"
        divisor = 1.0

    samples = struct.unpack(f"{fmt * count}", data)
    if divisor != 1.0:
        samples = [max(-1.0, min(1.0, s / divisor)) for s in samples]
    else:
        samples = list(samples)

    # Guard against NaN / Inf (e.g. from garbage bytes in oversized buffers)
    for i in range(len(samples)):
        s = samples[i]
        if s != s or s > 1e18 or s < -1e18:  # NaN check via self-inequality
            samples[i] = 0.0
    return samples
