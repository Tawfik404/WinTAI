import logging

from services.executor.tools._window_util import (
    find_window_by_app_name,
    get_screen_size,
    is_window_iconic,
    show_window,
    set_window_pos,
    SW_RESTORE,
)

logger = logging.getLogger(__name__)

_VALID_POSITIONS = {"left", "right", "top", "bottom"}


def execute(params: dict) -> dict:
    app_name = params.get("app_name", "")
    position = params.get("position", "").lower()

    if not app_name:
        return _error("No app_name provided")
    if not position or position not in _VALID_POSITIONS:
        return _error(f"Invalid position '{position}'. Valid: {', '.join(sorted(_VALID_POSITIONS))}")

    window = find_window_by_app_name(app_name)
    if not window:
        return {
            "success": False,
            "tool": "snap_window",
            "error": f"No visible window found for {app_name}.",
        }

    hwnd = window["hwnd"]
    screen_w, screen_h = get_screen_size()

    snap_rects = {
        "left": (0, 0, screen_w // 2, screen_h),
        "right": (screen_w // 2, 0, screen_w // 2, screen_h),
        "top": (0, 0, screen_w, screen_h // 2),
        "bottom": (0, screen_h // 2, screen_w, screen_h // 2),
    }

    x, y, w, h = snap_rects[position]

    try:
        if is_window_iconic(hwnd):
            show_window(hwnd, SW_RESTORE)

        set_window_pos(hwnd, x, y, w, h)

        return {
            "success": True,
            "tool": "snap_window",
            "app": app_name,
            "message": f"{window['process'].replace('.exe', '')} snapped to {position}.",
            "data": {"position": position, "x": x, "y": y, "width": w, "height": h},
        }
    except Exception as e:
        logger.error("Failed to snap window %d: %s", hwnd, e)
        return {
            "success": False,
            "tool": "snap_window",
            "error": f"Could not snap window: {e}",
        }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "snap_window",
        "error": msg,
    }
