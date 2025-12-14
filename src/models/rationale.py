"""Rationale data model for explaining match scores.

This module defines the Rationale dataclass for representing structured
explanations of why a discovered company is a good customer or partner match.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Rationale:
    """Structured explanation for why a company is a good match.

    This dataclass holds comprehensive rationale information that explains
    match scores in human-readable terms, helping stakeholders understand
    why each discovered entity is recommended.

    Attributes:
        summary: One-sentence summary of why this is a good match
        key_strengths: 3-5 bullet points highlighting why the match is strong
        fit_explanation: Detailed explanation of fit based on score components
        potential_concerns: 1-2 potential challenges or gaps, if any
        recommendation: Overall recommendation (Strong Match/Good Match/Fair Match)

    Recommendation Levels:
        - Strong Match (>= 80): Highly recommended, excellent fit
        - Good Match (>= 60): Recommended, solid fit with minor gaps
        - Fair Match (< 60): Consider with caution, significant gaps present

    Example:
        >>> rationale = Rationale(
        ...     summary="Excellent strategic fit with strong market alignment",
        ...     key_strengths=[
        ...         "Perfect geographic match in North America",
        ...         "Right size company for our target market",
        ...         "Strong relevance to our product offerings"
        ...     ],
        ...     fit_explanation="This company scores 85/100 overall...",
        ...     potential_concerns=["Limited international presence"],
        ...     recommendation="Strong Match"
        ... )
        >>> print(rationale.recommendation)
        Strong Match
    """

    summary: str = ""
    key_strengths: List[str] = field(default_factory=list)
    fit_explanation: str = ""
    potential_concerns: List[str] = field(default_factory=list)
    recommendation: str = "Fair Match"

    def __post_init__(self):
        """Validate rationale after initialization."""
        # Validate recommendation level
        valid_recommendations = ["Strong Match", "Good Match", "Fair Match"]
        if self.recommendation not in valid_recommendations:
            self.recommendation = "Fair Match"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Rationale to a dictionary for serialization.

        Returns:
            dict: Dictionary representation with all rationale fields.

        Example:
            >>> rationale = Rationale(summary="Excellent fit", recommendation="Strong Match")
            >>> data = rationale.to_dict()
            >>> print(data['recommendation'])
            Strong Match
        """
        return {
            "summary": self.summary,
            "key_strengths": self.key_strengths.copy(),
            "fit_explanation": self.fit_explanation,
            "potential_concerns": self.potential_concerns.copy(),
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rationale":
        """Create a Rationale instance from a dictionary.

        This method handles missing fields gracefully by using default values
        for any fields not present in the input dictionary.

        Args:
            data: Dictionary containing rationale fields.

        Returns:
            Rationale: A new Rationale instance.

        Example:
            >>> data = {
            ...     "summary": "Great match",
            ...     "key_strengths": ["High relevance", "Good location"],
            ...     "recommendation": "Strong Match"
            ... }
            >>> rationale = Rationale.from_dict(data)
            >>> print(rationale.summary)
            Great match
        """
        return cls(
            summary=data.get("summary", ""),
            key_strengths=data.get("key_strengths", []),
            fit_explanation=data.get("fit_explanation", ""),
            potential_concerns=data.get("potential_concerns", []),
            recommendation=data.get("recommendation", "Fair Match"),
        )
