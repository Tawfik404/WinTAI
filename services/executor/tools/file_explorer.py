import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    path = params.get("path", "").strip()

    if path:
        resolved = os.path.expandvars(os.path.expanduser(path))
        if not os.path.exists(resolved):
            return _error(f"Path not found: {path}")
        if not os.path.isdir(resolved):
            resolved = os.path.dirname(resolved) or resolved
    else:
        resolved = ""

    try:
        if resolved:
            subprocess.Popen(["explorer", resolved], shell=False)
            logger.info("Opened explorer: %s", resolved)
        else:
            subprocess.Popen(["explorer"], shell=False)
            logger.info("Opened explorer (default)")

        return {
            "success": True,
            "tool": "file_explorer",
            "params": {"path": resolved},
            "message": "Explorer opened"
            if not resolved
            else f"Opened {resolved}",
            "error": None,
        }
    except Exception as e:
        logger.error("Failed to open explorer: %s", e)
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "file_explorer",
        "error": msg,
    }
