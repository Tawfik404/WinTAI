import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    force = params.get("force", True)
    delay = 0 if force else 60

    try:
        cmd = ["shutdown", "/r", "/t", str(delay)]
        subprocess.run(cmd, check=True, timeout=10)
        logger.info("Restart initiated (force=%s, delay=%ds)", force, delay)
        return {
            "success": True,
            "tool": "restart_pc",
            "params": {"force": force},
            "message": "Restart command sent"
            if force
            else "Restart scheduled in 60 seconds",
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "tool": "restart_pc", "error": "Restart command timed out"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "tool": "restart_pc", "error": f"Restart failed (exit code {e.returncode})"}
    except Exception as e:
        logger.error("Restart error: %s", e)
        return {"success": False, "tool": "restart_pc", "error": str(e)}
