import os
import logging
import asyncio
from typing import List, Optional

from data_models import TweetContent

from .downloader import download_with_retries
try:
    from core.browser_manager import BrowserManager  # type: ignore
except Exception:  # pragma: no cover
    BrowserManager = None  # type: ignore

logger = logging.getLogger(__name__)


async def download_media(media_url: str, media_dir: str, browser_manager: Optional["BrowserManager"] = None) -> Optional[str]:
    """Download a single media URL to `media_dir`.

    Notes
    - Uses a resilient downloader with retries and basic content-type validation.
    - Async signature for compatibility; internally uses blocking I/O.
    """
    return await asyncio.to_thread(download_with_retries, media_url, media_dir, 30, 2, browser_manager)


async def prepare_media_paths(content: TweetContent, media_dir: str, browser_manager: Optional["BrowserManager"] = None) -> List[str]:
    """Return absolute file paths for media to attach.

    - Starts with any existing `local_media_paths` from `content`.
    - Downloads each URL in `content.media_urls` into `media_dir`.
    - Filters out any non-existent paths and normalizes to absolute paths.
    """
    final_media_paths: List[str] = list(content.local_media_paths or [])
    if content.media_urls:
        # Kick off parallel downloads (bounded by event loop/thread pool defaults)
        tasks = [
            download_media(str(url), media_dir, browser_manager)
            for url in content.media_urls
        ]
        for downloaded_path in await asyncio.gather(*tasks, return_exceptions=False):
            if downloaded_path:
                final_media_paths.append(downloaded_path)
    final_media_paths = [os.path.abspath(p) for p in final_media_paths if p and os.path.exists(p)]
    return final_media_paths
