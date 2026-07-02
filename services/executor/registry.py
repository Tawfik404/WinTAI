TOOLS: dict[str, dict] = {
    "open_app": {
        "name": "open_app",
        "description": "Launch or start any installed application on Windows by file path",
        "params_schema": {
            "app_path": {
                "type": "str",
                "required": True,
                "description": "Full path to the executable (.exe)",
            },
        },
        "handler": "services.executor.tools.open_app",
    },
    "open_url": {
        "name": "open_url",
        "description": "Open a web URL in the default browser",
        "params_schema": {
            "url": {
                "type": "str",
                "required": True,
                "description": "Full URL starting with http:// or https://",
            },
        },
        "handler": "services.executor.tools.open_url",
    },
    "shutdown_pc": {
        "name": "shutdown_pc",
        "description": "Shut down the computer immediately or with a delay",
        "params_schema": {
            "force": {
                "type": "bool",
                "required": False,
                "default": True,
                "description": "If true, shutdown immediately. If false, 60s grace period.",
            },
        },
        "handler": "services.executor.tools.shutdown_pc",
    },
    "file_explorer": {
        "name": "file_explorer",
        "description": "Open Windows File Explorer, optionally to a specific directory",
        "params_schema": {
            "path": {
                "type": "str",
                "required": False,
                "default": "",
                "description": "Directory path to open (empty = default)",
            },
        },
        "handler": "services.executor.tools.file_explorer",
    },
}


def get_tool(name: str) -> dict | None:
    return TOOLS.get(name)


def list_tools() -> list[str]:
    return list(TOOLS.keys())
