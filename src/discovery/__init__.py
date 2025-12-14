"""Discovery package for web search and result parsing.

This package provides tools for discovering potential customers and partners
through web search and structured result parsing.
"""

from .search_parser import SearchResultParser

__all__ = ["SearchResultParser"]

# WebSearchEngine will be imported after it's created
try:
    from .web_search import WebSearchEngine
    __all__.append("WebSearchEngine")
except ImportError:
    pass
