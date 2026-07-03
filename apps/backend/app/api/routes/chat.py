import re
import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import get_settings
from services.app_resolver import AppResolver
from services.tools import tool_registry
from services.tts.response_mapper import build_tts_message

router = APIRouter()
logger = logging.getLogger(__name__)

_resolver = AppResolver()
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
    tts: str | None = None


@router.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    settings = get_settings()
    embedder = request.app.state.embedder
    registry = request.app.state.registry
    app_embedder = getattr(request.app.state, "app_embedder", None)
    executor = getattr(request.app.state, "executor", None)

    logger.info("[QUERY] %s", body.message)

    results = embedder.search(body.message, top_k=5)

    if not results:
        logger.info("[TOOL MATCH] none | Score: 0.0 | Decision: NO_MATCH (no results)")
        return ChatResponse(
            response="No matching tool found for your request.",
            status="Failed",
            reason="No matching tool found for your request.",
        )

    logger.info("[TOOL MATCH] candidates=%s", [(tid, round(s, 4)) for tid, s in results])

    tool_id, score = results[0]
    threshold = settings.tool_similarity_threshold

    # Fallback: use best candidate even if below threshold
    fallback_used = score < threshold
    if fallback_used:
        logger.info(
            "[TOOL MATCH] %s (%.2f) | Threshold: %.2f | Decision: FALLBACK (best available)",
            tool_id, score, threshold,
        )
    else:
        logger.info(
            "[TOOL MATCH] %s (%.2f) | Threshold: %.2f | Decision: ACCEPTED",
            tool_id, score, threshold,
        )

    tool_def = registry.get_tool(tool_id)
    if not tool_def:
        all_ids = [t["id"] for t in tool_registry.list_tools()]
        suggestion = ""
        from difflib import get_close_matches
        close = get_close_matches(tool_id, all_ids, n=1, cutoff=0.5)
        if close:
            suggestion = close[0]
        logger.error(
            "[SAFETY] Tool '%s' not in registry. Suggestion: %s",
            tool_id, suggestion or "none",
        )
        return ChatResponse(
            response=f"Tool not found in registry",
            status="Failed",
            reason=f"Tool '{tool_id}' is not registered",
        )

    tool_info = ChatToolInfo(
        id=tool_id,
        name=tool_def.get("name", tool_id),
        description=tool_def.get("description", ""),
    )

    params = _resolve_params(
        tool_id, body.message, app_embedder, settings
    )

    if params is None:
        logger.info("[DECISION] fallback_used=%s | params=None", fallback_used)
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

        success = execution.get("success", False)
        tts_msg = build_tts_message(tool_id, success, params)
        if success:
            msg = execution.get("message", "Executed successfully")
            return ChatResponse(
                response=msg,
                tool=tool_info,
                status="Success",
                execution=execution,
                tts=tts_msg,
            )
        else:
            return ChatResponse(
                response=execution.get("error", "Execution failed"),
                tool=tool_info,
                status="Failed",
                reason=execution.get("error"),
                execution=execution,
                tts=tts_msg,
            )

    return ChatResponse(
        response=f"Tool: {tool_id}\nStatus: Success",
        tool=tool_info,
        status="Success",
    )


def _resolve_params(
    tool_id: str, message: str, app_embedder, settings=None
) -> dict | None:
    if tool_id == "open_app":
        if not app_embedder or app_embedder.get_index_size() == 0:
            return None

        result = app_embedder.search(message)
        app_name = result.get("name", "")
        raw_path = result.get("path", "")
        confidence = result.get("confidence", 0)
        threshold = settings.app_similarity_threshold if settings else 0.55

        logger.info("[APP MATCHES]")
        logger.info("  1. %s (%.2f)", app_name, confidence)

        resolved_path = _resolver.resolve(raw_path, app_name)
        logger.info("[RESOLVED PATH] %s", resolved_path)

        fallback_used = confidence < threshold
        logger.info(
            "[DECISION] fallback_used=%s confidence=%.2f threshold=%.2f",
            fallback_used, confidence, threshold,
        )

        if not resolved_path or not resolved_path.lower().endswith(".exe"):
            logger.info("[DECISION] REJECTED: no valid .exe path")
            return None

        return {"app_path": resolved_path}

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
