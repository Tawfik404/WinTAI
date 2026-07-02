TOOL_REGISTRY: list[dict] = [
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
        "id": "shutdown_pc",
        "name": "shutdown_pc",
        "description": "Power off the Windows computer completely. Use when the user wants to turn off, switch off, or shut down their machine for the day or to save power.",
        "examples": [
            "shut down my PC",
            "turn off computer",
            "power off laptop",
            "shut down Windows",
            "switch off my machine",
        ],
        "handler": "services.executor.tools.shutdown_pc",
        "params_schema": {
            "force": {
                "type": "bool",
                "required": False,
                "default": True,
                "description": "If true, shutdown immediately. If false, 60s grace period.",
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
