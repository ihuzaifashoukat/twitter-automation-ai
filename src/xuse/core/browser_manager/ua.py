import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from fake_headers import Headers
    FAKE_HEADERS_AVAILABLE = True
except Exception:
    Headers = None  # type: ignore
    FAKE_HEADERS_AVAILABLE = False


def get_user_agent(custom: Optional[str] = None) -> str:
    if custom and isinstance(custom, str):
        logger.debug(f"Using custom user agent: {custom}")
        return custom
    if FAKE_HEADERS_AVAILABLE:
        try:
            header = Headers(headers=True).generate()
            ua = header.get('User-Agent')
            if ua:
                logger.debug(f"Generated random user agent: {ua}")
                return ua
        except Exception as e:
            logger.warning(f"fake-headers UA generation failed: {e}")
    # Fallback reasonable UA
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

