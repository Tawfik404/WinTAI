import logging
import os
import subprocess
import time

from services.executor.tools._window_util import (
    find_processes_by_name,
    close_window_by_hwnd,
    find_windows_by_app_name,
    get_app_name_from_path,
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
        return _error(f"Refusing to restart critical system process: {app_name}")

    processes = find_processes_by_name(app_name)
    if not processes:
        return {
            "success": False,
            "tool": "restart_app",
            "error": f"No running process found for {app_name}.",
        }

    exe_path = None
    for p in processes:
        try:
            exe_path = p.exe()
            if exe_path:
                break
        except Exception:
            continue

    if not exe_path:
        try:
            exe_path = processes[0].exe()
        except Exception:
            pass

    windows = find_windows_by_app_name(app_name)
    for w in windows:
        close_window_by_hwnd(w["hwnd"])

    time.sleep(0.5)

    for p in processes:
        try:
            p.terminate()
        except Exception:
            continue

    time.sleep(1)

    if exe_path and os.path.isfile(exe_path):
        try:
            subprocess.Popen([exe_path], shell=False, close_fds=True)
            name = get_app_name_from_path(exe_path)
            return {
                "success": True,
                "tool": "restart_app",
                "app": app_name,
                "message": f"{name} restarted.",
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "restart_app",
                "error": f"Closed {app_name} but could not relaunch: {e}",
            }

    return {
        "success": True,
        "tool": "restart_app",
        "app": app_name,
        "message": f"{app_name} closed for restart, but executable path not found.",
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "restart_app",
        "error": msg,
    }
