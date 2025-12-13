"""Examples demonstrating query formulation for customer and partner discovery.

This script shows how the QueryBuilder generates targeted search queries based on
business context and optional filters.
"""

from src.agent.query_builder import QueryBuilder
from src.models.business_context import BusinessContext


def main():
    """Run query generation examples."""
    print("=" * 80)
    print("Query Formulation Examples")
    print("=" * 80)

    # Initialize the query builder
    builder = QueryBuilder()

    # Example 1: SaaS Marketing Automation Company
    print("\n" + "=" * 80)
    print("Example 1: SaaS Marketing Automation Company")
    print("=" * 80)

    saas_context = BusinessContext(
        company_name="CloudFlow",
        industry="SaaS - Marketing Automation",
        products_services=[
            "Email marketing platform",
            "Lead scoring tools",
            "Analytics dashboard"
        ],
        target_market="B2B - Small to medium-sized marketing agencies",
        geography=["North America", "Europe"],
        key_strengths=[
            "AI-powered optimization",
            "Easy integration with existing tools"
        ],
        additional_notes="Series A funded, 50-100 employees"
    )

    print("\nBusiness Context:")
    print(saas_context.to_prompt_string())

    print("\n" + "-" * 80)
    print("Customer Search Queries (No Filters):")
    print("-" * 80)
    customer_queries = builder.build_customer_queries(saas_context)
    for i, query in enumerate(customer_queries, 1):
        print(f"{i}. {query}")

    print("\n" + "-" * 80)
    print("Customer Search Queries (With Geography Filter):")
    print("-" * 80)
    customer_queries_filtered = builder.build_customer_queries(
        saas_context,
        filters={"geography": "California"}
    )
    for i, query in enumerate(customer_queries_filtered, 1):
        print(f"{i}. {query}")

    print("\n" + "-" * 80)
    print("Partner Search Queries (No Filters):")
    print("-" * 80)
    partner_queries = builder.build_partner_queries(saas_context)
    for i, query in enumerate(partner_queries, 1):
        print(f"{i}. {query}")

    print("\n" + "-" * 80)
    print("Partner Search Queries (With Partnership Type Filter):")
    print("-" * 80)
    partner_queries_filtered = builder.build_partner_queries(
        saas_context,
        filters={"partnership_type": "technology integration"}
    )
    for i, query in enumerate(partner_queries_filtered, 1):
        print(f"{i}. {query}")

    # Example 2: Manufacturing Company
    print("\n\n" + "=" * 80)
    print("Example 2: Manufacturing Company")
    print("=" * 80)

    manufacturing_context = BusinessContext(
        company_name="PrecisionTech Manufacturing",
        industry="Manufacturing - Industrial Equipment",
        products_services=[
            "CNC machines",
            "3D printers",
            "Quality control systems"
        ],
        target_market="B2B - Automotive and aerospace manufacturers",
        geography=["United States", "Germany", "Japan"],
        key_strengths=[
            "High precision equipment",
            "24/7 support",
            "Custom solutions"
        ],
        additional_notes="Established 20 years, 500+ employees"
    )

    print("\nBusiness Context:")
    print(manufacturing_context.to_prompt_string())

    print("\n" + "-" * 80)
    print("Customer Search Queries:")
    print("-" * 80)
    customer_queries = builder.build_customer_queries(manufacturing_context)
    for i, query in enumerate(customer_queries, 1):
        print(f"{i}. {query}")

    print("\n" + "-" * 80)
    print("Partner Search Queries:")
    print("-" * 80)
    partner_queries = builder.build_partner_queries(manufacturing_context)
    for i, query in enumerate(partner_queries, 1):
        print(f"{i}. {query}")

    # Example 3: Query Refinement
    print("\n\n" + "=" * 80)
    print("Example 3: Query Refinement with Filters")
    print("=" * 80)

    base_query = "marketing agencies needing automation"

    print(f"\nBase Query: {base_query}")

    # Refine with geography
    refined_geo = builder.refine_query(base_query, {"geography": "Europe"})
    print(f"With Geography Filter: {refined_geo}")

    # Refine with industry
    refined_industry = builder.refine_query(base_query, {"industry": "Healthcare"})
    print(f"With Industry Filter: {refined_industry}")

    # Refine with multiple filters
    refined_multi = builder.refine_query(
        base_query,
        {"geography": "North America", "industry": "Technology"}
    )
    print(f"With Multiple Filters: {refined_multi}")

    # Example 4: Query Strategy Explanation
    print("\n\n" + "=" * 80)
    print("Query Generation Strategy Explained")
    print("=" * 80)

    print("""
Customer Query Strategies:
1. Target Market Focus: Uses the target_market field directly
   Example: "B2B - SMB marketing agencies in North America"

2. Product/Service Need: Combines target market with products
   Example: "companies needing Email marketing platform in North America"

3. Industry-Based: Focuses on industry + geography
   Example: "SaaS companies in North America"

4. Geography + Industry: Broad market search
   Example: "SaaS businesses in North America"

5. Size-Based: Uses company size filter if provided
   Example: "SMB marketing agencies 50-200 employees in North America"

Partner Query Strategies:
1. Partnership with Industry: Seeks partners for the industry
   Example: "companies partnering with SaaS businesses"

2. Complementary Products: Looks for integration opportunities
   Example: "companies integrating with Email marketing platform"

3. Technology Partnerships: For SaaS/tech companies
   Example: "technology integration partners in North America"

4. Partnership Type Filter: Uses specific partnership type
   Example: "technology partnership opportunities in North America"

5. Industry-Specific Partners: Based on industry filter
   Example: "Healthcare strategic partners in North America"

Key Design Decisions:
- Generate 3-5 queries per request (optimal balance of coverage and API efficiency)
- No duplicate queries (ensures diverse search coverage)
- Queries under 150 characters (maintains search effectiveness)
- Geography prioritizes filter over context
- Handles None/empty filters gracefully
- Combines multiple context fields for richer queries
""")

    print("=" * 80)
    print("Examples Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
