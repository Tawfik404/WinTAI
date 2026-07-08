import logging
import subprocess
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)

# ========== Win32 API via ctypes (stdlib, always available on Windows) ==========

try:
    _user32 = ctypes.windll.user32
except (AttributeError, OSError):
    _user32 = None

if _user32 is not None:
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    _user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    _user32.EnumWindows.restype = wintypes.BOOL

    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.IsWindowVisible.restype = wintypes.BOOL

    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int

    _user32.GetForegroundWindow.argtypes = []
    _user32.GetForegroundWindow.restype = wintypes.HWND

    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    _user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.ShowWindow.restype = wintypes.BOOL

    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.SetForegroundWindow.restype = wintypes.BOOL

    _user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_uint,
    ]
    _user32.SetWindowPos.restype = wintypes.BOOL

    _user32.IsIconic.argtypes = [wintypes.HWND]
    _user32.IsIconic.restype = wintypes.BOOL

    _user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    _user32.PostMessageW.restype = wintypes.BOOL

    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int

# ========== Win32 constants ==========
WM_CLOSE = 0x0010
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
HWND_TOP = 0
SWP_SHOWWINDOW = 0x0040
SM_CXSCREEN = 0
SM_CYSCREEN = 1

# ========== psutil fallback ==========

def _get_psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        return None

# ========== tasklist helpers ==========

def _tasklist_csv(*args: str) -> list[dict[str, str]]:
    try:
        cmd = ["tasklist", "/FO", "CSV", "/NH"] + list(args)
        out = subprocess.check_output(cmd, text=True, timeout=10)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return []
    rows: list[dict[str, str]] = []
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split('","')
        if len(parts) >= 2:
            name = parts[0].strip('"')
            try:
                pid = int(parts[1].strip('"'))
            except ValueError:
                continue
            rows.append({"name": name, "pid": str(pid)})
    return rows


def _get_process_path_by_pid_ctypes(pid: int) -> str | None:
    try:
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_process:
            return None
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)
            if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
                return buf.value
        finally:
            kernel32.CloseHandle(h_process)
    except Exception:
        pass
    return None

# ========== Process name matching ==========

def _process_name_matches(app_key: str, process_name: str) -> bool:
    proc_key = process_name.lower().replace(".exe", "").strip()
    if app_key in proc_key:
        return True
    if " " in app_key:
        for part in app_key.split():
            if len(part) > 2 and part in proc_key:
                return True
    return False


# ========== Process lookup ==========

def get_process_name_by_pid(pid: int) -> str | None:
    if psutil_mod := _get_psutil():
        try:
            return psutil_mod.Process(pid).name()
        except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
            return None
    rows = _tasklist_csv("/FI", f"PID eq {pid}")
    for r in rows:
        return r["name"]
    return None


def get_process_path_by_pid(pid: int) -> str | None:
    if psutil_mod := _get_psutil():
        try:
            return psutil_mod.Process(pid).exe()
        except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
            return None
    return _get_process_path_by_pid_ctypes(pid)


def find_processes_by_name(app_name: str) -> list:
    app_key = app_name.lower().replace(".exe", "")

    psutil_mod = _get_psutil()
    if psutil_mod:
        results: list = []
        for proc in psutil_mod.process_iter(["pid", "name", "exe"]):
            try:
                pname = proc.info["name"] or ""
                if _process_name_matches(app_key, pname):
                    results.append(proc)
            except (psutil_mod.NoSuchProcess, psutil_mod.AccessDenied):
                continue
        return results

    rows = _tasklist_csv()
    proxied: list = []
    seen_pids: set[int] = set()
    for r in rows:
        pid = int(r["pid"])
        if _process_name_matches(app_key, r["name"]):
            if pid not in seen_pids:
                seen_pids.add(pid)
                proxied.append(_TasklistProcess(r["name"], pid))
    return proxied


def find_process_by_name(app_name: str):
    procs = find_processes_by_name(app_name)
    if not procs:
        return None
    if len(procs) == 1:
        return procs[0]
    app_key = app_name.lower().replace(".exe", "")
    for p in procs:
        try:
            if p.name().lower().replace(".exe", "") == app_key:
                return p
        except Exception:
            continue
    return procs[0]

# ========== Window operations ==========

def _raw_is_window_visible(hwnd: int) -> bool:
    if _user32 is None:
        return False
    return bool(_user32.IsWindowVisible(hwnd))


def _raw_get_window_text(hwnd: int) -> str:
    if _user32 is None:
        return ""
    buf = ctypes.create_unicode_buffer(512)
    length = _user32.GetWindowTextW(hwnd, buf, 512)
    return buf[:length] if length else ""


def _raw_get_window_thread_process_id(hwnd: int) -> tuple[int, int]:
    if _user32 is None:
        return (0, 0)
    pid = wintypes.DWORD()
    tid = _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return (tid, pid.value)


