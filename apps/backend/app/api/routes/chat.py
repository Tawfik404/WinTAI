from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatToolInfo(BaseModel):
    id: str
    name: str
    description: str


class ChatResponse(BaseModel):
    response: str
    tool: ChatToolInfo | None = None
    status: str
    reason: str | None = None


@router.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    embedder = request.app.state.embedder
    registry = request.app.state.registry

    results = embedder.search(body.message, top_k=1)

    if results and results[0][1] >= 0.25:
        tool_id, score = results[0]
        tool_def = registry.get_tool(tool_id)

        if tool_def:
            response_text = f"Tool: {tool_id}\nStatus: Success"
            return ChatResponse(
                response=response_text,
                tool=ChatToolInfo(
                    id=tool_id,
                    name=tool_def.get("name", tool_id),
                    description=tool_def.get("description", ""),
                ),
                status="Success",
            )

    response_text = "Tool: unknown\nStatus: Failed\nReason: No matching tool found for your request."
    return ChatResponse(
        response=response_text,
        status="Failed",
        reason="No matching tool found for your request.",
    )
