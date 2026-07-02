import json
import logging
import subprocess

from services.app_scanner.models import App

logger = logging.getLogger(__name__)

PS_SCRIPT = """
Get-AppxPackage | Select-Object Name, InstallLocation | ConvertTo-Json -Compress
"""


def scan() -> list[App]:
    apps: list[App] = []

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        logger.warning("PowerShell not found; skipping AppX scan")
        return apps
    except subprocess.TimeoutExpired:
        logger.warning("AppX scan timed out after 30s")
        return apps
    except Exception:
        logger.error("AppX scan failed", exc_info=True)
        return apps

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            logger.warning("PowerShell AppX query returned error: %s", stderr)
        return apps

    stdout = result.stdout.strip()
    if not stdout:
        return apps

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        logger.warning("Failed to parse AppX JSON output")
        return apps

    if isinstance(data, dict):
        data = [data]

    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = (entry.get("Name") or "").strip()
        if not name:
            continue
        install_location = (entry.get("InstallLocation") or "").strip()

        apps.append(App(
            name=name,
            path=install_location if install_location else name,
            source="appx",
            confidence=0.85,
        ))

    logger.debug("AppX scan found %d apps", len(apps))
    return apps
