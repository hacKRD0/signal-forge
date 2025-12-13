"""Agent module for Google ADK-based discovery agent.

This module provides the core AI agent functionality for customer
and partner discovery using Google's Agent Development Kit.
"""

from .agent_setup import create_discovery_agent
from .discovery_agent import DiscoveryAgent

__all__ = ['create_discovery_agent', 'DiscoveryAgent']
