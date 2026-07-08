import logging

from services.executor.tools._window_util import enum_windows

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    try:
        windows = enum_windows()
    except Exception as e:
        logger.error("Failed to enumerate windows: %s", e)
        return {
            "success": False,
            "tool": "window_list",
            "error": str(e),
        }

    return {
        "success": True,
        "tool": "window_list",
        "message": f"Found {len(windows)} open window(s).",
        "data": windows,
    }