def enum_windows() -> list[dict]:
    if _user32 is None:
        logger.warning("enum_windows unavailable: not on Windows")
        return []

    windows: list[dict] = []

    def _enum_callback(hwnd: int, _: int) -> bool:
        if not _raw_is_window_visible(hwnd):
            return True
        title = _raw_get_window_text(hwnd)
        if not title:
            return True
        _, pid = _raw_get_window_thread_process_id(hwnd)
        proc_name = get_process_name_by_pid(pid) or f"pid:{pid}"
        windows.append({
            "title": title,
            "process": proc_name,
            "handle": str(hwnd),
        })
        return True

    callback = WNDENUMPROC(_enum_callback)
    _user32.EnumWindows(callback, 0)
    return windows


def get_foreground_window_info() -> dict:
    if _user32 is None:
        return {"title": "", "process": "", "path": ""}

    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return {"title": "", "process": "", "path": ""}

    title = _raw_get_window_text(hwnd)
    _, pid = _raw_get_window_thread_process_id(hwnd)
    proc_name = get_process_name_by_pid(pid) or str(pid)
    proc_path = get_process_path_by_pid(pid) or ""

    return {
        "title": title,
        "process": proc_name,
        "path": proc_path,
    }


def find_windows_by_app_name(app_name: str) -> list[dict]:
    if _user32 is None:
        logger.warning("find_windows_by_app_name unavailable: not on Windows")
        return []

    app_name_lower = app_name.lower().replace(".exe", "")
    matches: list[dict] = []

    def _enum_callback(hwnd: int, _: int) -> bool:
        if not _raw_is_window_visible(hwnd):
            return True
        title = _raw_get_window_text(hwnd)
        if not title:
            return True
        _, pid = _raw_get_window_thread_process_id(hwnd)
        proc_name = get_process_name_by_pid(pid)
        if not proc_name:
            return True
        if _process_name_matches(app_name_lower, proc_name) or app_name_lower in title.lower():
            matches.append({
                "hwnd": hwnd,
                "title": title,
                "pid": pid,
                "process": proc_name,
            })
        return True

    callback = WNDENUMPROC(_enum_callback)
    _user32.EnumWindows(callback, 0)
    return matches


def find_window_by_app_name(app_name: str) -> dict | None:
    windows = find_windows_by_app_name(app_name)
    if not windows:
        return None
    return windows[0]


def activate_window(hwnd: int) -> bool:
    if _user32 is None:
        return False
    try:
        if _user32.IsIconic(hwnd):
            _user32.ShowWindow(hwnd, SW_RESTORE)
        _user32.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        logger.warning("Failed to activate window %d: %s", hwnd, e)
        return False


def show_window(hwnd: int, show_cmd: int) -> bool:
    if _user32 is None:
        return False
    try:
        _user32.ShowWindow(hwnd, show_cmd)
        return True
    except Exception as e:
        logger.warning("Failed to show window %d: %s", hwnd, e)
        return False


def close_window_by_hwnd(hwnd: int) -> bool:
    if _user32 is None:
        return False
    try:
        _user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return True
    except Exception as e:
        logger.warning("Failed to post WM_CLOSE to %d: %s", hwnd, e)
        return False


def get_app_name_from_path(path: str) -> str:
    if not path:
        return ""
    return path.split("\\")[-1].split("/")[-1].replace(".exe", "").replace(".lnk", "")


def get_screen_size() -> tuple[int, int]:
    if _user32 is None:
        return (0, 0)
    width = _user32.GetSystemMetrics(SM_CXSCREEN)
    height = _user32.GetSystemMetrics(SM_CYSCREEN)
    return width, height


def set_window_pos(hwnd: int, x: int, y: int, w: int, h: int) -> bool:
    if _user32 is None:
        return False
    try:
        _user32.SetWindowPos(hwnd, HWND_TOP, x, y, w, h, SWP_SHOWWINDOW)
        return True
    except Exception as e:
        logger.warning("Failed to set window pos %d: %s", hwnd, e)
        return False


def is_window_iconic(hwnd: int) -> bool:
    if _user32 is None:
        return False
    try:
        return bool(_user32.IsIconic(hwnd))
    except Exception:
        return False

# ========== Fallback process representation ==========

class _TasklistProcess:
    def __init__(self, name: str, pid: int):
        self._name = name
        self._pid = pid

    def name(self) -> str:
        return self._name

    def pid(self) -> int:
        return self._pid

    def exe(self) -> str | None:
        return _get_process_path_by_pid_ctypes(self._pid)

    def is_running(self) -> bool:
        rows = _tasklist_csv("/FI", f"PID eq {self._pid}")
        return len(rows) > 0

    def terminate(self) -> None:
        subprocess.run(["taskkill", "/im", self._name], timeout=10, capture_output=True)

    def kill(self) -> None:
        subprocess.run(["taskkill", "/f", "/im", self._name], timeout=10, capture_output=True)

    def __repr__(self) -> str:
        return f"_TasklistProcess({self._name}, pid={self._pid})"
