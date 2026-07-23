"""
Media manager package exposing high-level helpers for preparing media files.

Public API remains stable: from .media_manager import prepare_media_paths, download_media
"""

from .service import prepare_media_paths, download_media

__all__ = ["prepare_media_paths", "download_media"]

