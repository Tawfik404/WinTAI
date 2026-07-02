import logging

from services.tools import tool_registry as _registry

logger = logging.getLogger(__name__)


class RegistryService:
    def load(self) -> None:
        logger.info(
            "Registry loaded from tool_registry: %d tools.",
            len(_registry.TOOL_REGISTRY),
        )

    def list_tools(self) -> list[dict]:
        return _registry.list_tools()

    def get_tool(self, name: str) -> dict | None:
        return _registry.get_tool(name)

    def get_descriptions(self) -> list[tuple[str, str]]:
        return _registry.get_descriptions()
