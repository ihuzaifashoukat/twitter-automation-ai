"""
Analyzer package exposing TweetAnalyzer while organizing internals.

Public API remains stable: `from xuse.features.analyzer import TweetAnalyzer`.
"""

from .service import TweetAnalyzer

__all__ = ["TweetAnalyzer"]

