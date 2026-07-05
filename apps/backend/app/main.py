import asyncio
import sys
import logging
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.core.config import get_settings
from app.core.cors import configure_cors
from app.api.router import api_router

from services.registry.service import RegistryService
from services.embeddings.service import EmbeddingService
from services.app_scanner import AppScanner
from services.app_embeddings import AppEmbeddingService
from services.executor import ToolExecutor
from services.tts.piper_service import PiperTTS
from app.services.stt.moonshine_service import MoonshineSTT
from app.services.stt.stt_manager import STTManager

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# ---------------------------------------------------------------------------
# Startup state – allows the health endpoint to report real progress while
# services initialise in the background.
# ---------------------------------------------------------------------------
def _write_progress(progress: float, service: str, message: str) -> None:
    """Write a machine-parseable progress line to stdout that the Electron
    main process can capture for real-time status display."""
    print(f"[PROGRESS] {progress:.2f}|{service}|{message}", flush=True)


# ---------------------------------------------------------------------------
# Background initialisation – runs concurrently so the health endpoint
# becomes available immediately.
# ---------------------------------------------------------------------------
def _set_progress(app: FastAPI, status: str, progress: float, message: str, service: str = "") -> None:
    app.state.startup["status"] = status
    app.state.startup["progress"] = progress
    app.state.startup["message"] = message
    if service:
        _write_progress(progress, service, message)


async def _init_backend(app: FastAPI) -> None:
    logger = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()

    _set_progress(app, "loading", 0.05, "Loading registry...", "registry")
    registry = await loop.run_in_executor(None, _load_registry)
    app.state.registry = registry

    _set_progress(app, "loading", 0.10, "Loading AI model, scanning apps, loading voice...", "parallel")
    reg_descs = registry.get_descriptions()
    n_tools = len(reg_descs)

    results = await asyncio.gather(
        loop.run_in_executor(None, _load_embedder, reg_descs),
        loop.run_in_executor(None, _scan_apps),
        loop.run_in_executor(None, _load_moonshine),
        loop.run_in_executor(None, _load_piper),
    )

    embedder, apps, (moonshine, moonshine_err), piper = results

    app.state.embedder = embedder
    logger.info(
        "Embedding service initialized with %d tools (dimension=%d).",
        n_tools,
        embedder.get_dimension(),
    )
    _set_progress(app, "loading", 0.45, f"AI model ready ({n_tools} tools)")

    if moonshine_err:
        logger.warning("Moonshine STT model failed to load. Voice input disabled.")
        _set_progress(app, "loading", 0.50, "Voice model unavailable")
    else:
        logger.info("Moonshine STT model loaded.")
        _set_progress(app, "loading", 0.50, "Voice model loaded")
    app.state.moonshine_stt = moonshine

    if piper.available:
        logger.info("Piper TTS available.")
    else:
        logger.warning("Piper TTS not available. Set PIPER_MODEL env var to enable voice.")

    app.state.piper = piper

    n_apps = len(apps)
    _set_progress(app, "loading", 0.55, f"Scanned {n_apps} applications, indexing...", "apps")

    app_dicts = [{"name": a.name, "path": a.path, "source": a.source} for a in apps]

    app_embedder = await loop.run_in_executor(None, _load_app_embedder, app_dicts)
    app.state.app_embedder = app_embedder
    _set_progress(app, "loading", 0.75, f"Indexed {app_embedder.get_index_size()} applications")

    executor = ToolExecutor()
    app.state.executor = executor
    _set_progress(app, "loading", 0.80, "Tool executor ready")

    stt_manager = STTManager(moonshine)
    app.state.stt_manager = stt_manager
    _set_progress(app, "loading", 0.90, "Speech recognition ready")

    app.state.startup_complete = True

    _set_progress(app, "ready", 1.0, "All services ready")
    logger.info(
        "App scanner + embedder + executor + TTS + STT ready (%d apps indexed).",
        app_embedder.get_index_size(),
    )


def _load_registry() -> RegistryService:
    registry = RegistryService()
    registry.load()
    return registry


def _load_embedder(descriptions: list) -> EmbeddingService:
    embedder = EmbeddingService()
    embedder.initialize()
    embedder.build_index(descriptions)
    return embedder


def _scan_apps() -> list:
    scanner = AppScanner(max_workers=4)
    return scanner.scan_all()


def _load_moonshine() -> tuple[MoonshineSTT, str | None]:
    moonshine = MoonshineSTT()
    try:
        moonshine.initialize()
        return moonshine, None
    except Exception as exc:
        return moonshine, str(exc)


def _load_piper() -> PiperTTS:
    return PiperTTS()


def _load_app_embedder(app_dicts: list) -> AppEmbeddingService:
    ae = AppEmbeddingService()
    ae.initialize(app_dicts)
    return ae


# ---------------------------------------------------------------------------
# App construction
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
)

configure_cors(app)
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Startup – runs init in background so the health endpoint responds
# immediately (even while other services are still loading).
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup() -> None:
    app.state.startup = {"status": "starting", "progress": 0.0, "message": ""}
    asyncio.create_task(_init_backend(app))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
