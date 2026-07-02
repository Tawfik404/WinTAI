import re
import webbrowser
import logging

logger = logging.getLogger(__name__)

_VALID_URL_RE = re.compile(
    r"^https?://"  # http:// or https://
    r"[^\s/$.?#]"  # first char of domain
    r"[^\s]*$",  # rest of URL
    re.IGNORECASE,
)


def execute(params: dict) -> dict:
    url = params.get("url", "").strip()
    if not url:
        return _error("No URL provided")

    if not _VALID_URL_RE.match(url):
        return _error(f"Invalid or unsafe URL: {url}")

    try:
        webbrowser.open(url, new=2)
        logger.info("Opened URL: %s", url)
        return {
            "success": True,
            "tool": "open_url",
            "params": {"url": url},
            "message": f"Opened {url}",
            "error": None,
        }
    except Exception as e:
        logger.error("Failed to open URL %s: %s", url, e)
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "success": False,
        "tool": "open_url",
        "error": msg,
    }
