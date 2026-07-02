import os
import logging

from services.app_scanner.models import App
from services.app_scanner.sources.utils import expand_path, is_lnk, resolve_shortcut

logger = logging.getLogger(__name__)

_START_MENU_PATHS = [
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs",
    r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs",
]


def scan() -> list[App]:
    apps: list[App] = []
    seen_paths: set[str] = set()

    for raw in _START_MENU_PATHS:
        base = expand_path(raw)
        if not os.path.isdir(base):
            continue
        try:
            for root, _dirs, files in os.walk(base):
                for f in files:
                    fp = os.path.join(root, f)
                    if not is_lnk(fp):
                        continue
                    if fp in seen_paths:
                        continue
                    seen_paths.add(fp)

                    target = resolve_shortcut(fp)
                    name = os.path.splitext(f)[0]
                    app_path = target if target and os.path.isfile(target) else fp

                    apps.append(App(
                        name=name,
                        path=app_path,
                        source="start_menu",
                        confidence=0.90,
                    ))
        except Exception:
            logger.error("Error scanning start menu: %s", base, exc_info=True)

    logger.debug("Start Menu scan found %d apps", len(apps))
    return apps
