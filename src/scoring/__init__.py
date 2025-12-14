"""Scoring package for customer and partner discovery.

This package provides scoring algorithms for evaluating how well discovered
customers and partners match the business context.
"""

from .match_scorer import MatchScorer

__all__ = ["MatchScorer"]
