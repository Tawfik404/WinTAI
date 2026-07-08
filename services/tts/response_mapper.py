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
    "close_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} closed." if p else "Application closed.",
        "failure": lambda p: f"I could not close {p.get('app_name', 'the application')}." if p else "I could not close the application.",
    },
    "focus_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} brought to front." if p else "Window focused.",
        "failure": lambda p: f"I could not focus {p.get('app_name', 'the application')}." if p else "I could not focus the application.",
    },
    "restart_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} restarted." if p else "Application restarted.",
        "failure": lambda p: f"I could not restart {p.get('app_name', 'the application')}." if p else "I could not restart the application.",
    },
    "force_close_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} terminated." if p else "Application terminated.",
        "failure": lambda p: f"I could not terminate {p.get('app_name', 'the application')}." if p else "I could not terminate the application.",
    },
    "open_app_folder": {
        "success": lambda p: f"Folder opened for {p.get('app_name', 'app')}." if p else "Application folder opened.",
        "failure": lambda p: f"I could not open the folder for {p.get('app_name', 'the application')}." if p else "I could not open the application folder.",
    },
    "get_app_details": {
        "success": lambda p: f"Details retrieved for {p.get('app_name', 'app')}." if p else "Application details retrieved.",
        "failure": lambda p: f"I could not get details for {p.get('app_name', 'the application')}." if p else "I could not get application details.",
    },
    "get_active_window": {
        "success": lambda p: "Active window details retrieved.",
        "failure": lambda p: "I could not get the active window.",
    },
    "window_list": {
        "success": lambda p: "Window list retrieved.",
        "failure": lambda p: "I could not list windows.",
    },
    "minimize_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} minimized." if p else "Window minimized.",
        "failure": lambda p: f"I could not minimize {p.get('app_name', 'the application')}." if p else "I could not minimize the window.",
    },
    "maximize_app": {
        "success": lambda p: f"{p.get('app_name', 'App')} maximized." if p else "Window maximized.",
        "failure": lambda p: f"I could not maximize {p.get('app_name', 'the application')}." if p else "I could not maximize the window.",
    },
    "snap_window": {
        "success": lambda p: f"Window snapped to {p.get('position', 'position')}." if p else "Window snapped.",
        "failure": lambda p: f"I could not snap the window for {p.get('app_name', 'the application')}." if p else "I could not snap the window.",
    },
    "list_startup_apps": {
        "success": lambda p: "Startup programs listed.",
        "failure": lambda p: "I could not list startup programs.",
    },
    "open_app": {
        "success": _open_app_success,
        "failure": _open_app_failure,
    },
    "open_url": {
        "success": lambda p: "Website opened.",
        "failure": lambda p: "I could not open the website.",
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
