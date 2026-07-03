from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.embedding import router as embedding_router
from app.api.routes.chat import router as chat_router
from app.api.routes.tts import router as tts_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(embedding_router, tags=["embedding"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(tts_router, tags=["tts"])
