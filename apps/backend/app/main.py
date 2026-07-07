import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
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

settings = get_settings()
logger = logging.getLogger(__name__)
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"
APP_SCAN_CACHE = CACHE_DIR / "apps.json"
TOOL_EMBEDDING_CACHE = CACHE_DIR / "tool_embeddings.json"
APP_EMBEDDING_CACHE = CACHE_DIR / "app_embeddings.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def _write_progress(progress: float, service: str, message: str) -> None:
    print(f"[PROGRESS] {progress:.2f}|{service}|{message}", flush=True)


def _set_progress(app: FastAPI, status: str, progress: float, message: str, service: str = "") -> None:
    startup = app.state.startup
    startup["status"] = status
    startup["progress"] = progress
    startup["message"] = message
    if service:
        _write_progress(progress, service, message)


def _set_flag(app: FastAPI, name: str, value: bool) -> None:
    app.state.startup[name] = value


def _init_state(app: FastAPI) -> None:
    app.state.startup = {
        "status": "starting",
        "progress": 0.0,
        "message": "Backend starting",
        "backgroundInitialization": False,
        "embeddingModelLoaded": False,
        "toolIndexLoaded": False,
        "appIndexLoaded": False,
        "appScanCacheLoaded": False,
        "moonshineLoaded": False,
        "piperReady": False,
        "errors": [],
    }
    app.state.startup_complete = False
    app.state.registry = None
    app.state.embedder = None
    app.state.app_embedder = None
    app.state.executor = None
    app.state.piper = None
    app.state.moonshine_stt = None
    app.state.stt_manager = None
    app.state.background_tasks = set()


def _track_task(app: FastAPI, task: asyncio.Task) -> None:
    app.state.background_tasks.add(task)
    task.add_done_callback(app.state.background_tasks.discard)


async def _background_initialization(app: FastAPI) -> None:
    logger.info("Background initialization started")
    _set_flag(app, "backgroundInitialization", True)
    _set_progress(app, "loading", 0.05, "Loading registry", "registry")

    try:
        registry = await asyncio.to_thread(_load_registry)
        app.state.registry = registry
        app.state.executor = await asyncio.to_thread(_load_executor)
        _set_progress(app, "loading", 0.15, "Core services ready", "core")

        tool_task = asyncio.create_task(_load_tool_embeddings(app, registry))
        apps_task = asyncio.create_task(_load_cached_apps_and_embeddings(app))
        piper_task = asyncio.create_task(_load_piper_background(app))
        moonshine_task = asyncio.create_task(_load_moonshine_background(app))

        await asyncio.gather(tool_task, apps_task, piper_task, moonshine_task)

        app.state.stt_manager = await asyncio.to_thread(_load_stt_manager, app.state.moonshine_stt)
        _set_progress(app, "ready", 1.0, "API ready")
        app.state.startup_complete = True
        logger.info("Background initialization completed")

        refresh_task = asyncio.create_task(_refresh_apps_if_changed(app))
        _track_task(app, refresh_task)
    except Exception as exc:
        logger.exception("Background initialization failed")
        app.state.startup["errors"].append(str(exc))
        _set_progress(app, "degraded", 1.0, "Backend running with initialization errors")


async def _load_tool_embeddings(app: FastAPI, registry: Any) -> None:
    descriptions = registry.get_descriptions()
    embedder, cache_hit = await asyncio.to_thread(_load_embedder, descriptions)
    app.state.embedder = embedder
    _set_flag(app, "embeddingModelLoaded", True)
    _set_flag(app, "toolIndexLoaded", True)
    label = "Tool index loaded from cache" if cache_hit else "Tool index built"
    _set_progress(app, "loading", 0.45, label, "embeddings")


async def _load_cached_apps_and_embeddings(app: FastAPI) -> None:
    try:
        apps = await asyncio.to_thread(_load_app_cache)
        if apps is not None:
            _set_flag(app, "appScanCacheLoaded", True)
            app_embedder, cache_hit = await asyncio.to_thread(_load_app_embedder, apps)
            app.state.app_embedder = app_embedder
            _set_flag(app, "appIndexLoaded", True)
            label = "App index loaded from cache" if cache_hit else "App index rebuilt from cached apps"
            _set_progress(app, "loading", 0.70, label, "apps")
            return

        _set_progress(app, "loading", 0.55, "No app cache; scanning applications", "apps")
        apps = await asyncio.to_thread(_scan_apps)
        await asyncio.to_thread(_save_app_cache, apps)
        app_embedder, _ = await asyncio.to_thread(_load_app_embedder, apps)
        app.state.app_embedder = app_embedder
        _set_flag(app, "appIndexLoaded", True)
        _set_progress(app, "loading", 0.70, "App index built", "apps")
    except Exception as exc:
        logger.exception("App index initialization failed")
        app.state.startup["errors"].append(f"App index unavailable: {exc}")
        _set_flag(app, "appIndexLoaded", False)


