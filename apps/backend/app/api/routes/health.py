from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    startup = getattr(request.app.state, "startup", None)
    if startup:
        return {
            "status": startup["status"],
            "progress": startup["progress"],
            "message": startup["message"],
        }
    return {"status": "ok", "progress": 1.0, "message": "ready"}
