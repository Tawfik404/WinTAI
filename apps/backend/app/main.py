import sys
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.cors import configure_cors
from app.api.router import api_router

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from services.registry.service import RegistryService
from services.embeddings.service import EmbeddingService

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
)

configure_cors(app)
app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    logger = logging.getLogger(__name__)

    registry = RegistryService()
    registry.load()
    app.state.registry = registry

    embedder = EmbeddingService()
    embedder.initialize()
    descriptions = registry.get_descriptions()
    embedder.build_index(descriptions)
    app.state.embedder = embedder

    logger.info(
        "Embedding service initialized with %d tools (dimension=%d).",
        len(descriptions),
        embedder.get_dimension(),
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
