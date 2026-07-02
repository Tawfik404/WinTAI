import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.app_scanner.models import App, ScanResult
from services.app_scanner.normalize import deduplicate
from services.app_scanner.sources import start_menu, registry, desktop, appx, program_files

logger = logging.getLogger(__name__)


class AppScanner:
    def __init__(self, max_workers: int = 4) -> None:
        self._max_workers = max_workers
        self._scanners: dict[str, callable] = {
            "start_menu": start_menu.scan,
            "registry": registry.scan,
            "desktop": desktop.scan,
            "appx": appx.scan,
            "program_files": program_files.scan,
        }

    def scan_all(self) -> list[App]:
        all_apps: list[App] = []
        results: list[ScanResult] = []
        start = time.perf_counter()

        logger.info(
            "Starting parallel app scan (%d scanners, %d workers)...",
            len(self._scanners),
            self._max_workers,
        )

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(self._run_scanner, name, fn): name
                for name, fn in self._scanners.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    scan_result = future.result()
                    results.append(scan_result)
                    all_apps.extend(scan_result.apps)
                    logger.info(
                        "[%s] %d apps in %.2fs",
                        name,
                        len(scan_result.apps),
                        scan_result.elapsed,
                    )
                except Exception:
                    logger.error("[%s] scanner crashed", name, exc_info=True)

        total_time = time.perf_counter() - start
        before_dedup = len(all_apps)
        all_apps = deduplicate(all_apps)

        logger.info(
            "Scan complete: %d raw → %d unique in %.2fs (%.1f apps/s)",
            before_dedup,
            len(all_apps),
            total_time,
            before_dedup / total_time if total_time > 0 else 0,
        )

        return all_apps

    @staticmethod
    def _run_scanner(name: str, scan_fn: callable) -> ScanResult:
        t0 = time.perf_counter()
        try:
            apps = scan_fn()
        except Exception:
            logger.error("[%s] scanner raised", name, exc_info=True)
            apps = []
        elapsed = time.perf_counter() - t0
        return ScanResult(apps=apps, source=name, elapsed=elapsed)
