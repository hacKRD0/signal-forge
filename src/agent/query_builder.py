"""Query formulation logic for customer and partner discovery.

This module provides the QueryBuilder class for generating targeted search queries
based on business context and optional filters.
"""

import logging
from typing import List, Dict, Optional, Any

from ..models.business_context import BusinessContext


logger = logging.getLogger(__name__)


class QueryBuilder:
    """Build targeted search queries for customer and partner discovery.

    This class generates diverse, optimized search queries based on business
    context and user filters. It creates different query strategies for finding
    customers vs. partners.

    Example:
        >>> from src.models.business_context import BusinessContext
        >>> builder = QueryBuilder()
        >>> context = BusinessContext(
        ...     industry="SaaS - Marketing Automation",
        ...     products_services=["Email platform", "Analytics"],
        ...     target_market="B2B - SMB marketing agencies",
        ...     geography=["North America"]
        ... )
        >>> queries = builder.build_customer_queries(context)
        >>> print(len(queries))
        5
        >>> print(queries[0])
        'SMB marketing agencies in North America'
    """

    def build_customer_queries(
        self, context: BusinessContext, filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate diverse search queries to find potential customers.

        Creates 3-5 targeted queries based on the business context, focusing on
        finding companies that would benefit from the products/services offered.

        Args:
            context: BusinessContext with company information
            filters: Optional filters to narrow the search:
                - geography: str or list of geographic regions
                - industry: str or list of industries to target
                - size: Company size range (e.g., "50-200 employees")

        Returns:
            list: 3-5 diverse search query strings

        Example:
            >>> builder = QueryBuilder()
            >>> context = BusinessContext(
            ...     industry="SaaS - Marketing Automation",
            ...     target_market="B2B - SMB marketing agencies"
            ... )
            >>> queries = builder.build_customer_queries(context)
            >>> print(queries[0])
            'SMB marketing agencies needing marketing automation'
        """
        if filters is None:
            filters = {}

        queries = []
        seen_queries = set()  # Prevent duplicates

        # Extract key info from context
        industry = context.industry or "businesses"
        products = context.products_services or []
        target_market = context.target_market or ""
        geography = self._extract_geography(context, filters)

        # Strategy 1: Target market focused
        if target_market:
            query = self._build_query(target_market, geography)
            if query and query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Strategy 2: Industry + need for products/services
        if products:
            for product in products[:2]:  # Limit to top 2 products
                query = self._build_query(
                    f"{target_market or 'companies'} needing {product.lower()}",
                    geography
                )
                if query and query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)

        # Strategy 3: Industry-based search
        if industry:
            filter_industry = filters.get("industry")
            if filter_industry:
                # Use filter industry if provided
                industries = (
                    [filter_industry] if isinstance(filter_industry, str)
                    else filter_industry
                )
                for ind in industries[:2]:
                    query = self._build_query(f"{ind} companies", geography)
                    if query and query not in seen_queries:
                        queries.append(query)
                        seen_queries.add(query)
            else:
                # Extract base industry
                base_industry = industry.split("-")[0].strip()
                query = self._build_query(f"{base_industry} companies", geography)
                if query and query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)

        # Strategy 4: Geography + industry combination
        if geography and industry:
            base_industry = industry.split("-")[0].strip()
            query = f"{base_industry} businesses in {geography}"
            if query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Strategy 5: Size-based if filter provided
        size_filter = filters.get("size")
        if size_filter and target_market:
            query = self._build_query(
                f"{target_market} {size_filter}",
                geography
            )
            if query and query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Ensure we return 3-5 queries (optimal balance)
        while len(queries) < 3:
            # Add generic fallbacks
            if len(queries) == 0:
                fallback = self._build_query(
                    target_market or industry or "businesses",
                    geography
                )
            elif len(queries) == 1:
                fallback = f"{industry or 'companies'} looking for growth"
            elif len(queries) == 2:
                fallback = f"potential {industry or 'business'} customers"

            if fallback and fallback not in seen_queries:
                queries.append(fallback)
                seen_queries.add(fallback)
            else:
                # If fallback is duplicate, create a more generic one
                queries.append(f"businesses in {geography}" if geography else "companies")
                break

        logger.info(f"Generated {len(queries)} customer search queries")
        return queries[:5]  # Cap at 5 queries

    def build_partner_queries(
        self, context: BusinessContext, filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate diverse search queries to find potential partners.

        Creates 3-5 targeted queries based on the business context, focusing on
        finding complementary businesses and integration opportunities.

        Args:
            context: BusinessContext with company information
            filters: Optional filters to narrow the search:
                - geography: str or list of geographic regions
                - industry: str or list of industries to target
                - partnership_type: Type of partnership (e.g., "technology", "distribution")

        Returns:
            list: 3-5 diverse search query strings

        Example:
            >>> builder = QueryBuilder()
            >>> context = BusinessContext(
            ...     industry="SaaS - Marketing Automation",
            ...     products_services=["Email platform"]
            ... )
            >>> queries = builder.build_partner_queries(context)
            >>> print(queries[0])
            'companies partnering with SaaS businesses'
        """
        if filters is None:
            filters = {}

        queries = []
        seen_queries = set()

        # Extract key info
        industry = context.industry or "businesses"
        products = context.products_services or []
        geography = self._extract_geography(context, filters)

        # Strategy 1: Partnership with industry
        if industry:
            base_industry = industry.split("-")[0].strip()
            query = self._build_query(
                f"companies partnering with {base_industry} businesses",
                geography
            )
            if query and query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Strategy 2: Complementary services/products
        if products:
            # Look for complementary products
            for product in products[:2]:
                query = self._build_query(
                    f"companies integrating with {product.lower()}",
                    geography
                )
                if query and query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)

        # Strategy 3: Technology partnerships (if SaaS/tech company)
        if "saas" in industry.lower() or "software" in industry.lower():
            query = self._build_query(
                "technology integration partners",
                geography
            )
            if query and query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Strategy 4: Filter-based partnership type
        partnership_type = filters.get("partnership_type")
        if partnership_type:
            query = self._build_query(
                f"{partnership_type} partnership opportunities",
                geography
            )
            if query and query not in seen_queries:
                queries.append(query)
                seen_queries.add(query)

        # Strategy 5: Industry-specific complementary businesses
        filter_industry = filters.get("industry")
        if filter_industry:
            industries = (
                [filter_industry] if isinstance(filter_industry, str)
                else filter_industry
            )
            for ind in industries[:2]:
                query = self._build_query(
                    f"{ind} strategic partners",
                    geography
                )
                if query and query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)

        # Ensure we return 3-5 queries
        while len(queries) < 3:
            # Add generic fallbacks
            if len(queries) == 0:
                fallback = self._build_query(
                    f"{industry.split('-')[0].strip() if industry else 'business'} partners",
                    geography
                )
            elif len(queries) == 1:
                fallback = f"strategic {industry or 'business'} partnerships"
            elif len(queries) == 2:
                fallback = f"complementary {industry or 'business'} partners"

            if fallback and fallback not in seen_queries:
                queries.append(fallback)
                seen_queries.add(fallback)
            else:
                # If fallback is duplicate, create a more generic one
                queries.append(f"partnership opportunities in {geography}" if geography else "business partners")
                break

        logger.info(f"Generated {len(queries)} partner search queries")
        return queries[:5]  # Cap at 5 queries

    def refine_query(self, base_query: str, filters: Dict[str, Any]) -> str:
        """Add filter constraints to a base query.

        Args:
            base_query: The base search query string
            filters: Dictionary of filters to apply:
                - geography: str or list of geographic regions
                - industry: str or list of industries

        Returns:
            str: Refined query with filters applied

        Example:
            >>> builder = QueryBuilder()
            >>> query = builder.refine_query(
            ...     "marketing agencies",
            ...     {"geography": "North America"}
            ... )
            >>> print(query)
            'marketing agencies in North America'
        """
        if not filters:
            return base_query

        refined = base_query

        # Add geography filter
        geography = filters.get("geography")
        if geography:
            geo_str = geography if isinstance(geography, str) else ", ".join(geography[:2])
            if "in " not in refined.lower():
                refined = f"{refined} in {geo_str}"

        # Add industry filter if not already in query
        industry = filters.get("industry")
        if industry and industry.lower() not in refined.lower():
            industry_str = industry if isinstance(industry, str) else industry[0]
            refined = f"{industry_str} {refined}"

        logger.debug(f"Refined query: '{base_query}' -> '{refined}'")
        return refined

    def _build_query(self, base: str, geography: Optional[str] = None) -> str:
        """Build a query string from base and optional geography.

        Args:
            base: Base query text
            geography: Optional geography string

        Returns:
            str: Formatted query string
        """
        if not base:
            return ""

        query = base.strip()

        if geography and "in " not in query.lower():
            query = f"{query} in {geography}"

        return query

    def _extract_geography(
        self, context: BusinessContext, filters: Dict[str, Any]
    ) -> Optional[str]:
        """Extract geography from context or filters.

        Args:
            context: BusinessContext instance
            filters: Filter dictionary

        Returns:
            str or None: Geography string for queries
        """
        # Priority 1: Filter geography
        if filters.get("geography"):
            geo = filters["geography"]
            if isinstance(geo, list):
                return ", ".join(geo[:2])  # Limit to 2 regions
            return geo

        # Priority 2: Context geography
        if context.geography:
            return ", ".join(context.geography[:2])  # Limit to 2 regions

        return None
