import logging

logger = logging.getLogger(__name__)


def _open_app_success(params: dict | None) -> str:
    name = (params or {}).get("app_path", "")
    if name:
        name = name.split("\\")[-1].split("/")[-1].replace(".exe", "").replace(".lnk", "")
        if name:
            return f"{name} opened."
    return "Application opened."


def _open_app_failure(params: dict | None) -> str:
    name = (params or {}).get("app_path", "")
    if name:
        name = name.split("\\")[-1].split("/")[-1].replace(".exe", "").replace(".lnk", "")
        if name:
            return f"I could not open {name}."
    return "I could not open the application."


TOOL_RESPONSES: dict[str, dict[str, callable]] = {
    "open_app": {
        "success": _open_app_success,
        "failure": _open_app_failure,
    },
    "open_url": {
        "success": lambda p: "Website opened.",
        "failure": lambda p: "I could not open the website.",
    },
    "shutdown_pc": {
        "success": lambda p: "Shutting down now.",
        "failure": lambda p: "Shutdown failed.",
    },
    "restart_pc": {
        "success": lambda p: "Restarting now.",
        "failure": lambda p: "Restart failed.",
    },
    "hibernate_pc": {
        "success": lambda p: "Hibernating now.",
        "failure": lambda p: "Hibernation failed.",
    },
    "lock_pc": {
        "success": lambda p: "Computer locked.",
        "failure": lambda p: "I could not lock the computer.",
    },
    "file_explorer": {
        "success": lambda p: "File explorer opened.",
        "failure": lambda p: "I could not open file explorer.",
    },
    "get_system_info": {
        "success": lambda p: "System information retrieved.",
        "failure": lambda p: "I could not retrieve system information.",
    },
    "get_clipboard": {
        "success": lambda p: "Clipboard content read.",
        "failure": lambda p: "I could not read the clipboard.",
    },
    "set_clipboard": {
        "success": lambda p: "Clipboard updated.",
        "failure": lambda p: "I could not update the clipboard.",
    },
}

_DEFAULT_SUCCESS = "Done."
_DEFAULT_FAILURE = "Something went wrong."


def build_tts_message(
    tool_name: str,
    success: bool,
    params: dict | None = None,
    error: str | None = None,
) -> str:
    templates = TOOL_RESPONSES.get(tool_name)
    if templates:
        key = "success" if success else "failure"
        try:
            return templates[key](params)
        except Exception as e:
            logger.warning("TTS template error for %s: %s", tool_name, e)
    if success:
        return _DEFAULT_SUCCESS
    return _DEFAULT_FAILURE
