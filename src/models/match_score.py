"""Match score data model for customer and partner discovery.

This module defines the MatchScore dataclass for representing multi-dimensional
match scores with component breakdowns and confidence levels.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class MatchScore:
    """Multi-dimensional match score for discovered companies.

    This dataclass holds comprehensive scoring information that evaluates how well
    a discovered customer or partner matches the business context. Scores are
    normalized to 0-100 range for consistency.

    Attributes:
        overall_score: Weighted average of all component scores (0-100)
        relevance_score: How relevant the company is to the business (0-100)
        geographic_fit: Location alignment with target geography (0-100)
        size_appropriateness: Company size fit with target market (0-100)
        strategic_alignment: Strategic fit and complementary capabilities (0-100)
        score_breakdown: Dictionary of component scores for transparency
        confidence: Confidence level in the score (High/Medium/Low) based on data availability

    Scoring Components:
        - relevance_score (40% weight): AI-powered assessment of business relevance
        - geographic_fit (20% weight): Geographic proximity and market overlap
        - size_appropriateness (20% weight): Company size alignment with target market
        - strategic_alignment (20% weight): Strategic fit and capability complementarity

    Confidence Levels:
        - High: Complete data available for all scoring dimensions
        - Medium: Some data missing but core dimensions covered
        - Low: Limited data available, scores based on partial information

    Example:
        >>> score = MatchScore(
        ...     overall_score=85.0,
        ...     relevance_score=90.0,
        ...     geographic_fit=80.0,
        ...     size_appropriateness=85.0,
        ...     strategic_alignment=85.0,
        ...     score_breakdown={
        ...         "relevance": 90.0,
        ...         "geographic": 80.0,
        ...         "size": 85.0,
        ...         "strategic": 85.0
        ...     },
        ...     confidence="High"
        ... )
        >>> print(f"Overall match: {score.overall_score}%")
        Overall match: 85.0%
    """

    overall_score: float = 0.0
    relevance_score: float = 0.0
    geographic_fit: float = 0.0
    size_appropriateness: float = 0.0
    strategic_alignment: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    confidence: str = "Low"

    def __post_init__(self):
        """Validate score ranges after initialization."""
        # Ensure all scores are within 0-100 range
        self.overall_score = max(0.0, min(100.0, self.overall_score))
        self.relevance_score = max(0.0, min(100.0, self.relevance_score))
        self.geographic_fit = max(0.0, min(100.0, self.geographic_fit))
        self.size_appropriateness = max(0.0, min(100.0, self.size_appropriateness))
        self.strategic_alignment = max(0.0, min(100.0, self.strategic_alignment))

        # Validate confidence level
        valid_confidence_levels = ["High", "Medium", "Low"]
        if self.confidence not in valid_confidence_levels:
            self.confidence = "Low"

        # Populate score_breakdown if empty
        if not self.score_breakdown:
            self.score_breakdown = {
                "relevance": self.relevance_score,
                "geographic": self.geographic_fit,
                "size": self.size_appropriateness,
                "strategic": self.strategic_alignment,
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the MatchScore to a dictionary for serialization.

        Returns:
            dict: Dictionary representation with all score components and metadata.

        Example:
            >>> score = MatchScore(overall_score=85.0, confidence="High")
            >>> data = score.to_dict()
            >>> print(data['overall_score'])
            85.0
        """
        return {
            "overall_score": self.overall_score,
            "relevance_score": self.relevance_score,
            "geographic_fit": self.geographic_fit,
            "size_appropriateness": self.size_appropriateness,
            "strategic_alignment": self.strategic_alignment,
            "score_breakdown": self.score_breakdown.copy(),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchScore":
        """Create a MatchScore instance from a dictionary.

        This method handles missing fields gracefully by using default values
        for any fields not present in the input dictionary.

        Args:
            data: Dictionary containing match score fields.

        Returns:
            MatchScore: A new MatchScore instance.

        Example:
            >>> data = {
            ...     "overall_score": 85.0,
            ...     "relevance_score": 90.0,
            ...     "confidence": "High"
            ... }
            >>> score = MatchScore.from_dict(data)
            >>> print(score.overall_score)
            85.0
        """
        return cls(
            overall_score=data.get("overall_score", 0.0),
            relevance_score=data.get("relevance_score", 0.0),
            geographic_fit=data.get("geographic_fit", 0.0),
            size_appropriateness=data.get("size_appropriateness", 0.0),
            strategic_alignment=data.get("strategic_alignment", 0.0),
            score_breakdown=data.get("score_breakdown", {}),
            confidence=data.get("confidence", "Low"),
        )
