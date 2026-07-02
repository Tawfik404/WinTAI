import os
import logging

from services.app_scanner.models import App
from services.app_scanner.sources.utils import expand_path, is_lnk, resolve_shortcut

logger = logging.getLogger(__name__)

_DESKTOP_PATHS = [
    r"%USERPROFILE%\Desktop",
    r"%PUBLIC%\Desktop",
]


def scan() -> list[App]:
    apps: list[App] = []
    seen_paths: set[str] = set()

    for raw in _DESKTOP_PATHS:
        base = expand_path(raw)
        if not os.path.isdir(base):
            continue
        try:
            for entry in os.listdir(base):
                fp = os.path.join(base, entry)
                if not is_lnk(fp):
                    continue
                if fp in seen_paths:
                    continue
                seen_paths.add(fp)

                target = resolve_shortcut(fp)
                name = os.path.splitext(entry)[0]
                app_path = target if target and os.path.isfile(target) else fp

                apps.append(App(
                    name=name,
                    path=app_path,
                    source="desktop",
                    confidence=0.70,
                ))
        except Exception:
            logger.error("Error scanning desktop: %s", base, exc_info=True)

    logger.debug("Desktop scan found %d apps", len(apps))
    return apps
