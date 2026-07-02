import logging

logger = logging.getLogger(__name__)


def execute(params: dict) -> dict:
    text = params.get("text", "")
    if not text:
        return {
            "success": False,
            "tool": "set_clipboard",
            "error": "No text provided to copy to clipboard",
        }

    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
        except Exception as e:
            return {
                "success": False,
                "tool": "set_clipboard",
                "error": f"Clipboard write failed: {e}",
            }
    except Exception as e:
        return {
            "success": False,
            "tool": "set_clipboard",
            "error": f"Clipboard write failed: {e}",
        }

    logger.info("Clipboard set (%d chars)", len(text))
    return {
        "success": True,
        "tool": "set_clipboard",
        "params": {"text": text},
        "message": f"Copied {len(text)} characters to clipboard",
        "error": None,
    }
