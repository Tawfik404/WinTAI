import re
import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


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
    execution: dict | None = None


@router.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    embedder = request.app.state.embedder
    registry = request.app.state.registry
    app_embedder = getattr(request.app.state, "app_embedder", None)
    executor = getattr(request.app.state, "executor", None)

    results = embedder.search(body.message, top_k=1)

    if not results or results[0][1] < 0.25:
        return ChatResponse(
            response="No matching tool found for your request.",
            status="Failed",
            reason="No matching tool found for your request.",
        )

    tool_id, score = results[0]
    tool_def = registry.get_tool(tool_id)

    if not tool_def:
        return ChatResponse(
            response="Tool identified but definition not found.",
            status="Failed",
            reason="Tool definition missing.",
        )

    tool_info = ChatToolInfo(
        id=tool_id,
        name=tool_def.get("name", tool_id),
        description=tool_def.get("description", ""),
    )

    params = _resolve_params(tool_id, body.message, app_embedder)

    if params is None:
        return ChatResponse(
            response=f"Matched tool '{tool_id}' but could not resolve parameters.",
            tool=tool_info,
            status="Failed",
            reason="Parameter resolution failed.",
        )

    if executor:
        try:
            execution = executor.execute(tool_id, params)
        except Exception as e:
            logger.error("Execution failed: %s", e)
            return ChatResponse(
                response=f"Tool '{tool_id}' matched but execution failed.",
                tool=tool_info,
                status="Failed",
                reason=str(e),
            )

        if execution.get("success"):
            msg = execution.get("message", "Executed successfully")
            return ChatResponse(
                response=msg,
                tool=tool_info,
                status="Success",
                execution=execution,
            )
        else:
            return ChatResponse(
                response=execution.get("error", "Execution failed"),
                tool=tool_info,
                status="Failed",
                reason=execution.get("error"),
                execution=execution,
            )

    return ChatResponse(
        response=f"Tool: {tool_id}\nStatus: Success",
        tool=tool_info,
        status="Success",
    )


def _resolve_params(
    tool_id: str, message: str, app_embedder
) -> dict | None:
    if tool_id == "open_app":
        if not app_embedder or app_embedder.get_index_size() == 0:
            return None
        result = app_embedder.search(message)
        path = result.get("path", "")
        if not path or result.get("confidence", 0) < 0.3:
            return None
        return {"app_path": path}

    if tool_id == "open_url":
        match = _URL_RE.search(message)
        if match:
            return {"url": match.group(0)}
        words = message.split()
        for w in words:
            w = w.strip().lower()
            if "." in w and not w.startswith(("open", "launch", "start", "run", "go to", "navigate")):
                if not w.startswith("http"):
                    w = "https://" + w
                return {"url": w}
        return None

    if tool_id == "shutdown_pc":
        force = "force" in message.lower() or "now" in message.lower() or "immediately" in message.lower()
        return {"force": force}

    if tool_id == "file_explorer":
        words = message.lower().split()
        for kw in ["documents", "downloads", "desktop", "pictures", "music", "videos"]:
            if kw in message.lower():
                import os
                known = {
                    "documents": "Documents",
                    "downloads": "Downloads",
                    "desktop": "Desktop",
                    "pictures": "Pictures",
                    "music": "Music",
                    "videos": "Videos",
                }
                return {"path": os.path.join(os.path.expanduser("~"), known[kw])}
        return {"path": ""}

    return {}
