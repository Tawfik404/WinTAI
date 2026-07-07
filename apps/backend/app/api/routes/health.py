from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    startup = getattr(request.app.state, "startup", None)
    if startup:
        return {
            "status": startup.get("status", "starting"),
            "progress": startup.get("progress", 0.0),
            "message": startup.get("message", ""),
            "backgroundInitialization": startup.get("backgroundInitialization", False),
            "embeddingModelLoaded": startup.get("embeddingModelLoaded", False),
            "toolIndexLoaded": startup.get("toolIndexLoaded", False),
            "appIndexLoaded": startup.get("appIndexLoaded", False),
            "appScanCacheLoaded": startup.get("appScanCacheLoaded", False),
            "moonshineLoaded": startup.get("moonshineLoaded", False),
            "piperReady": startup.get("piperReady", False),
            "errors": startup.get("errors", []),
        }
    return {
        "status": "ready",
        "progress": 1.0,
        "message": "ready",
        "backgroundInitialization": False,
        "embeddingModelLoaded": False,
        "toolIndexLoaded": False,
        "appIndexLoaded": False,
    }
