"""
Scraper package exposing TweetScraper while organizing internals.

Public API remains stable: `from features.scraper import TweetScraper`.
"""

from .service import TweetScraper

__all__ = ["TweetScraper"]

