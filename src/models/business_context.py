"""Business context data model.

This module defines the BusinessContext dataclass for representing structured
business information extracted from documents.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List


@dataclass
class BusinessContext:
    """Structured representation of business information.

    This dataclass holds business context information extracted from documents,
    including company details, industry, products/services, target market,
    geography, and key strengths.

    Attributes:
        company_name: Name of the company or organization
        industry: Primary industry or sector (e.g., "SaaS", "Manufacturing")
        products_services: List of main products or services offered
        target_market: Description of who they sell to (B2B, B2C, specific industries)
        geography: List of regions where they operate (countries, regions, cities)
        key_strengths: List of key differentiators or unique selling points
        additional_notes: Any additional relevant information

    Example:
        >>> context = BusinessContext(
        ...     company_name="Acme Corp",
        ...     industry="SaaS - Marketing Automation",
        ...     products_services=["Email platform", "Analytics"],
        ...     target_market="B2B - SMB marketing agencies",
        ...     geography=["North America", "Europe"],
        ...     key_strengths=["AI-powered optimization"],
        ...     additional_notes="Series A funded"
        ... )
        >>> print(context.to_dict())
    """

    company_name: str = ""
    industry: str = ""
    products_services: List[str] = field(default_factory=list)
    target_market: str = ""
    geography: List[str] = field(default_factory=list)
    key_strengths: List[str] = field(default_factory=list)
    additional_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the BusinessContext to a dictionary.

        Returns:
            dict: Dictionary representation of the business context with all fields.

        Example:
            >>> context = BusinessContext(company_name="Acme Corp")
            >>> data = context.to_dict()
            >>> print(data['company_name'])
            'Acme Corp'
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessContext":
        """Create a BusinessContext instance from a dictionary.

        This method handles missing fields gracefully by using default values
        for any fields not present in the input dictionary.

        Args:
            data: Dictionary containing business context fields.

        Returns:
            BusinessContext: A new BusinessContext instance.

        Example:
            >>> data = {"company_name": "Acme Corp", "industry": "SaaS"}
            >>> context = BusinessContext.from_dict(data)
            >>> print(context.company_name)
            'Acme Corp'
        """
        # Extract only the fields that are defined in the dataclass
        valid_fields = {
            "company_name",
            "industry",
            "products_services",
            "target_market",
            "geography",
            "key_strengths",
            "additional_notes",
        }

        # Filter data to only include valid fields
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        # Create instance with filtered data
        return cls(**filtered_data)

    def to_prompt_string(self) -> str:
        """Convert the BusinessContext to a human-readable string for prompts.

        Returns:
            str: A formatted, human-readable string representation suitable for
                including in agent prompts.

        Example:
            >>> context = BusinessContext(
            ...     company_name="Acme Corp",
            ...     industry="SaaS"
            ... )
            >>> print(context.to_prompt_string())
            Company: Acme Corp
            Industry: SaaS
            ...
        """
        lines = []

        if self.company_name:
            lines.append(f"Company: {self.company_name}")

        if self.industry:
            lines.append(f"Industry: {self.industry}")

        if self.products_services:
            products_str = ", ".join(self.products_services)
            lines.append(f"Products/Services: {products_str}")

        if self.target_market:
            lines.append(f"Target Market: {self.target_market}")

        if self.geography:
            geography_str = ", ".join(self.geography)
            lines.append(f"Geography: {geography_str}")

        if self.key_strengths:
            strengths_str = ", ".join(self.key_strengths)
            lines.append(f"Key Strengths: {strengths_str}")

        if self.additional_notes:
            lines.append(f"Additional Notes: {self.additional_notes}")

        return "\n".join(lines) if lines else "No business context available"
