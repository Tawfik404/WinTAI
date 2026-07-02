import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RegistryService:
    def __init__(self, registry_path: str | None = None) -> None:
        if registry_path is None:
            registry_path = str(Path(__file__).resolve().parent / "tools.json")
        self._path = registry_path
        self._tools: list[dict[str, Any]] = []

    def load(self) -> None:
        logger.info("Loading registry from '%s'...", self._path)
        with open(self._path, encoding="utf-8") as f:
            self._tools = json.load(f)
        logger.info("Registry loaded with %d tools.", len(self._tools))

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    def get_tool(self, name: str) -> dict[str, Any] | None:
        for tool in self._tools:
            if tool["id"] == name:
                return tool
        return None

    def get_descriptions(self) -> list[tuple[str, str]]:
        combined: list[tuple[str, str]] = []
        for t in self._tools:
            text = t["description"]
            examples = t.get("examples", [])
            if examples:
                text = text + " " + " ".join(examples)
            combined.append((t["id"], text))
        return combined
