import logging

from services.tools import tool_registry as _registry

logger = logging.getLogger(__name__)

TOOLS: dict[str, dict] = {t["id"]: t for t in _registry.list_tools()}


def get_tool(name: str) -> dict | None:
    return TOOLS.get(name)


def list_tools() -> list[str]:
    return list(TOOLS.keys())
