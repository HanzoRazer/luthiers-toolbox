#!/usr/bin/env python3
"""
List Semantic Owners

Sprint: MRP-5J / Governance Execution Alignment
Purpose: List semantic term ownership from the semantic registry

Usage:
    python list_semantic_owners.py [--json] [--json-output PATH] [--domain DOMAIN] [--term TERM] [--include-timestamp]

This is a manual reporting utility, not run in CI.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

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
    """Group terms by their owning domain."""
    by_domain = {}
    terms = registry.get("terms", {})

    for term_name, term_data in terms.items():
        domain = term_data.get("owner_domain", "unknown")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(term_name)

    return by_domain


def get_term_details(registry: Dict, term: str) -> Optional[Dict]:
    """Get details for a specific term."""
    terms = registry.get("terms", {})
    if term in terms:
        return {
            "term": term,
            **terms[term]
        }
    return None


def filter_by_domain(registry: Dict, domain: str) -> Dict[str, Dict]:
    """Filter terms by domain."""
    terms = registry.get("terms", {})
    return {
        name: data for name, data in terms.items()
        if data.get("owner_domain", "").lower() == domain.lower()
    }


def write_json_output(data: Dict, path: Path) -> None:
    """Write JSON report to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="List semantic term ownership")
    parser.add_argument("--json", action="store_true", help="Output in JSON format to stdout")
    parser.add_argument("--json-output", type=str, metavar="PATH", help="Write JSON report to file")
    parser.add_argument("--domain", type=str, help="Filter by domain")
    parser.add_argument("--term", type=str, help="Show details for specific term")
    parser.add_argument("--include-timestamp", action="store_true", help="Include generated_at timestamp")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable output")
    args = parser.parse_args()

    registry = load_semantic_registry()

    if "error" in registry:
        if not args.quiet:
            print(f"Error: {registry['error']}")
        sys.exit(1)

    results = {
        "script": "scripts/governance/list_semantic_owners.py",
        "passed": True,
        "severity": "informational",
        "summary": {},
        "findings": [],
    }

    if args.include_timestamp:
        results["generated_at"] = datetime.now(timezone.utc).isoformat()
    else:
        results["generated_at"] = None

    if args.term:
        term_details = get_term_details(registry, args.term)
        if term_details:
            results["summary"] = {"terms_found": 1}
            results["findings"] = [term_details]
        else:
            results["summary"] = {"terms_found": 0}
            results["findings"] = []
            if not args.quiet and not args.json:
                print(f"Term '{args.term}' not found in registry")

    elif args.domain:
        filtered = filter_by_domain(registry, args.domain)
        results["summary"] = {
            "domain": args.domain,
            "terms_found": len(filtered)
        }
        results["findings"] = [
            {"term": name, **data} for name, data in filtered.items()
        ]

    else:
        by_domain = get_owners_by_domain(registry)
        all_terms = registry.get("terms", {})
        results["summary"] = {
            "total_domains": len(by_domain),
            "total_terms": len(all_terms),
            "terms_by_domain": {domain: len(terms) for domain, terms in by_domain.items()}
        }
        results["findings"] = [
            {"domain": domain, "terms": terms}
            for domain, terms in sorted(by_domain.items())
        ]

    if args.json_output:
        output_path = Path(args.json_output)
        write_json_output(results, output_path)
        if not args.quiet:
            print(f"JSON report written to: {output_path}")

    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.quiet:
        print("=" * 50)
        print("SEMANTIC TERM OWNERSHIP")
        print("=" * 50)

        if args.term:
            if results["findings"]:
                term_info = results["findings"][0]
                print(f"\nTerm: {term_info['term']}")
                print(f"  Owner: {term_info.get('owner_domain', 'unknown')}")
                print(f"  Description: {term_info.get('description', 'N/A')}")
            else:
                print(f"\nTerm '{args.term}' not found")

        elif args.domain:
            print(f"\nDomain: {args.domain}")
            print(f"Terms: {results['summary']['terms_found']}")
            for finding in results["findings"]:
                print(f"  - {finding['term']}")

        else:
            print(f"\nTotal domains: {results['summary']['total_domains']}")
            print(f"Total terms: {results['summary']['total_terms']}")
            print("\nTerms by domain:")
            for domain, count in results["summary"]["terms_by_domain"].items():
                print(f"  {domain}: {count}")

        print("\n" + "=" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()
