import logging
import time

from services.executor.tools._window_util import (
    find_windows_by_app_name,
    close_window_by_hwnd,
    find_processes_by_name,
)

logger = logging.getLogger(__name__)

_CRITICAL_PROCESSES = {
    "winlogon", "csrss", "services", "lsass", "svchost",
    "system", "smss", "wininit", "explorer",
}


def execute(params: dict) -> dict:
    app_name = params.get("app_name", "")
    if not app_name:
        return _error("No app_name provided")

    app_key = app_name.lower().replace(".exe", "")
    if app_key in _CRITICAL_PROCESSES:
        return _error(f"Refusing to close critical system process: {app_name}")

    windows = find_windows_by_app_name(app_name)
    closed_via_window = False
    for w in windows:
        if close_window_by_hwnd(w["hwnd"]):
            closed_via_window = True

    time.sleep(0.5)

    processes = find_processes_by_name(app_name)
    still_running = []
    for proc in processes:
        try:
            if proc.is_running():
                still_running.append(proc)
        except Exception:
            continue

    if not still_running and not closed_via_window:
        return {
            "success": True,
            "tool": "close_app",
            "app": app_name,
            "message": f"{app_name} was not running.",
        }

    if not still_running:
        return {
            "success": True,
            "tool": "close_app",
            "app": app_name,
            "message": f"{app_name} closed.",
        }

    if closed_via_window and not still_running:
        return {
            "success": True,
            "tool": "close_app",
            "app": app_name,
            "message": f"{app_name} closed.",
        }

    still_names = []
    for p in still_running:
        try:
            still_names.append(p.name())
        except Exception:
            continue

    return {
        "success": False,
        "tool": "close_app",
        "app": app_name,
        "error": f"Could not close {app_name}. Processes still running: {', '.join(still_names)}",
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "close_app",
        "error": msg,
    }
