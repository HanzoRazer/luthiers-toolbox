#!/usr/bin/env python3
"""
Namespace / Authority Drift Detector  (v1 - ADVISORY)

Sprint: SPINE / pre-governance asset recovery follow-on
Purpose: Adjudicate whether a *candidate change* (a git ref against a base)
    introduces, revives, duplicates, bypasses, or alters an authority-bearing
    namespace in a way inconsistent with the current DECLARED authority topology.

Boundary with sibling governance tools (non-duplication, per the recovery report R3):
  - detect_semantic_drift.py   -> terminology / vocabulary drift (words). NOT namespaces.
  - audit_authority_chains.py  -> the authority registry's OWN internal ordering
                                 self-consistency. NOT a candidate diff.
  - THIS tool                  -> does a candidate code change drift from the declared
                                 authority topology? (the gap neither sibling covers)

Core boundary rule (from the archaeology):
  ****  THE DETECTOR MAY CONSUME AUTHORITY. IT MAY NOT CREATE AUTHORITY.  ****
  It never infers namespace->domain ownership from path names, keywords, or module
  contents. When no declared namespace->domain binding exists, the honest deterministic
  verdict is INSUFFICIENT_EVIDENCE - which is itself evidence that the governance
  topology is incomplete at the namespace-binding layer.

  WHY NOT HEURISTICS  (read this before "improving" the tool)
  -----------------------------------------------------------
  The production authority registry declares NO namespace_bindings today, so almost
  every code namespace adjudicates to INSUFFICIENT_EVIDENCE. That looks like a tool
  that isn't trying. It is the opposite: it is the tool refusing to invent the fact
  it was asked to check against.

  Inferring a binding - matching a namespace to a same-named domain, to a declared
  owner, or to the module path it happens to live under - would make this detector
  MANUFACTURE ownership that no governance record ever asserted. Every downstream
  verdict would then inherit a fabricated premise, and the failure is asymmetric:
  a wrong DECLARED_EXTENSION silently blesses real drift, while an honest
  INSUFFICIENT_EVIDENCE merely says "governance has not decided yet". One of those
  is recoverable.

  The bait is real and specific: production declares both a `geometry` and a
  `topology` domain, so namespaces like `body_outline` and `retopo` look obviously
  bindable to a human and to a regex. They are not bound. Until governance binds
  them, "we do not know" is the true answer.

  This rule is enforced executably, not by convention. See the ANTI-INFERENCE GUARD
  section of tests/governance/test_namespace_authority_drift.py: a bait topology whose
  domain and owner names collide head-on with the probed namespace names, asserting
  none of them resolves. Four heuristics (exact domain-name match, fuzzy substring
  match, owner-name match, path sniffing) were each injected during development and
  each was caught. If you add inference, those tests fail - by design.

  Closing the gap is a GOVERNANCE action, not a detector change: bindings declare
  ownership and therefore carry authority. This module already consumes a
  `namespace_bindings` map the moment one is declared - no code change needed.
  Rationale, expected consequences, and the deferred-work note:
      docs/governance/ontology/NAMESPACE_BINDING_GAP.md

Architecture (three separable layers - the analysis engine is Git-independent):
      git/ref adapter  ->  candidate-change model  ->  authority analysis engine

Portability:
  Luthiers-specific roots/paths live on ``DetectorConfig`` (defaults = today's
  Luthiers layout). The Git-independent engine consumes ``CandidateChange`` +
  ``AuthorityTopology`` only — it does not invent authority and does not require
  a Luthiers checkout. Vendors should copy the engine surface, not the CLI/git
  adapter.

Usage:
    python scripts/governance/check_namespace_authority_drift.py \
        --base origin/main --candidate feature/mesh-pipeline-scaffold [--json] [--quiet]

Exit codes (v1 is ADVISORY):
    0 - always, in v1. Verdicts carry an independent Severity so a later governance
        sprint can convert selected verdicts to blocking WITHOUT redesigning the engine.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Default Luthiers layout (preserved for CLI + existing tests).
# Injectable via DetectorConfig for portability / vendoring.
# ---------------------------------------------------------------------------
_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ONTOLOGY_DIR = _DEFAULT_REPO_ROOT / "docs" / "governance" / "ontology"
_DEFAULT_AUTHORITY_REGISTRY = _DEFAULT_ONTOLOGY_DIR / "authority_chain_registry.json"
_DEFAULT_AUTHORITY_ARTIFACT_PATHS = frozenset({
    "contracts/schema_registry.json",
    "docs/governance/ontology/authority_chain_registry.json",
    "docs/governance/ontology/semantic_registry.json",
    "docs/governance/governance_manifest.json",
})
_DEFAULT_CODE_ROOTS = ("services/api/app/", "services/")
_DEFAULT_NON_CODE_HINTS = ("docs/", "tests/", "test/", "examples/", "presets/", ".github/")

# Backward-compatible module aliases (same values as pre-portability constants).
REPO_ROOT = _DEFAULT_REPO_ROOT
ONTOLOGY_DIR = _DEFAULT_ONTOLOGY_DIR
AUTHORITY_REGISTRY = _DEFAULT_AUTHORITY_REGISTRY
AUTHORITY_ARTIFACT_PATHS = set(_DEFAULT_AUTHORITY_ARTIFACT_PATHS)
CODE_ROOTS = _DEFAULT_CODE_ROOTS
NON_CODE_HINTS = _DEFAULT_NON_CODE_HINTS

# Reuse the shared governance Severity vocabulary (lib.py) when importable; else inline.
try:  # pragma: no cover - import path resolution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib import Severity  # type: ignore
except Exception:  # pragma: no cover
    class Severity(str, Enum):  # type: ignore
        INFORMATIONAL = "informational"
        ADVISORY = "advisory"
        WARNING = "warning"
        BLOCKING = "blocking"


@dataclass(frozen=True)
class DetectorConfig:
    """Injectable layout facts for the git/ref adapter and registry loader.

    These are *path classification* and *file location* facts — not authority.
    The analysis engine never reads this object; it only sees CandidateChange +
    AuthorityTopology. Defaults match the Luthiers-Toolbox layout.
    """

    repo_root: Path = _DEFAULT_REPO_ROOT
    code_roots: Tuple[str, ...] = _DEFAULT_CODE_ROOTS
    non_code_hints: Tuple[str, ...] = _DEFAULT_NON_CODE_HINTS
    authority_artifact_paths: FrozenSet[str] = _DEFAULT_AUTHORITY_ARTIFACT_PATHS
    authority_registry_path: Path = _DEFAULT_AUTHORITY_REGISTRY

    @classmethod
    def luthiers_defaults(cls) -> "DetectorConfig":
        """Explicit constructor for the preserved Luthiers layout."""
        return cls()


# Module-level default used by CLI and loaders when no config is passed.
DEFAULT_CONFIG = DetectorConfig.luthiers_defaults()


class Verdict(str, Enum):
    # Advisory-clear (exit 0, informational):
    NO_AUTHORITY_IMPACT = "NO_AUTHORITY_IMPACT"
    DECLARED_EXTENSION = "DECLARED_EXTENSION"
    NOVEL_VALID = "NOVEL_VALID"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    # Flagged (reported clearly; still exit 0 in v1 advisory mode):
    DUPLICATE_AUTHORITY = "DUPLICATE_AUTHORITY"
    PARALLEL_AUTHORITY = "PARALLEL_AUTHORITY"
    OBSOLETE_AUTHORITY = "OBSOLETE_AUTHORITY"
    AUTHORITY_BYPASS = "AUTHORITY_BYPASS"


_FLAGGED = {
    Verdict.DUPLICATE_AUTHORITY,
    Verdict.PARALLEL_AUTHORITY,
    Verdict.OBSOLETE_AUTHORITY,
    Verdict.AUTHORITY_BYPASS,
}

_SEVERITY = {
    Verdict.NO_AUTHORITY_IMPACT: Severity.INFORMATIONAL,
    Verdict.DECLARED_EXTENSION: Severity.INFORMATIONAL,
    Verdict.NOVEL_VALID: Severity.INFORMATIONAL,
    Verdict.INSUFFICIENT_EVIDENCE: Severity.ADVISORY,
    Verdict.DUPLICATE_AUTHORITY: Severity.WARNING,
    Verdict.PARALLEL_AUTHORITY: Severity.WARNING,
    Verdict.OBSOLETE_AUTHORITY: Severity.WARNING,
    Verdict.AUTHORITY_BYPASS: Severity.WARNING,
}


# --------------------------- candidate-change model (Git-independent) ---------------------------
@dataclass
class NamespaceChange:
    """A single namespace-level change in a candidate.

    FACTUAL fields (a git adapter may set these - they are facts about the diff):
        namespace, path, change, is_code_namespace, touches_authority_artifacts
    AUTHORITY-DERIVED fields (set ONLY from a declared binding source - a fixture or a
    future namespace-binding registry - NEVER inferred by the git adapter from paths):
        declared_domain, declared_concept, introduces_parallel_registry,
        violates_invariant, restores_superseded
    """
    namespace: str
    path: str
    change: str  # "added" | "removed" | "modified"
    is_code_namespace: bool = True
    touches_authority_artifacts: Tuple[str, ...] = ()
    # authority-derived (binding-sourced only):
    declared_domain: Optional[str] = None
    declared_concept: Optional[str] = None
    introduces_parallel_registry: bool = False
    violates_invariant: Optional[str] = None
    restores_superseded: bool = False


@dataclass
class CandidateChange:
    base_ref: str
    candidate_ref: str
    namespace_changes: List[NamespaceChange] = field(default_factory=list)


@dataclass
class DriftFinding:
    namespace: str
    path: str
    verdict: Verdict
    severity: Severity
    evidence: str

    def to_dict(self) -> Dict:
        return {
            "namespace": self.namespace,
            "path": self.path,
            "verdict": self.verdict.value,
            "severity": self.severity.value,
            "flagged": self.verdict in _FLAGGED,
            "evidence": self.evidence,
        }


# --------------------------- authority analysis engine (Git-independent) ---------------------------
class AuthorityTopology:
    """Reads DECLARED authority; never invents it."""

    def __init__(self, registry: Dict, namespace_bindings: Optional[Dict] = None):
        self.registry = registry
        self.domain_ownership: Dict = registry.get("domain_ownership", {}) or {}
        self.chains: Dict = registry.get("chains", {}) or {}
        # Namespace->domain bindings: from the registry if present (currently ABSENT in
        # production) or injected by a caller/fixture. This is the only sanctioned source
        # of a namespace->domain mapping - there is no path/keyword inference anywhere.
        self.namespace_bindings: Dict = (
            namespace_bindings
            if namespace_bindings is not None
            else registry.get("namespace_bindings", {}) or {}
        )

    @classmethod
    def load(
        cls,
        registry_path: Optional[Path] = None,
        *,
        config: Optional[DetectorConfig] = None,
    ) -> "AuthorityTopology":
        """Load topology from a registry file.

        ``registry_path`` wins when given. Otherwise ``config.authority_registry_path``
        (defaulting to the Luthiers registry) is used. No namespace bindings are
        invented here.
        """
        cfg = config or DEFAULT_CONFIG
        path = registry_path if registry_path is not None else cfg.authority_registry_path
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    def operational_owners(self, domain: str) -> set:
        d = self.domain_ownership.get(domain, {}) or {}
        owners = set(d.get("operational_owners", []) or [])
        if d.get("canonical_owner"):
            owners.add(d["canonical_owner"])
        return owners

    def resolve(self, nc: NamespaceChange) -> Optional[Tuple[str, str]]:
        """Return (domain, concept) IFF a DECLARED binding exists; else None.

        No inference. A binding is honored only if its domain is a real declared domain.
        """
        # 1) binding declared on the change itself (from a binding source / fixture)
        if nc.declared_domain and nc.declared_domain in self.domain_ownership:
            return (nc.declared_domain, nc.declared_concept or nc.namespace)
        # 2) binding from the registry's namespace_bindings map (absent in production)
        b = self.namespace_bindings.get(nc.namespace)
        if isinstance(b, dict) and b.get("domain") in self.domain_ownership:
            return (b["domain"], b.get("concept", nc.namespace))
        return None


def adjudicate(nc: NamespaceChange, topo: AuthorityTopology) -> DriftFinding:
    """Deterministic verdict for one namespace change. Every verdict carries evidence."""
    def finding(v: Verdict, ev: str) -> DriftFinding:
        return DriftFinding(nc.namespace, nc.path, v, _SEVERITY[v], ev)

    # A pure non-code change bears no authority-bearing namespace.
    if not nc.is_code_namespace:
        return finding(
            Verdict.NO_AUTHORITY_IMPACT,
            "change introduces no code namespace (docs/tests/config only)",
        )

    binding = topo.resolve(nc)
    if binding is None:
        art = (
            f"; touches authority artifact(s) {list(nc.touches_authority_artifacts)}"
            if nc.touches_authority_artifacts
            else ""
        )
        return finding(
            Verdict.INSUFFICIENT_EVIDENCE,
            (
                f"code namespace '{nc.namespace}' has no declared namespace->domain "
                f"binding in the authority topology - cannot adjudicate ownership "
                f"(binding-layer gap){art}. This is evidence the topology is "
                f"incomplete, not a defect in the change."
            ),
        )

    domain, concept = binding
    if nc.violates_invariant:
        return finding(
            Verdict.AUTHORITY_BYPASS,
            f"change in domain '{domain}' violates a declared chain invariant: "
            f"{nc.violates_invariant!r}",
        )
    if nc.restores_superseded:
        return finding(
            Verdict.OBSOLETE_AUTHORITY,
            f"restores a namespace declared superseded within domain '{domain}'",
        )
    if nc.introduces_parallel_registry:
        return finding(
            Verdict.PARALLEL_AUTHORITY,
            f"introduces an independent registry/contract for domain '{domain}', "
            f"which already has a declared authority",
        )

    owners = topo.operational_owners(domain)
    if concept in owners:
        return finding(
            Verdict.DECLARED_EXTENSION,
            f"'{concept}' is a declared operational owner of domain '{domain}' "
            f"({sorted(owners)}) - recognized authority participant, not drift",
        )
    if owners:
        return finding(
            Verdict.DUPLICATE_AUTHORITY,
            f"'{concept}' claims domain '{domain}' already owned by {sorted(owners)} "
            f"and is not a declared owner",
        )
    return finding(
        Verdict.NOVEL_VALID,
        f"'{concept}' introduces domain '{domain}' with no existing declared owner "
        f"and no conflicting authority",
    )


def analyze(change: CandidateChange, topo: AuthorityTopology) -> List[DriftFinding]:
    """Git-independent analysis: CandidateChange + AuthorityTopology → findings."""
    return [adjudicate(nc, topo) for nc in change.namespace_changes]


def analyze_namespace_authority_drift(
    change: CandidateChange,
    topology: Union[AuthorityTopology, Dict, Path],
    *,
    namespace_bindings: Optional[Dict] = None,
) -> List[DriftFinding]:
    """Portable engine entrypoint for vendors / code-analysis-tool adapters.

    Accepts an ``AuthorityTopology``, a registry dict, or a path to a
    registry-shaped JSON file. Optional ``namespace_bindings`` are honored only
    when ``topology`` is a dict or path (injected binding source); when an
    ``AuthorityTopology`` is passed, its existing bindings are used unchanged.

    Does not invent authority. Does not touch git.
    """
    if isinstance(topology, AuthorityTopology):
        topo = topology
    elif isinstance(topology, Path):
        data = json.loads(topology.read_text(encoding="utf-8"))
        topo = AuthorityTopology(data, namespace_bindings=namespace_bindings)
    elif isinstance(topology, dict):
        topo = AuthorityTopology(topology, namespace_bindings=namespace_bindings)
    else:
        raise TypeError(
            "topology must be AuthorityTopology | dict | Path, "
            f"got {type(topology).__name__}"
        )
    return analyze(change, topo)


# --------------------------- git/ref adapter (the ONLY Git-coupled layer) ---------------------------
def _git(args: List[str], *, config: Optional[DetectorConfig] = None) -> str:
    cfg = config or DEFAULT_CONFIG
    return subprocess.run(
        ["git", *args], cwd=str(cfg.repo_root), check=True,
        capture_output=True, text=True,
    ).stdout


def _namespace_of(
    path: str, *, config: Optional[DetectorConfig] = None
) -> Tuple[str, bool]:
    """(namespace_identifier, is_code_namespace) - a FACTUAL path classification only."""
    cfg = config or DEFAULT_CONFIG
    p = path.replace("\\", "/")
    for root in cfg.code_roots:
        if p.startswith(root):
            rest = p[len(root):]
            seg = rest.split("/", 1)[0]
            if seg and not seg.endswith(".py") or "/" in rest:
                # top-level package/service segment
                return seg, True
            # a bare file directly under the root
            return seg or rest, True
    if any(h in p for h in cfg.non_code_hints) or p.startswith("contracts/"):
        top = p.split("/", 1)[0]
        return top, False
    return p.split("/", 1)[0], False


def build_candidate_change(
    base: str,
    candidate: str,
    *,
    config: Optional[DetectorConfig] = None,
) -> CandidateChange:
    """Build the candidate-change model from a real diff. Sets FACTUAL fields only -
    never a declared_domain/concept (that would be authority inference)."""
    cfg = config or DEFAULT_CONFIG
    out = _git(["diff", "--name-status", f"{base}...{candidate}"], config=cfg)
    # aggregate per namespace
    agg: Dict[str, Dict] = {}
    primary_code_root = cfg.code_roots[0] if cfg.code_roots else ""
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][0]  # A/M/D/R...
        path = parts[-1]
        ns, is_code = _namespace_of(path, config=cfg)
        rec = agg.setdefault(ns, {
            "path": f"{primary_code_root}{ns}" if is_code else ns,
            "is_code": is_code, "statuses": set(), "arts": set(),
        })
        rec["statuses"].add(status)
        rec["is_code"] = rec["is_code"] or is_code
        norm = path.replace("\\", "/")
        if norm in cfg.authority_artifact_paths:
            rec["arts"].add(norm)

    changes: List[NamespaceChange] = []
    for ns, rec in sorted(agg.items()):
        statuses = rec["statuses"]
        change = "added" if statuses <= {"A"} else ("removed" if statuses <= {"D"} else "modified")
        changes.append(NamespaceChange(
            namespace=ns, path=rec["path"], change=change,
            is_code_namespace=rec["is_code"],
            touches_authority_artifacts=tuple(sorted(rec["arts"])),
        ))
    return CandidateChange(base_ref=base, candidate_ref=candidate, namespace_changes=changes)


# --------------------------- CLI ---------------------------
def _render(
    findings: List[DriftFinding],
    change: CandidateChange,
    as_json: bool,
    quiet: bool,
    *,
    config: Optional[DetectorConfig] = None,
) -> None:
    cfg = config or DEFAULT_CONFIG
    if as_json:
        print(json.dumps({
            "base": change.base_ref, "candidate": change.candidate_ref,
            "mode": "advisory-v1",
            "findings": [f.to_dict() for f in findings],
        }, indent=2))
        return
    print(f"Namespace/Authority Drift Detector (advisory v1)")
    print(f"  base={change.base_ref}  candidate={change.candidate_ref}")
    try:
        reg_disp = cfg.authority_registry_path.relative_to(cfg.repo_root)
    except ValueError:
        reg_disp = cfg.authority_registry_path
    print(f"  authority topology: {reg_disp}")
    print()
    if not findings:
        print("  No namespace changes detected.")
    for f in findings:
        mark = "[!]" if f.verdict in _FLAGGED else "[ ]"
        if quiet and f.verdict in (Verdict.NO_AUTHORITY_IMPACT,):
            continue
        print(f"  {mark} [{f.verdict.value}] ({f.severity.value}) {f.namespace}")
        print(f"      {f.evidence}")
    print()
    flagged = [f for f in findings if f.verdict in _FLAGGED]
    insufficient = [f for f in findings if f.verdict == Verdict.INSUFFICIENT_EVIDENCE]
    print(f"  Summary: {len(findings)} finding(s); {len(flagged)} flagged; "
          f"{len(insufficient)} insufficient-evidence (binding gap).")
    print("  Mode: ADVISORY - exit 0 regardless of verdict (severity carried per finding).")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Namespace/Authority Drift Detector (advisory v1)")
    ap.add_argument("--base", default="origin/main", help="base ref (default origin/main)")
    ap.add_argument("--candidate", required=True, help="candidate ref to adjudicate")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--quiet", action="store_true", help="suppress NO_AUTHORITY_IMPACT lines")
    ap.add_argument(
        "--registry",
        default=None,
        help="optional path to authority_chain_registry.json (defaults to Luthiers ontology)",
    )
    args = ap.parse_args(argv)

    cfg = DEFAULT_CONFIG
    if args.registry:
        cfg = DetectorConfig(
            repo_root=cfg.repo_root,
            code_roots=cfg.code_roots,
            non_code_hints=cfg.non_code_hints,
            authority_artifact_paths=cfg.authority_artifact_paths,
            authority_registry_path=Path(args.registry),
        )

    topo = AuthorityTopology.load(config=cfg)
    change = build_candidate_change(args.base, args.candidate, config=cfg)
    findings = analyze_namespace_authority_drift(change, topo)
    _render(findings, change, args.json, args.quiet, config=cfg)
    # v1 ADVISORY: always exit 0. Severity is carried per finding for a future gate.
    return 0


if __name__ == "__main__":
    sys.exit(main())
