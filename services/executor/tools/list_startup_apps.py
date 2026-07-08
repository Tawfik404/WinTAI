import logging
import os

import winreg

logger = logging.getLogger(__name__)

_REGISTRY_PATHS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
]


def _scan_registry() -> list[dict]:
    entries: list[dict] = []
    for hkey, subkey in _REGISTRY_PATHS:
        try:
            with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        enabled = True

                        # Check if entry starts with a comment or is empty
                        if name.startswith("!") or not value.strip():
                            enabled = False

                        entries.append({
                            "name": name,
                            "enabled": enabled,
                            "path": value.strip(),
                            "source": "registry",
                        })
                        i += 1
                    except OSError:
                        break
        except (PermissionError, OSError):
            continue
    return entries


def _scan_startup_folder() -> list[dict]:
    entries: list[dict] = []
    startup_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
    ]

    for startup_dir in startup_dirs:
        if not os.path.isdir(startup_dir):
            continue
        try:
            for entry in os.listdir(startup_dir):
                full_path = os.path.join(startup_dir, entry)
                if os.path.isfile(full_path) and (
                    entry.lower().endswith(".lnk") or entry.lower().endswith(".url")
                ):
                    name = os.path.splitext(entry)[0]
                    entries.append({
                        "name": name,
                        "enabled": True,
                        "path": full_path,
                        "source": "startup_folder",
                    })
        except (PermissionError, OSError):
            continue

    return entries


def execute(params: dict) -> dict:
    try:
        registry_entries = _scan_registry()
        folder_entries = _scan_startup_folder()

        all_entries = registry_entries + folder_entries

        seen = set()
        unique: list[dict] = []
        for entry in all_entries:
            key = (entry["name"].lower(), entry["path"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(entry)

        return {
            "success": True,
            "tool": "list_startup_apps",
            "message": f"Found {len(unique)} startup program(s).",
            "data": unique,
        }
    except Exception as e:
        logger.error("Failed to list startup apps: %s", e)
        return {
            "success": False,
            "tool": "list_startup_apps",
            "error": str(e),
        }
