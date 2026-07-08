import logging
import os

from services.executor.tools._window_util import (
    find_processes_by_name,
    find_windows_by_app_name,
    get_process_name_by_pid,
)

logger = logging.getLogger(__name__)


def _get_file_version(filepath: str) -> str:
    try:
        from ctypes import windll, c_wchar_p, byref, c_uint, create_unicode_buffer
        size = windll.version.GetFileVersionInfoSizeW(c_wchar_p(filepath), None)
        if size == 0:
            return ""
        buf = create_unicode_buffer(size)
        if not windll.version.GetFileVersionInfoW(c_wchar_p(filepath), None, size, buf):
            return ""
        lang_cp = c_uint()
        windll.version.VerQueryValueW(buf, c_wchar_p("\\VarFileInfo\\Translation"), byref(lang_cp), byref(c_uint()))
        if not lang_cp.value:
            return ""
        key = f"\\StringFileInfo\\{lang_cp.value:08X}\\FileVersion"
        ver_ptr = c_wchar_p()
        ver_len = c_uint()
        if windll.version.VerQueryValueW(buf, c_wchar_p(key), byref(ver_ptr), byref(ver_len)):
            return ver_ptr.value or ""
        return ""
    except Exception:
        return ""


def execute(params: dict) -> dict:
    app_name = params.get("app_name", "")
    if not app_name:
        return _error("No app_name provided")

    processes = find_processes_by_name(app_name)
    running = len(processes) > 0

    exe_path = ""
    for p in processes:
        try:
            exe_path = p.exe()
            if exe_path:
                break
        except Exception:
            continue

    windows = find_windows_by_app_name(app_name)
    window_count = len(windows)

    version = ""
    publisher = ""
    install_location = ""

    if exe_path and os.path.isfile(exe_path):
        version = _get_file_version(exe_path)
        install_location = os.path.dirname(exe_path)
        try:
            from ctypes import windll, c_wchar_p, byref, c_uint, create_unicode_buffer
            size = windll.version.GetFileVersionInfoSizeW(c_wchar_p(exe_path), None)
            if size:
                buf = create_unicode_buffer(size)
                if windll.version.GetFileVersionInfoW(c_wchar_p(exe_path), None, size, buf):
                    lang_cp = c_uint()
                    windll.version.VerQueryValueW(buf, c_wchar_p("\\VarFileInfo\\Translation"), byref(lang_cp), byref(c_uint()))
                    if lang_cp.value:
                        key = f"\\StringFileInfo\\{lang_cp.value:08X}\\CompanyName"
                        ptr = c_wchar_p()
                        length = c_uint()
                        if windll.version.VerQueryValueW(buf, c_wchar_p(key), byref(ptr), byref(length)):
                            publisher = ptr.value or ""
        except Exception:
            pass

    data = {
        "name": app_name,
        "path": exe_path or "",
        "version": version or "Unknown",
        "publisher": publisher or "Unknown",
        "install_location": install_location or "",
        "running": running,
        "windows": window_count,
    }

    return {
        "success": True,
        "tool": "get_app_details",
        "app": app_name,
        "message": f"Details retrieved for {app_name}.",
        "data": data,
    }


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "get_app_details",
        "error": msg,
    }
