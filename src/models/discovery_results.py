"""Discovery result data models for customer and partner discovery.

This module provides dataclasses for storing structured discovery results,
including company information and discovery metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .match_score import MatchScore
from .rationale import Rationale


@dataclass
class CompanyInfo:
    """Structured information about a discovered company.

    Attributes:
        name: Company name
        website: Company website URL
        locations: List of locations where the company operates
        size_estimate: Company size estimate (Small/Medium/Large)
        description: Brief description from search results
        sources: List of source URLs where information was found
    """

    name: str
    website: str
    locations: List[str] = field(default_factory=list)
    size_estimate: str = "Unknown"
    description: str = ""
    sources: List[str] = field(default_factory=list)
    match_score: Optional[MatchScore] = None
    rationale: Optional[Rationale] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert CompanyInfo to dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation of the company info
        """
        result = {
            "name": self.name,
            "website": self.website,
            "locations": self.locations,
            "size_estimate": self.size_estimate,
            "description": self.description,
            "sources": self.sources,
        }

        # Add optional scoring fields if present
        if self.match_score is not None:
            result["match_score"] = self.match_score.to_dict()

        if self.rationale is not None:
            result["rationale"] = self.rationale.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompanyInfo":
        """Create CompanyInfo from dictionary.

        Args:
            data: Dictionary containing company information

        Returns:
            CompanyInfo: New CompanyInfo instance
        """
        # Parse optional scoring fields
        match_score = None
        if "match_score" in data and data["match_score"]:
            match_score = MatchScore.from_dict(data["match_score"])

        rationale = None
        if "rationale" in data and data["rationale"]:
            rationale = Rationale.from_dict(data["rationale"])

        return cls(
            name=data.get("name", ""),
            website=data.get("website", ""),
            locations=data.get("locations", []),
            size_estimate=data.get("size_estimate", "Unknown"),
            description=data.get("description", ""),
            sources=data.get("sources", []),
            match_score=match_score,
            rationale=rationale,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on name and website for deduplication.

        Args:
            other: Another CompanyInfo instance

        Returns:
            bool: True if companies match by name or website
        """
        if not isinstance(other, CompanyInfo):
            return False
        # Match by name (case-insensitive) or website
        return (
            self.name.lower() == other.name.lower()
            or self.website.lower() == other.website.lower()
        )

    def __hash__(self) -> int:
        """Hash based on lowercase name for set operations.

        Returns:
            int: Hash value
        """
        return hash(self.name.lower())


@dataclass
class DiscoveryResult:
    """Complete discovery result with metadata.

    Attributes:
        entity_type: Type of entity discovered ("customer" or "partner")
        companies: List of discovered companies
        query_used: The search query that produced these results
        timestamp: When the discovery was performed
        scored: Whether scoring has been applied to the results
        avg_score: Average match score across all companies
    """

    entity_type: str
    companies: List[CompanyInfo] = field(default_factory=list)
    query_used: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    scored: bool = False
    avg_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert DiscoveryResult to dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation of the discovery result
        """
        return {
            "entity_type": self.entity_type,
            "companies": [company.to_dict() for company in self.companies],
            "query_used": self.query_used,
            "timestamp": self.timestamp.isoformat(),
            "scored": self.scored,
            "avg_score": self.avg_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscoveryResult":
        """Create DiscoveryResult from dictionary.

        Args:
            data: Dictionary containing discovery result data

        Returns:
            DiscoveryResult: New DiscoveryResult instance
        """
        # Parse companies
        companies = [
            CompanyInfo.from_dict(c) for c in data.get("companies", [])
        ]

        # Parse timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()

        return cls(
            entity_type=data.get("entity_type", ""),
            companies=companies,
            query_used=data.get("query_used", ""),
            timestamp=timestamp,
            scored=data.get("scored", False),
            avg_score=data.get("avg_score", 0.0),
        )

    def add_company(self, company: CompanyInfo) -> None:
        """Add a company to the result, avoiding duplicates.

        Args:
            company: CompanyInfo instance to add
        """
        # Check if company already exists
        if company not in self.companies:
            self.companies.append(company)

    def deduplicate_companies(self) -> None:
        """Remove duplicate companies from the result."""
        seen = set()
        unique_companies = []

        for company in self.companies:
            # Use name and website for deduplication
            key = (company.name.lower(), company.website.lower())
            if key not in seen:
                seen.add(key)
                unique_companies.append(company)

        self.companies = unique_companies

    def __len__(self) -> int:
        """Return the number of companies in the result.

        Returns:
            int: Number of companies
        """
        return len(self.companies)
