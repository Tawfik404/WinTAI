import logging

from services.executor.tools._window_util import (
    find_window_by_app_name,
    activate_window,
    get_app_name_from_path,
)

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    app_name = params.get("app_name", "")
    if not app_name:
        return _error("No app_name provided")

    window = find_window_by_app_name(app_name)
    if not window:
        return {
            "success": False,
            "tool": "focus_app",
            "error": f"No visible window found for {app_name}.",
        }

    if activate_window(window["hwnd"]):
        return {
            "success": True,
            "tool": "focus_app",
            "app": app_name,
            "message": f"{window['process'].replace('.exe', '')} brought to foreground.",
        }

    return {
        "success": False,
        "tool": "focus_app",
        "error": f"Could not activate window for {app_name}.",
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "focus_app",
        "error": msg,
    }
