import platform
import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    try:
        import psutil
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_physical": psutil.cpu_count(logical=False),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_c_total_gb": round(psutil.disk_usage("C:\\").total / (1024**3), 2),
            "disk_c_free_gb": round(psutil.disk_usage("C:\\").free / (1024**3), 2),
        }
    except ImportError:
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    logger.info("System info retrieved")
    return {
        "success": True,
        "tool": "get_system_info",
        "params": {},
        "message": str(info),
        "data": info,
        "error": None,
    }
