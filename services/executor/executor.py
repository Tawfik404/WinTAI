import importlib
import logging
import time

from services.executor.registry import get_tool
from services.executor.validator import validate, ValidationError

logger = logging.getLogger(__name__)


class ToolExecutor:
    def execute(self, tool_name: str, params: dict) -> dict:
        t0 = time.perf_counter()
        logger.info("Executing tool: %s", tool_name)

        try:
            validated = validate(tool_name, params)
        except ValidationError as e:
            logger.warning("Validation failed for %s: %s", tool_name, e)
            return _failure(tool_name, str(e))

        tool_def = get_tool(tool_name)
        handler = _load_handler(tool_def["handler"])
        if handler is None:
            return _failure(tool_name, f"Handler not found for tool: {tool_name}")

        try:
            result = handler(validated)
            elapsed = time.perf_counter() - t0
            logger.info(
                "Tool %s completed: success=%s (%.2fs)",
                tool_name,
                result.get("success"),
                elapsed,
            )
            return result
        except Exception as e:
            logger.error("Tool %s threw: %s", tool_name, e, exc_info=True)
            return _failure(tool_name, str(e))


def _load_handler(module_path: str):
    try:
        mod = importlib.import_module(module_path)
        return mod.execute
    except ImportError as e:
        logger.error("Cannot import handler module %s: %s", module_path, e)
        return None


def _failure(tool_name: str, msg: str) -> dict:
    return {
        "success": False,
        "tool": tool_name,
        "error": msg,
    }
