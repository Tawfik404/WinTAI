import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    force = params.get("force", True)
    delay = 0 if force else 60

    try:
        cmd = ["shutdown", "/s", "/t", str(delay)]
        subprocess.run(cmd, check=True, timeout=10)
        logger.info("Shutdown initiated (force=%s, delay=%ds)", force, delay)
        return {
            "success": True,
            "tool": "shutdown_pc",
            "params": {"force": force},
            "message": "Shutdown command sent"
            if force
            else "Shutdown scheduled in 60 seconds",
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return _error("Shutdown command timed out")
    except subprocess.CalledProcessError as e:
        return _error(f"Shutdown failed (exit code {e.returncode})")
    except Exception as e:
        logger.error("Shutdown error: %s", e)
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "shutdown_pc",
        "error": msg,
    }
