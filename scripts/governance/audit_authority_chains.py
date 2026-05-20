#!/usr/bin/env python3
"""
Audit Authority Chains

Sprint: MRP-5J / Governance Execution Alignment
Purpose: Verify no downstream authority redefines upstream terms

Validates:
- Registry structure completeness
- Authority chain ordering invariants
- Semantic authority chain: Runtime Consumer must not precede Vocabulary Registry/Domain Owner
- Geometry authority chain: Translator must not precede upstream geometry owners

Usage:
    python audit_authority_chains.py [--json] [--strict] [--json-output PATH] [--quiet]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Repository paths
REPO_ROOT = Path(__file__).parent.parent.parent
ONTOLOGY_DIR = REPO_ROOT / "docs" / "governance" / "ontology"


def load_authority_chain_registry() -> Dict:
    """Load the authority chain registry."""
    registry_file = ONTOLOGY_DIR / "authority_chain_registry.json"
    if not registry_file.exists():
        return {"error": "Authority chain registry not found"}
    try:
        return json.loads(registry_file.read_text())
    except Exception as e:
        return {"error": str(e)}


def load_semantic_registry() -> Dict:
    """Load the semantic registry."""
    registry_file = ONTOLOGY_DIR / "semantic_registry.json"
    if not registry_file.exists():
        return {}
    try:
        return json.loads(registry_file.read_text())
    except Exception:
        return {}


def build_authority_graph(registry: Dict) -> Dict[str, List[str]]:
    """Build a graph of authority chain dependencies."""
    graph = {}
    chains = registry.get("chains", {})

    for chain_name, chain_data in chains.items():
        sequence = chain_data.get("sequence", [])
        graph[chain_name] = sequence

    return graph


def get_term_ownership(semantic_registry: Dict) -> Dict[str, str]:
    """Get mapping of terms to their owning domains."""
    ownership = {}
    terms = semantic_registry.get("terms", {})

    for term_name, term_data in terms.items():
        owner = term_data.get("owner_domain", "unknown")
        ownership[term_name] = owner

    return ownership


def check_downstream_redefinitions(
    authority_registry: Dict,
    term_ownership: Dict[str, str]
) -> List[Dict]:
    """Check if any downstream authority redefines upstream terms."""
    violations = []
    domain_ownership = authority_registry.get("domain_ownership", {})

    # Check for forbidden ownership violations
    for domain_name, domain_data in domain_ownership.items():
        canonical_owner = domain_data.get("canonical_owner", "")
        forbidden = domain_data.get("forbidden_ownership", "")

        # Check if any term owned by this domain is claimed by a forbidden owner
        for term, owner in term_ownership.items():
            term_lower = term.lower()
            if domain_name in term_lower:
                # Term relates to this domain
                if canonical_owner and owner != canonical_owner:
                    # Check if the owner is a valid operational owner
                    operational_owners = domain_data.get("operational_owners", [])
                    if owner not in operational_owners and owner != canonical_owner:
                        violations.append({
                            "chain": domain_name,
                            "term": term,
                            "canonical_owner": canonical_owner,
                            "actual_owner": owner,
                            "severity": "warning"
                        })

    return violations


def check_chain_completeness(registry: Dict) -> List[str]:
    """Check if authority chains have required fields."""
    missing = []
    chains = registry.get("chains", {})

    required_fields = {"description", "sequence"}

    for chain_name, chain_data in chains.items():
        for field in required_fields:
            if field not in chain_data:
                missing.append(f"Chain '{chain_name}' missing '{field}'")

        sequence = chain_data.get("sequence", [])
        if len(sequence) == 0:
            missing.append(f"Chain '{chain_name}' has empty sequence")

    return missing


def check_authority_level_ordering(registry: Dict) -> List[Dict]:
    """Check that sequences have proper invariants documented."""
    violations = []
    chains = registry.get("chains", {})

    for chain_name, chain_data in chains.items():
        invariants = chain_data.get("invariants", [])
        if not invariants:
            violations.append({
                "chain": chain_name,
                "node": "N/A",
                "issue": "No invariants defined for authority chain",
                "severity": "warning"
            })

        # Check for source document reference
        if "source_document" not in chain_data:
            violations.append({
                "chain": chain_name,
                "node": "N/A",
                "issue": "No source_document reference",
                "severity": "warning"
            })

    return violations


def check_semantic_authority_ordering(registry: Dict) -> List[Dict]:
    """
    Check semantic_authority_chain: Runtime Consumer must not appear before
    Vocabulary Registry or Domain Owner.
    """
    violations = []
    chains = registry.get("chains", {})
    chain_data = chains.get("semantic_authority_chain", {})
    sequence = chain_data.get("sequence", [])

    if not sequence:
        return violations

    # Find positions
    runtime_pos = None
    vocab_pos = None
    domain_pos = None

    for i, node in enumerate(sequence):
        if node == "Runtime Consumer":
            runtime_pos = i
        elif node == "Vocabulary Registry":
            vocab_pos = i
        elif node == "Domain Owner":
            domain_pos = i

    # Runtime Consumer must not appear before Vocabulary Registry
    if runtime_pos is not None and vocab_pos is not None:
        if runtime_pos < vocab_pos:
            violations.append({
                "type": "runtime_authority_inversion",
                "chain": "semantic_authority_chain",
                "message": "Runtime Consumer appears before Vocabulary Registry",
                "upstream_node": "Vocabulary Registry",
                "downstream_node": "Runtime Consumer",
                "severity": "error"
            })

    # Runtime Consumer must not appear before Domain Owner
    if runtime_pos is not None and domain_pos is not None:
        if runtime_pos < domain_pos:
            violations.append({
                "type": "runtime_authority_inversion",
                "chain": "semantic_authority_chain",
                "message": "Runtime Consumer appears before Domain Owner",
                "upstream_node": "Domain Owner",
                "downstream_node": "Runtime Consumer",
                "severity": "error"
            })

    return violations


def check_geometry_authority_ordering(registry: Dict) -> List[Dict]:
    """
    Check geometry_authority_chain: Translator must not appear before
    Blueprint, IBG, BOE, CadSemantics, TopologyBuilder, or ShellValidation.
    """
    violations = []
    chains = registry.get("chains", {})
    chain_data = chains.get("geometry_authority_chain", {})
    sequence = chain_data.get("sequence", [])

    if not sequence:
        return violations

    # Upstream geometry owners that Translator must not precede
    upstream_nodes = [
        "Blueprint", "IBG", "BOE", "CadSemantics",
        "TopologyBuilder", "ShellValidation"
    ]

    # Find Translator position
    translator_pos = None
    for i, node in enumerate(sequence):
        if node == "Translator":
            translator_pos = i
            break

    if translator_pos is None:
        return violations

    # Check that Translator doesn't precede any upstream nodes
    for i, node in enumerate(sequence):
        if node in upstream_nodes and translator_pos < i:
            # Translator appears before this upstream node - this is actually OK
            # We need the opposite check: Translator should NOT appear BEFORE upstream
            pass

    # Correct check: find upstream nodes that appear AFTER translator
    for node in upstream_nodes:
        try:
            node_pos = sequence.index(node)
            if translator_pos < node_pos:
                violations.append({
                    "type": "translator_authority_inversion",
                    "chain": "geometry_authority_chain",
                    "message": f"Translator appears before {node}",
                    "upstream_node": node,
                    "downstream_node": "Translator",
                    "severity": "error"
                })
        except ValueError:
            # Node not in sequence, skip
            pass

    return violations


def write_json_output(data: Dict, path: Path) -> None:
    """Write JSON report to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Audit authority chains")
    parser.add_argument("--json", action="store_true", help="Output in JSON format to stdout")
    parser.add_argument("--json-output", type=str, metavar="PATH", help="Write JSON report to file")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on blocking issues")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable output")
    args = parser.parse_args()

    # Load registries
    authority_registry = load_authority_chain_registry()
    if "error" in authority_registry:
        if not args.quiet:
            print(f"Error loading authority chain registry: {authority_registry['error']}")
        sys.exit(1)

    semantic_registry = load_semantic_registry()

    results = {
        "chains_audited": len(authority_registry.get("chains", {})),
        "domains_audited": len(authority_registry.get("domain_ownership", {})),
        "completeness_issues": [],
        "ordering_violations": [],
        "authority_inversion_violations": [],
        "redefinition_violations": [],
        "summary": {}
    }

    # Check completeness
    results["completeness_issues"] = check_chain_completeness(authority_registry)

    # Check authority level ordering (documentation checks)
    results["ordering_violations"] = check_authority_level_ordering(authority_registry)

    # Check specific authority chain ordering invariants
    semantic_violations = check_semantic_authority_ordering(authority_registry)
    geometry_violations = check_geometry_authority_ordering(authority_registry)
    results["authority_inversion_violations"] = semantic_violations + geometry_violations

    # Check for downstream redefinitions
    term_ownership = get_term_ownership(semantic_registry)
    results["redefinition_violations"] = check_downstream_redefinitions(
        authority_registry, term_ownership
    )

    # Summary
    results["summary"] = {
        "completeness_issues": len(results["completeness_issues"]),
        "ordering_violations": len(results["ordering_violations"]),
        "authority_inversion_violations": len(results["authority_inversion_violations"]),
        "redefinition_violations": len(results["redefinition_violations"]),
        "total_issues": (
            len(results["completeness_issues"]) +
            len(results["ordering_violations"]) +
            len(results["authority_inversion_violations"]) +
            len(results["redefinition_violations"])
        )
    }

    # Count blocking violations (severity: error)
    blocking_redefinitions = [
        v for v in results["redefinition_violations"]
        if v.get("severity") == "error"
    ]
    blocking_inversions = [
        v for v in results["authority_inversion_violations"]
        if v.get("severity") == "error"
    ]

    # Blocking = completeness issues OR authority inversions OR error-severity redefinitions
    blocking_count = (
        len(results["completeness_issues"]) +
        len(blocking_inversions) +
        len(blocking_redefinitions)
    )
    warning_count = results["summary"]["total_issues"] - blocking_count

    results["passed"] = blocking_count == 0
    results["blocking_violations"] = blocking_count
    results["warnings"] = warning_count

    # Write JSON to file if requested
    if args.json_output:
        output_path = Path(args.json_output)
        write_json_output(results, output_path)
        if not args.quiet:
            print(f"JSON report written to: {output_path}")

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.quiet:
        print("=" * 60)
        print("AUTHORITY CHAIN AUDIT REPORT")
        print("=" * 60)

        print(f"\nChains audited: {results['chains_audited']}")
        print(f"Domains audited: {results['domains_audited']}")

        if results["completeness_issues"]:
            print("\n--- COMPLETENESS ISSUES [BLOCKING] ---")
            for issue in results["completeness_issues"]:
                print(f"  {issue}")
        else:
            print("\n--- Completeness: OK ---")

        if results["authority_inversion_violations"]:
            print("\n--- AUTHORITY INVERSION VIOLATIONS [BLOCKING] ---")
            for v in results["authority_inversion_violations"]:
                print(f"  [{v['chain']}] {v['message']}")
        else:
            print("\n--- Authority inversions: OK ---")

        if results["ordering_violations"]:
            print("\n--- DOCUMENTATION ISSUES [WARNING] ---")
            for v in results["ordering_violations"]:
                print(f"  {v['chain']}: {v['issue']}")

        if results["redefinition_violations"]:
            severity_counts = {}
            for v in results["redefinition_violations"]:
                sev = v.get("severity", "warning")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            print(f"\n--- OWNERSHIP VIOLATIONS ({severity_counts}) ---")
            for v in results["redefinition_violations"]:
                print(f"  [{v.get('severity', 'warning').upper()}] {v['chain']}: '{v['term']}'")

        print("\n" + "=" * 60)
        if blocking_count > 0:
            print(f"STATUS: BLOCKING - {blocking_count} violation(s)")
        elif warning_count > 0:
            print(f"STATUS: WARNINGS - {warning_count} issue(s)")
        else:
            print("STATUS: CLEAN")
        print("=" * 60)

    # Exit code
    if blocking_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
