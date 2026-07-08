import logging

from services.executor.tools._window_util import (
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
        return _error(f"Refusing to force close critical system process: {app_name}")

    processes = find_processes_by_name(app_name)
    if not processes:
        return {
            "success": False,
            "tool": "force_close_app",
            "error": f"No running process found for {app_name}.",
        }

    killed = []
    failed = []
    for proc in processes:
        try:
            proc.kill()
            killed.append(proc.name())
        except Exception as e:
            failed.append(f"{proc.name()}: {e}")

    if killed and not failed:
        return {
            "success": True,
            "tool": "force_close_app",
            "app": app_name,
            "message": f"{app_name} terminated ({len(killed)} process{'es' if len(killed) > 1 else ''}).",
        }

    if killed:
        return {
            "success": True,
            "tool": "force_close_app",
            "app": app_name,
            "message": f"{app_name} partially terminated. Failures: {'; '.join(failed)}",
        }

    return {
        "success": False,
        "tool": "force_close_app",
        "error": f"Could not terminate {app_name}: {'; '.join(failed)}",
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "force_close_app",
        "error": msg,
    }
