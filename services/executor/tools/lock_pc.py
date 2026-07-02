import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    try:
        cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
        subprocess.run(cmd, check=True, timeout=10)
        logger.info("Workstation locked")
        return {
            "success": True,
            "tool": "lock_pc",
            "params": {},
            "message": "Workstation locked",
            "error": None,
        }
    except Exception as e:
        logger.error("Lock error: %s", e)
        return {"success": False, "tool": "lock_pc", "error": str(e)}
