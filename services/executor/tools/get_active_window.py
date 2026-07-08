import logging

from services.executor.tools._window_util import get_foreground_window_info

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    try:
        info = get_foreground_window_info()
        return {
            "success": True,
            "tool": "get_active_window",
            "message": f"Active window: {info['title']} ({info['process']})",
            "data": info,
        }
    except Exception as e:
        logger.error("Failed to get active window: %s", e)
        return {
            "success": False,
            "tool": "get_active_window",
            "error": str(e),
        }
