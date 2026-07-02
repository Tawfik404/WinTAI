import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    path = params.get("app_path", "")
    if not path:
        return _error("No app_path provided")

    if not os.path.isfile(path):
        return _error(f"File not found: {path}")

    try:
        if path.lower().endswith(".lnk"):
            os.startfile(path)
        else:
            subprocess.Popen(
                [path],
                shell=False,
                close_fds=True,
            )
        logger.info("Launched: %s", path)
        return {
            "success": True,
            "tool": "open_app",
            "params": {"app_path": path},
            "message": f"Launched {os.path.basename(path)}",
            "error": None,
        }
    except Exception as e:
        logger.error("Failed to launch %s: %s", path, e)
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "open_app",
        "error": msg,
    }
