#!/usr/bin/env python3
"""
List Semantic Owners

Sprint: MRP-5J
Purpose: List semantic term owners from the registry

Usage:
    python list_semantic_owners.py [--json] [--domain DOMAIN] [--tier TIER]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Repository paths
REPO_ROOT = Path(__file__).parent.parent.parent
ONTOLOGY_DIR = REPO_ROOT / "docs" / "governance" / "ontology"


def load_semantic_registry() -> Dict:
    """Load the semantic registry."""
    registry_file = ONTOLOGY_DIR / "semantic_registry.json"
    if not registry_file.exists():
        return {"error": "Semantic registry not found"}
    try:
        return json.loads(registry_file.read_text())
    except Exception as e:
        return {"error": str(e)}


def get_owners_by_domain(registry: Dict) -> Dict[str, List[str]]:
    """Group terms by owning domain."""
    by_domain = {}
    terms = registry.get("terms", {})

    for term_name, term_data in terms.items():
        domain = term_data.get("owner_domain", "unknown")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(term_name)

    # Sort terms within each domain
    for domain in by_domain:
        by_domain[domain].sort()

    return by_domain


def get_owners_by_tier(registry: Dict) -> Dict[int, List[Dict]]:
    """Group terms by authority tier."""
    by_tier = {}
    terms = registry.get("terms", {})

    for term_name, term_data in terms.items():
        tier = term_data.get("authority_tier", 0)
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append({
            "term": term_name,
            "domain": term_data.get("owner_domain", "unknown"),
            "definition": term_data.get("canonical_definition", "")[:60]
        })

    return by_tier


def get_term_details(registry: Dict, term_name: str) -> Dict:
    """Get detailed information about a specific term."""
    terms = registry.get("terms", {})
    return terms.get(term_name, {"error": f"Term '{term_name}' not found"})


def filter_by_domain(registry: Dict, domain: str) -> Dict[str, Dict]:
    """Filter terms by domain."""
    filtered = {}
    terms = registry.get("terms", {})

    for term_name, term_data in terms.items():
        if term_data.get("owner_domain", "").lower() == domain.lower():
            filtered[term_name] = term_data

    return filtered


def filter_by_tier(registry: Dict, tier: int) -> Dict[str, Dict]:
    """Filter terms by authority tier."""
    filtered = {}
    terms = registry.get("terms", {})

    for term_name, term_data in terms.items():
        if term_data.get("authority_tier", 0) == tier:
            filtered[term_name] = term_data

    return filtered


def main():
    parser = argparse.ArgumentParser(description="List semantic term owners")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--domain", type=str, help="Filter by domain")
    parser.add_argument("--tier", type=int, help="Filter by authority tier (1-3)")
    parser.add_argument("--term", type=str, help="Show details for specific term")
    args = parser.parse_args()

    # Load registry
    registry = load_semantic_registry()
    if "error" in registry:
        print(f"Error: {registry['error']}")
        sys.exit(1)

    # Handle specific term lookup
    if args.term:
        details = get_term_details(registry, args.term)
        if args.json:
            print(json.dumps(details, indent=2))
        else:
            if "error" in details:
                print(details["error"])
                sys.exit(1)
            print(f"\nTerm: {args.term}")
            print(f"  Owner: {details.get('owner_domain', 'unknown')}")
            print(f"  Tier: {details.get('authority_tier', 'unknown')}")
            print(f"  Definition: {details.get('canonical_definition', 'N/A')}")
            if details.get("allowed_meanings"):
                print(f"  Allowed meanings: {', '.join(details['allowed_meanings'])}")
            if details.get("prohibited_meanings"):
                print(f"  Prohibited meanings: {', '.join(details['prohibited_meanings'])}")
        sys.exit(0)

    # Apply filters
    if args.domain:
        filtered = filter_by_domain(registry, args.domain)
        if args.json:
            print(json.dumps({"domain": args.domain, "terms": filtered}, indent=2))
        else:
            print(f"\nTerms owned by '{args.domain}':")
            for term in sorted(filtered.keys()):
                print(f"  - {term}")
            print(f"\nTotal: {len(filtered)} terms")
        sys.exit(0)

    if args.tier:
        filtered = filter_by_tier(registry, args.tier)
        if args.json:
            print(json.dumps({"tier": args.tier, "terms": filtered}, indent=2))
        else:
            print(f"\nTier {args.tier} terms:")
            for term in sorted(filtered.keys()):
                data = filtered[term]
                print(f"  - {term} (owner: {data.get('owner_domain', 'unknown')})")
            print(f"\nTotal: {len(filtered)} terms")
        sys.exit(0)

    # Default: show all owners grouped by domain
    by_domain = get_owners_by_domain(registry)
    by_tier = get_owners_by_tier(registry)

    total_terms = len(registry.get("terms", {}))
    total_domains = len(by_domain)

    if args.json:
        print(json.dumps({
            "total_terms": total_terms,
            "total_domains": total_domains,
            "by_domain": by_domain,
            "by_tier": {str(k): v for k, v in by_tier.items()}
        }, indent=2))
    else:
        print("=" * 60)
        print("SEMANTIC TERM OWNERSHIP REPORT")
        print("=" * 60)

        print(f"\nTotal terms: {total_terms}")
        print(f"Total domains: {total_domains}")

        print("\n--- BY DOMAIN ---")
        for domain in sorted(by_domain.keys()):
            terms = by_domain[domain]
            print(f"\n{domain} ({len(terms)} terms):")
            for term in terms:
                print(f"  - {term}")

        print("\n--- BY AUTHORITY TIER ---")
        for tier in sorted(by_tier.keys()):
            entries = by_tier[tier]
            print(f"\nTier {tier} ({len(entries)} terms):")
            for entry in entries:
                print(f"  - {entry['term']} ({entry['domain']})")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
