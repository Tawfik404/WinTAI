import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    try:
        import pyperclip
        text = pyperclip.paste()
    except ImportError:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
        except Exception:
            text = ""
    except Exception:
        text = ""

    logger.info("Clipboard retrieved (%d chars)", len(text))
    return {
        "success": True,
        "tool": "get_clipboard",
        "params": {},
        "message": text if text else "Clipboard is empty",
        "data": {"text": text, "length": len(text)},
        "error": None,
    }
