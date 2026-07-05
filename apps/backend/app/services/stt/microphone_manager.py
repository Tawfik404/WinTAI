import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_VAR_DIR = Path(__file__).resolve().parents[3] / "var"
_MICROPHONE_FILE = _VAR_DIR / "microphone.json"


class MicrophoneManager:
    def __init__(self):
        self._device_id: str = "default"
        self._load()

    def get_device_id(self) -> str:
        return self._device_id

    def set_device_id(self, device_id: str) -> None:
        self._device_id = device_id
        self._save()
        logger.info("Microphone changed: %s", device_id)

    def enumerate(self) -> list[dict]:
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice not installed")
            return [{"id": "default", "name": "System Default", "default": True}]

        devices = sd.query_devices()
        default_id = sd.default.device[0]

        result = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                result.append({
                    "id": str(i),
                    "name": dev["name"],
                    "default": i == default_id,
                })

        if not result:
            result.append({"id": "default", "name": "System Default", "default": True})

        logger.info("Microphones detected: %d", len(result))
        return result

    def _save(self) -> None:
        _VAR_DIR.mkdir(parents=True, exist_ok=True)
        try:
            _MICROPHONE_FILE.write_text(json.dumps({"deviceId": self._device_id}))
        except Exception as e:
            logger.error("Failed to save microphone setting: %s", e)

    def _load(self) -> None:
        try:
            if _MICROPHONE_FILE.exists():
                data = json.loads(_MICROPHONE_FILE.read_text())
                self._device_id = data.get("deviceId", "default")
                logger.info("Saved microphone restored: %s", self._device_id)
            else:
                logger.info("Default microphone selected")
        except Exception as e:
            logger.error("Failed to load microphone setting: %s", e)
