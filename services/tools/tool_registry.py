TOOL_REGISTRY: list[dict] = [
    # ──────────────────────────────────────────────
    # App Management Tools
    # ──────────────────────────────────────────────
    {
        "id": "close_app",
        "name": "close_app",
        "description": "Gracefully close a running application by name. Sends a close signal to the application window so it can exit cleanly. Use when the user wants to quit, exit, shut down, or close a program like Chrome, Discord, Spotify, or any desktop app.",
        "examples": [
            "close Chrome",
            "exit Discord",
            "quit Spotify",
            "close my browser",
            "shut down VS Code",
            "stop the terminal",
            "close app",
            "exit program",
        ],
        "handler": "services.executor.tools.close_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to close (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "focus_app",
        "name": "focus_app",
        "description": "Bring an application window to the foreground so it becomes the active window. Handles minimized windows by restoring them first. Use when the user wants to switch to a program, bring a window forward, or make an app the active window.",
        "examples": [
            "focus VS Code",
            "bring Chrome to front",
            "switch to Discord",
            "show me my browser",
            "go to the terminal window",
            "activate Spotify",
            "make Notepad the active window",
        ],
        "handler": "services.executor.tools.focus_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to focus (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "restart_app",
        "name": "restart_app",
        "description": "Restart a running application by closing it gracefully and launching it again from its original executable path. Use when the user wants to refresh an app, reboot a program, or restart software like Discord, Slack, or a game.",
        "examples": [
            "restart Discord",
            "reopen Chrome",
            "refresh Slack",
            "restart my browser",
            "reboot VS Code",
            "restart Spotify",
        ],
        "handler": "services.executor.tools.restart_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to restart (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "force_close_app",
        "name": "force_close_app",
        "description": "Forcefully terminate a frozen or unresponsive application by killing its processes. Use when the user says an app is not responding, stuck, frozen, or when graceful close failed. Only use this for user applications — never for critical system processes.",
        "examples": [
            "kill Chrome",
            "force close Discord",
            "terminate Spotify",
            "Notepad is frozen, kill it",
            "end task Slack",
            "force quit VS Code",
        ],
        "handler": "services.executor.tools.force_close_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to force close (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "open_app_folder",
        "name": "open_app_folder",
        "description": "Open the Windows File Explorer to show the installation directory of an application. Use when the user wants to see where an app is installed, browse its program files, or locate the executable on disk.",
        "examples": [
            "open Chrome folder",
            "show VS Code location",
            "where is Discord installed",
            "open the directory for Spotify",
            "show me the program files for Slack",
            "browse the install folder for Firefox",
        ],
        "handler": "services.executor.tools.open_app_folder",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application whose install folder to open (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "get_app_details",
        "name": "get_app_details",
        "description": "Return detailed metadata about an application including its executable path, version number, publisher, installation location, and whether it is currently running. Use when the user asks about app properties, version info, publisher details, or wants to know if a program is installed.",
        "examples": [
            "tell me about Chrome",
            "get details for Discord",
            "what version of VS Code do I have",
            "who published Spotify",
            "is Slack running",
            "where is Firefox installed",
            "show app info for Notepad",
        ],
        "handler": "services.executor.tools.get_app_details",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to get details for (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "get_active_window",
        "name": "get_active_window",
        "description": "Return information about the currently focused window including its title, process name, and executable path. Use when the user asks what window is active, what program is in the foreground, or what they are currently looking at on screen.",
        "examples": [
            "what window is active",
            "what is in the foreground",
            "which app is focused",
            "what am I looking at",
            "show active window info",
            "what program is currently open",
            "tell me about the current window",
        ],
        "handler": "services.executor.tools.get_active_window",
        "params_schema": {},
    },
    # ──────────────────────────────────────────────
    # Window Management Tools
    # ──────────────────────────────────────────────
    {
        "id": "window_list",
        "name": "window_list",
        "description": "List all currently open user-facing windows on the desktop, showing each window's title, associated process name, and window handle. Invisible or system windows are filtered out. Use when the user wants to see what programs are open, check running windows, or get an overview of their desktop.",
        "examples": [
            "list windows",
            "what windows are open",
            "show me open programs",
            "list running windows",
            "what apps have windows open",
            "show all desktop windows",
            "enumerate open windows",
        ],
        "handler": "services.executor.tools.window_list",
        "params_schema": {},
    },
    {
        "id": "minimize_app",
        "name": "minimize_app",
        "description": "Minimize an application window to the taskbar. Use when the user wants to hide a window, get it out of the way, or reduce an app to the taskbar without closing it.",
        "examples": [
            "minimize Chrome",
            "hide Discord",
            "minimize the browser",
            "put Spotify on the taskbar",
            "hide VS Code",
            "minimize the terminal",
            "minimize that window",
        ],
        "handler": "services.executor.tools.minimize_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to minimize (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "maximize_app",
        "name": "maximize_app",
        "description": "Maximize an application window to fill the entire screen. Use when the user wants to make a window full screen, expand it to fill the display, or get a larger view of an application.",
        "examples": [
            "maximize VS Code",
            "make Chrome full screen",
            "full screen Discord",
            "expand Spotify",
            "maximize the terminal",
            "make Notepad full screen",
        ],
        "handler": "services.executor.tools.maximize_app",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to maximize (e.g. 'Chrome', 'Discord')",
            },
        },
    },
    {
        "id": "snap_window",
        "name": "snap_window",
        "description": "Snap an application window to a specific area of the screen like Windows Snap Assist. Supports snapping to the left half, right half, top half, or bottom half of the display. Use when the user wants to arrange windows side by side or organize their screen layout.",
        "examples": [
            "snap Chrome left",
            "put VS Code on the right",
            "snap Discord to the left side",
            "move Notepad to the right half",
            "snap the browser to the top",
            "snap terminal to bottom",
            "split screen Chrome left",
        ],
        "handler": "services.executor.tools.snap_window",
        "params_schema": {
            "app_name": {
                "type": "str",
                "required": True,
                "description": "Name of the application to snap (e.g. 'Chrome', 'Discord')",
            },
            "position": {
                "type": "str",
                "required": True,
                "description": "Snap position: 'left', 'right', 'top', or 'bottom'",
            },
        },
    },
    {
        "id": "list_startup_apps",
        "name": "list_startup_apps",
        "description": "List all programs that are configured to launch automatically when Windows starts. Checks the Windows Startup folder and registry startup locations (CurrentVersion\\Run and RunOnce for both HKCU and HKLM). Use when the user wants to see startup programs, check what runs on boot, or find out which apps start automatically.",
        "examples": [
            "show startup apps",
            "list startup programs",
            "what runs at startup",
            "show me startup applications",
            "what programs start automatically",
            "list boot programs",
            "check startup items",
        ],
        "handler": "services.executor.tools.list_startup_apps",
        "params_schema": {},
    },
    # ──────────────────────────────────────────────
    # Existing Tools
    # ──────────────────────────────────────────────
    {
        "id": "open_app",
        "name": "open_app",
        "description": "Launch or start any installed application on Windows. Use when the user wants to open an app, run a program, start software, or execute something like a browser, editor, game, media player, or any desktop application.",
        "examples": [
            "open Chrome",
            "launch Discord",
            "run Steam",
            "start Visual Studio Code",
            "open Spotify",
            "open Edge browser",
            "open app",
            "launch app",
            "start application",
            "run program",
        ],
        "handler": "services.executor.tools.open_app",
        "params_schema": {
            "app_path": {
                "type": "str",
                "required": True,
                "description": "Full path to the executable (.exe)",
            },
        },
    },
    {
        "id": "open_url",
        "name": "open_url",
        "description": "Navigate to a website in the default web browser. Use when the user wants to visit, open, or go to a specific web address or online service by name or URL.",
        "examples": [
            "go to YouTube",
            "open Google",
            "visit github.com",
            "open chatgpt.com",
            "navigate to Reddit",
            "go to amazon.com",
        ],
        "handler": "services.executor.tools.open_url",
        "params_schema": {
            "url": {
                "type": "str",
                "required": True,
                "description": "Full URL starting with http:// or https://",
            },
        },
    },
    {
        "id": "restart_pc",
        "name": "restart_pc",
        "description": "Reboot the Windows computer so it starts fresh. Use when the user wants to refresh the system, apply updates, or restart after installing new software.",
        "examples": [
            "restart my computer",
            "reboot the PC",
            "restart Windows",
            "reboot the system",
            "restart my machine",
        ],
        "handler": "services.executor.tools.restart_pc",
        "params_schema": {
            "force": {
                "type": "bool",
                "required": False,
                "default": True,
                "description": "If true, restart immediately. If false, warn running programs first.",
            },
        },
    },
    {
        "id": "hibernate_pc",
        "name": "hibernate_pc",
        "description": "Put the Windows computer into a low-power sleep or hibernate state preserving the current session. Use when the user wants to conserve battery or step away temporarily without shutting down.",
        "examples": [
            "put PC to sleep",
            "hibernate computer",
            "sleep mode",
            "suspend Windows",
            "put my laptop to sleep",
        ],
        "handler": "services.executor.tools.hibernate_pc",
        "params_schema": {},
    },
    {
        "id": "lock_pc",
        "name": "lock_pc",
        "description": "Lock the Windows workstation so a password is needed to regain access. Use when the user is stepping away from their desk and wants to prevent others from using their computer.",
        "examples": [
            "lock my PC",
            "lock screen",
            "lock workstation",
            "secure my computer",
            "lock my computer when I step away",
        ],
        "handler": "services.executor.tools.lock_pc",
        "params_schema": {},
    },
    {
        "id": "file_explorer",
        "name": "file_explorer",
        "description": "Open Windows File Explorer to browse files and folders at a specific location. Use when the user wants to view directory contents, see their files, or navigate to a folder on their computer.",
        "examples": [
            "open downloads folder",
            "show my documents",
            "browse desktop files",
            "open the pictures directory",
            "show me my videos folder",
        ],
        "handler": "services.executor.tools.file_explorer",
        "params_schema": {
            "path": {
                "type": "str",
                "required": False,
                "default": "",
                "description": "Directory path to open (empty = default)",
            },
        },
    },
    {
        "id": "get_system_info",
        "name": "get_system_info",
        "description": "Show details about the Windows computer including hardware specs and system information. Use when the user asks about their machine, performance, or hardware components like RAM, CPU, or storage.",
        "examples": [
            "what are my PC specs",
            "show system information",
            "check RAM and CPU",
            "tell me about this computer",
            "how much RAM do I have",
        ],
        "handler": "services.executor.tools.get_system_info",
        "params_schema": {},
    },
    {
        "id": "get_clipboard",
        "name": "get_clipboard",
        "description": "Retrieve and show the current text stored on the Windows clipboard. Use when the user wants to recall, see, or check what text they last copied.",
        "examples": [
            "what is on my clipboard",
            "show clipboard content",
            "read copied text",
            "what did I copy",
            "check my clipboard",
        ],
        "handler": "services.executor.tools.get_clipboard",
        "params_schema": {},
    },
    {
        "id": "set_clipboard",
        "name": "set_clipboard",
        "description": "Copy new text onto the Windows clipboard so it can be pasted elsewhere. Use when the user wants to save text for later pasting or transfer text between programs.",
        "examples": [
            "copy this to clipboard",
            "save text to clipboard",
            "copy my notes",
            "put this on the clipboard",
            "copy this text",
        ],
        "handler": "services.executor.tools.set_clipboard",
        "params_schema": {
            "text": {
                "type": "str",
                "required": True,
                "description": "Text content to store on the clipboard",
            },
        },
    },
]


def get_tool(name: str) -> dict | None:
    for t in TOOL_REGISTRY:
        if t["id"] == name:
            return t
    return None


def list_tools() -> list[dict]:
    return list(TOOL_REGISTRY)


def get_descriptions() -> list[tuple[str, str]]:
    combined: list[tuple[str, str]] = []
    for t in TOOL_REGISTRY:
        text = t["description"]
        examples = t.get("examples", [])
        if examples:
            text = text + " " + " ".join(examples)
        combined.append((t["id"], text))
    return combined
