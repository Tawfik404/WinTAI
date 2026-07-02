import logging
import winreg

from services.app_scanner.models import App

logger = logging.getLogger(__name__)

_REGISTRY_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _scan_key(hive: int, key_path: str) -> list[App]:
    apps: list[App] = []

    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return apps
    except Exception:
        logger.error("Error opening registry: %s", key_path, exc_info=True)
        return apps

    try:
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                i += 1
            except OSError:
                break

            try:
                subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
            except Exception:
                continue

            try:
                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
            except FileNotFoundError:
                winreg.CloseKey(subkey)
                continue

            display_name = display_name.strip() if display_name else ""
            if not display_name:
                winreg.CloseKey(subkey)
                continue

            path = ""
            try:
                path, _ = winreg.QueryValueEx(subkey, "InstallLocation")
            except FileNotFoundError:
                try:
                    uninstall, _ = winreg.QueryValueEx(subkey, "UninstallString")
                    if uninstall:
                        import shlex
                        parts = shlex.split(uninstall)
                        if parts:
                            path = parts[0]
                except Exception:
                    pass

            if not path:
                path = display_name

            winreg.CloseKey(subkey)

            apps.append(App(
                name=display_name,
                path=path,
                source="registry",
                confidence=0.95,
            ))
    finally:
        winreg.CloseKey(key)

    return apps


def scan() -> list[App]:
    apps: list[App] = []
    for hive, path in _REGISTRY_PATHS:
        apps.extend(_scan_key(hive, path))
    logger.debug("Registry scan found %d apps", len(apps))
    return apps
