from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class EmbeddingTestRequest(BaseModel):
    text: str


class EmbeddingTestResponse(BaseModel):
    dimension: int
    preview: list[float]


@router.post("/api/embedding/test")
async def embedding_test(body: EmbeddingTestRequest, request: Request) -> EmbeddingTestResponse:
    embedder = request.app.state.embedder
    vector = embedder.embed(body.text)
    return EmbeddingTestResponse(
        dimension=embedder.get_dimension(),
        preview=vector[:3],
    )