async def _load_piper_background(app: FastAPI) -> None:
    piper = await asyncio.to_thread(_load_piper)
    app.state.piper = piper
    _set_flag(app, "piperReady", bool(getattr(piper, "available", False)))


async def _load_moonshine_background(app: FastAPI) -> None:
    try:
        import sys
        import subprocess
        _set_progress(app, "loading", 0.72, "Checking Moonshine dependencies", "stt")
        try:
            import moonshine_voice
        except ImportError:
            _set_progress(app, "loading", 0.73, "Installing moonshine-voice", "stt")
            logger.info("Installing moonshine-voice...")
            subprocess.run([sys.executable, "-m", "pip", "install", "moonshine-voice>=0.0.65"], check=True)
            logger.info("moonshine-voice installed successfully.")
    except Exception as exc:
        logger.exception("Failed to verify/install moonshine-voice")
        app.state.startup["errors"].append(f"Moonshine STT install failed: {exc}")
        app.state.moonshine_stt = None
        _set_flag(app, "moonshineLoaded", False)
        return

    moonshine, err = await asyncio.to_thread(_load_moonshine)
    app.state.moonshine_stt = moonshine
    _set_flag(app, "moonshineLoaded", err is None)
    if err:
        app.state.startup["errors"].append(f"Moonshine STT unavailable: {err}")



async def _refresh_apps_if_changed(app: FastAPI) -> None:
    try:
        apps = await asyncio.to_thread(_scan_apps)
        old = _load_app_cache() or []
        if _app_fingerprint(apps) == _app_fingerprint(old):
            return
        await asyncio.to_thread(_save_app_cache, apps)
        app_embedder, _ = await asyncio.to_thread(_load_app_embedder, apps)
        app.state.app_embedder = app_embedder
        _set_flag(app, "appIndexLoaded", True)
    except Exception as exc:
        logger.exception("Background app refresh failed")
        app.state.startup["errors"].append(f"App refresh failed: {exc}")


def _load_registry() -> Any:
    from services.registry.service import RegistryService

    registry = RegistryService()
    registry.load()
    return registry


def _load_executor() -> Any:
    from services.executor import ToolExecutor

    return ToolExecutor()


def _load_embedder(descriptions: list[tuple[str, str]]) -> tuple[Any, bool]:
    from services.embeddings.service import EmbeddingService

    embedder = EmbeddingService()
    cache_hit = embedder.build_or_load_index(descriptions, TOOL_EMBEDDING_CACHE)
    return embedder, cache_hit


def _scan_apps() -> list[dict[str, Any]]:
    from services.app_scanner import AppScanner

    scanner = AppScanner(max_workers=4)
    apps = scanner.scan_all()
    return [{"name": a.name, "path": a.path, "source": a.source} for a in apps]


def _load_app_embedder(apps: list[dict[str, Any]]) -> tuple[Any, bool]:
    from services.app_embeddings import AppEmbeddingService

    app_embedder = AppEmbeddingService()
    cache_hit = app_embedder.initialize_or_load(apps, APP_EMBEDDING_CACHE)
    return app_embedder, cache_hit


def _load_moonshine() -> tuple[Any, str | None]:
    from app.services.stt.moonshine_service import MoonshineSTT

    moonshine = MoonshineSTT()
    try:
        moonshine.initialize()
        return moonshine, None
    except Exception as exc:
        return moonshine, str(exc)


def _load_stt_manager(moonshine: Any) -> Any:
    from app.services.stt.stt_manager import STTManager

    return STTManager(moonshine)


def _load_piper() -> Any:
    from services.tts.piper_service import PiperTTS

    return PiperTTS()


def _load_app_cache() -> list[dict[str, Any]] | None:
    try:
        payload = json.loads(APP_SCAN_CACHE.read_text(encoding="utf-8"))
        if payload.get("version") != 1:
            return None
        apps = payload.get("apps")
        if not isinstance(apps, list):
            return None
        return [
            {
                "name": str(app.get("name", "")),
                "path": str(app.get("path", "")),
                "source": str(app.get("source", "")),
            }
            for app in apps
            if app.get("name")
        ]
    except (OSError, json.JSONDecodeError, TypeError, AttributeError):
        return None


def _save_app_cache(apps: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "fingerprint": _app_fingerprint(apps), "apps": apps}
    APP_SCAN_CACHE.write_text(json.dumps(payload), encoding="utf-8")


def _app_fingerprint(apps: list[dict[str, Any]]) -> str:
    import hashlib

    raw = json.dumps(sorted(apps, key=lambda a: (a.get("name", ""), a.get("path", ""))), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend starting")
    _init_state(app)
    _write_progress(0.01, "core", "API ready")
    task = asyncio.create_task(_background_initialization(app))
    _track_task(app, task)
    try:
        yield
    finally:
        for pending in list(app.state.background_tasks):
            pending.cancel()
        if app.state.background_tasks:
            await asyncio.gather(*app.state.background_tasks, return_exceptions=True)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    lifespan=lifespan,
)

configure_cors(app)
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

