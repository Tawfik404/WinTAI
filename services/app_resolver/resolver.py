import logging
import os
import re

from services.app_resolver.patterns import (
    KNOWN_EXECUTABLES,
    SEARCH_PATHS,
    SKIP_EXE_KEYWORDS,
)

logger = logging.getLogger(__name__)


class AppResolver:
    def resolve(self, path: str, app_name: str = "") -> str | None:
        if not path:
            return self._fallback_search(app_name)

        if os.path.isfile(path) and path.lower().endswith(".exe"):
            return path

        if path.lower().endswith(".lnk") and os.path.isfile(path):
            resolved = self._resolve_lnk(path)
            if resolved:
                return resolved

        return self._resolve_directory(path, app_name)

    def _resolve_directory(self, directory: str, app_name: str) -> str | None:
        if not os.path.isdir(directory):
            return self._fallback_search(app_name)

        candidates: list[tuple[str, int, int]] = []
        app_key = self._normalize(app_name)

        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if not fname.lower().endswith(".exe"):
                    continue

                fp = os.path.join(root, fname)
                if not os.path.isfile(fp):
                    continue

                exe_key = self._normalize(fname)
                if any(kw in exe_key for kw in SKIP_EXE_KEYWORDS):
                    continue

                priority = self._score_exe(exe_key, app_key, fname, fp)
                size = os.path.getsize(fp)
                candidates.append((fp, priority, size))

        if not candidates:
            return self._fallback_search(app_name)

        candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
        best = candidates[0][0]
        logger.info("Resolved '%s' -> %s (from %d candidates)", app_name or directory, best, len(candidates))
        return best

    def _score_exe(self, exe_key: str, app_key: str, fname: str, fp: str) -> int:
        score = 0

        if app_key and (exe_key == app_key or exe_key.startswith(app_key)):
            score += 100

        if app_key and app_key in exe_key:
            score += 50

        for known_name, known_exe in KNOWN_EXECUTABLES.items():
            known_key = self._normalize(known_name)
            if app_key and (known_key == app_key or app_key in known_key):
                if fname.lower() == known_exe.lower():
                    score += 200
                    break
                if known_key in exe_key:
                    score += 100
                    break

        main_exe = os.path.splitext(os.path.basename(fp))[0].lower()
        folder_name = os.path.basename(os.path.dirname(fp)).lower()
        if main_exe == folder_name:
            score += 80

        score += len(fname) * 2

        return score

    def _fallback_search(self, app_name: str) -> str | None:
        if not app_name:
            return None

        app_key = self._normalize(app_name)
        if not app_key:
            return None

        known_name = self._match_known(app_key)
        if known_name:
            known_exe = KNOWN_EXECUTABLES[known_name]
            found = self._find_exe_in_search_paths(known_exe)
            if found:
                logger.info("Fallback: found known exe '%s' for '%s'", found, app_name)
                return found

        found = self._find_exe_in_search_paths(f"{app_key}.exe")
        if found:
            return found

        logger.info("Fallback search failed for '%s'", app_name)
        return None

    def _find_exe_in_search_paths(self, exe_name: str) -> str | None:
        exe_lower = exe_name.lower()
        for raw in SEARCH_PATHS:
            base = os.path.expandvars(os.path.expanduser(raw))
            if not os.path.isdir(base):
                continue

            for entry in os.listdir(base):
                fp = os.path.join(base, entry)
                if os.path.isfile(fp) and fp.lower().endswith(exe_lower):
                    return fp

            for vendor in os.listdir(base):
                vendor_path = os.path.join(base, vendor)
                if not os.path.isdir(vendor_path):
                    continue
                try:
                    for sub in os.listdir(vendor_path):
                        fp2 = os.path.join(vendor_path, sub)
                        if os.path.isfile(fp2) and fp2.lower().endswith(exe_lower):
                            return fp2
                        if os.path.isdir(fp2):
                            try:
                                for sub2 in os.listdir(fp2):
                                    fp3 = os.path.join(fp2, sub2)
                                    if os.path.isfile(fp3) and fp3.lower().endswith(exe_lower):
                                        return fp3
                            except PermissionError:
                                continue
                except PermissionError:
                    continue
        return None

    def _match_known(self, app_key: str) -> str | None:
        best_match = None
        best_len = 0
        for known_name in KNOWN_EXECUTABLES:
            known_key = self._normalize(known_name)
            if known_key == app_key:
                return known_name
            if known_key in app_key and len(known_key) > best_len:
                best_match = known_name
                best_len = len(known_key)
            if app_key in known_key and len(known_key) > best_len:
                best_match = known_name
                best_len = len(known_key)
        return best_match

    def _resolve_lnk(self, path: str) -> str | None:
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(path)
            target = shortcut.TargetPath
            if target and os.path.isfile(target) and target.lower().endswith(".exe"):
                return target
        except ImportError:
            pass
        except Exception:
            logger.debug("Failed to resolve .lnk: %s", path, exc_info=True)
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\.(exe|lnk|appref-ms)$', "", text, flags=re.IGNORECASE)
        text = re.sub(r'[^a-z0-9]', "", text.lower())
        return text.strip()
