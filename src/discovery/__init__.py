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

# CustomerDiscovery will be imported after it's created
try:
    from .customer_discovery import CustomerDiscovery
    __all__.append("CustomerDiscovery")
except ImportError:
    pass

# PartnerDiscovery will be imported after it's created
try:
    from .partner_discovery import PartnerDiscovery
    __all__.append("PartnerDiscovery")
except ImportError:
    pass
