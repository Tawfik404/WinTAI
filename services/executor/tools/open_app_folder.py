import logging
import os
import subprocess

from services.executor.tools._window_util import get_app_name_from_path

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    app_path = params.get("app_path", "")
    if not app_path:
        return _error("No app_path provided")

    if not os.path.isfile(app_path):
        return _error(f"File not found: {app_path}")

    folder = os.path.dirname(app_path)
    if not os.path.isdir(folder):
        return _error(f"Directory not found: {folder}")

    try:
        subprocess.Popen(["explorer.exe", folder], shell=False, close_fds=True)
        name = get_app_name_from_path(app_path)
        return {
            "success": True,
            "tool": "open_app_folder",
            "app": name,
            "message": f"Opened folder for {name}: {folder}",
        }
    except Exception as e:
        logger.error("Failed to open folder %s: %s", folder, e)
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "open_app_folder",
        "error": msg,
    }
