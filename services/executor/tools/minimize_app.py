import logging

from services.executor.tools._window_util import (
    find_window_by_app_name,
    show_window,
    SW_MINIMIZE,
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
            "tool": "minimize_app",
            "error": f"No visible window found for {app_name}.",
        }

    if show_window(window["hwnd"], SW_MINIMIZE):
        return {
            "success": True,
            "tool": "minimize_app",
            "app": app_name,
            "message": f"{window['process'].replace('.exe', '')} minimized.",
        }

    return {
        "success": False,
        "tool": "minimize_app",
        "error": f"Could not minimize window for {app_name}.",
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "minimize_app",
        "error": msg,
    }
