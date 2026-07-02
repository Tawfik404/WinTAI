import os
import logging

logger = logging.getLogger(__name__)

_lnk_resolver = None


def _get_lnk_resolver():
    global _lnk_resolver
    if _lnk_resolver is not None:
        return _lnk_resolver

    try:
        import win32com.client  # noqa: F811
        _lnk_resolver = _resolve_lnk_win32com
        logger.debug("Using win32com for .lnk resolution")
    except ImportError:
        _lnk_resolver = _resolve_lnk_fallback
        logger.debug("win32com not available; using fallback .lnk resolution")

    return _lnk_resolver


def _resolve_lnk_win32com(path: str) -> str | None:
    import win32com.client
    import pythoncom
    try:
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(path)
        target = shortcut.TargetPath
        if target and os.path.isfile(target):
            return target
    except Exception:
        logger.debug("win32com failed to resolve: %s", path, exc_info=True)
    return None


def _resolve_lnk_fallback(path: str) -> str | None:
    return None


def resolve_shortcut(path: str) -> str | None:
    resolver = _get_lnk_resolver()
    try:
        return resolver(path)
    except Exception:
        logger.debug("Failed to resolve shortcut: %s", path, exc_info=True)
    return None


def expand_path(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))


def is_exe(path: str) -> bool:
    return path.lower().endswith(".exe") and os.path.isfile(path)


def is_lnk(path: str) -> bool:
    return path.lower().endswith(".lnk") and os.path.isfile(path)
