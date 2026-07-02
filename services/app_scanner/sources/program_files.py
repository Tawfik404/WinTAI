import os
import logging

from services.app_scanner.models import App
from services.app_scanner.sources.utils import is_exe

logger = logging.getLogger(__name__)

_PROGRAM_FILES_PATHS = [
    r"C:\Program Files",
    r"C:\Program Files (x86)",
]

_SKIP_DIRS = {
    "windows", "windowsapps", "windowspowershell",
    "common files", "microsoft shared", "modifiablewindowsapps",
    "package cache", "references", "dotnet", "sdk",
    "microsoft.net", "assembly", "microsoft visual studio",
}


def _scan_dir_exes(directory: str, apps: list[App]) -> None:
    try:
        for entry in os.listdir(directory):
            fp = os.path.join(directory, entry)
            if is_exe(fp):
                name = os.path.splitext(entry)[0]
                apps.append(App(
                    name=name,
                    path=fp,
                    source="program_files",
                    confidence=0.60,
                ))
    except PermissionError:
        pass
    except Exception:
        logger.debug("Error scanning dir: %s", directory, exc_info=True)


def scan() -> list[App]:
    apps: list[App] = []

    for base in _PROGRAM_FILES_PATHS:
        if not os.path.isdir(base):
            continue

        try:
            vendor_entries = os.listdir(base)
        except Exception:
            logger.debug("Cannot list: %s", base, exc_info=True)
            continue

        for vendor in vendor_entries:
            vendor_path = os.path.join(base, vendor)

            if not os.path.isdir(vendor_path):
                continue
            if vendor.lower() in _SKIP_DIRS:
                continue

            # Level 1: .exe files directly in vendor folder
            _scan_dir_exes(vendor_path, apps)

            # Level 2: one subdirectory deeper
            try:
                app_entries = os.listdir(vendor_path)
            except PermissionError:
                continue
            except Exception:
                continue

            for sub in app_entries:
                sub_path = os.path.join(vendor_path, sub)
                if os.path.isdir(sub_path):
                    _scan_dir_exes(sub_path, apps)

    logger.debug("Program Files scan found %d apps", len(apps))
    return apps
