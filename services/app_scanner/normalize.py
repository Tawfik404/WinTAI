import re
from typing import List, Dict

from services.app_scanner.models import App

_SOURCE_PRIORITY: dict[str, int] = {
    "registry": 1,
    "start_menu": 2,
    "appx": 3,
    "desktop": 4,
    "program_files": 5,
}


def normalize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'\.(exe|lnk|appref-ms)$', "", name, flags=re.IGNORECASE)
    name = re.sub(r'\s+v?\d+(\.\d+)*\s*$', "", name)
    name = re.sub(r'\s+', " ", name).strip()
    return name


def deduplicate(apps: list[App]) -> list[App]:
    groups: dict[str, list[App]] = {}

    for app in apps:
        key = normalize_name(app.name).casefold()
        groups.setdefault(key, []).append(app)

    result: list[App] = []
    for _key, group in groups.items():
        group.sort(key=lambda a: _SOURCE_PRIORITY.get(a.source, 99))
        best = group[0]
        longest_name = max((a.name for a in group if a.name.strip()), key=len)
        best.name = longest_name
        for other in group[1:]:
            if best.path == best.name and other.path != other.name:
                best.path = other.path
        result.append(best)

    return result
