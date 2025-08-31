"""
Browser manager package.

Public API:
- BrowserManager: Facade to configure, create, use, and close Selenium WebDriver.

Existing imports like `from core.browser_manager import BrowserManager` continue to work
because this package exposes BrowserManager at the top level.
"""

from .service import BrowserManager

__all__ = ["BrowserManager"]

