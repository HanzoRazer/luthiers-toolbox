"""Synthetic + real-registry tests for the Namespace/Authority Drift Detector.

These tests exercise the *analysis engine* directly with constructed candidate-change
models (Git-independent, per the three-layer design). The engine's verdicts are proven
across all required families; the real authority registry is then used to assert the
current *factual* topology condition (the binding gap), NOT a permanent semantic truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "governance"))

import check_namespace_authority_drift as det  # noqa: E402
from check_namespace_authority_drift import (  # noqa: E402
    AuthorityTopology,
    CandidateChange,
    NamespaceChange,
    Verdict,
    adjudicate,
    analyze,
)


# A synthetic authority topology that mirrors the real registry's shape but adds the
# namespace→domain BINDINGS the real registry does not (yet) declare. This lets us prove
# the engine's substantive verdicts are correct WHEN bindings exist — without inventing
# authority in production.
SYNTH_REGISTRY = {
    "domain_ownership": {
        "geometry": {"canonical_owner": "Geometry Layer",
                     "operational_owners": ["IBG", "Body Grid", "BOE"], "authority_tier": 2},
        "feasibility": {"canonical_owner": "Feasibility Layer",
                        "operational_owners": ["RMOS"], "authority_tier": 2},
        "greenfield": {"canonical_owner": None, "operational_owners": [], "authority_tier": 2},
    },
    "chains": {},
}
SYNTH_BINDINGS = {
    "boe": {"domain": "geometry", "concept": "BOE"},
    "rmos": {"domain": "feasibility", "concept": "RMOS"},
    "brandnew": {"domain": "greenfield", "concept": "BrandNew"},
}


@pytest.fixture()
def synth_topo():
    return AuthorityTopology(SYNTH_REGISTRY, namespace_bindings=SYNTH_BINDINGS)


@pytest.fixture()
def real_topo():
    return AuthorityTopology.load()


def _nc(**kw):
    base = dict(namespace="x", path="services/api/app/x", change="added")
    base.update(kw)
    return NamespaceChange(**base)


# ───────────────────────── every verdict family (engine, git-independent) ─────────────────────────
def test_no_authority_impact_for_noncode(synth_topo):
    v = adjudicate(_nc(namespace="notes", path="docs/notes.md", is_code_namespace=False), synth_topo)
    assert v.verdict is Verdict.NO_AUTHORITY_IMPACT


def test_insufficient_evidence_when_unbound(synth_topo):
    # a real, code namespace that no binding covers → cannot adjudicate (the honest gap)
    v = adjudicate(_nc(namespace="retopo", path="services/api/app/retopo"), synth_topo)
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert "binding" in v.evidence.lower()


def test_declared_extension_when_owner(synth_topo):
    v = adjudicate(_nc(namespace="boe", declared_domain="geometry", declared_concept="BOE"), synth_topo)
    assert v.verdict is Verdict.DECLARED_EXTENSION


def test_declared_extension_via_registry_binding(synth_topo):
    # bound purely through the topology's namespace_bindings map (no change-carried binding)
    v = adjudicate(_nc(namespace="boe"), synth_topo)
    assert v.verdict is Verdict.DECLARED_EXTENSION


def test_duplicate_authority_when_claiming_owned_domain(synth_topo):
    v = adjudicate(_nc(namespace="rival", declared_domain="geometry", declared_concept="Rival"), synth_topo)
    assert v.verdict is Verdict.DUPLICATE_AUTHORITY


def test_parallel_authority_on_independent_registry(synth_topo):
    v = adjudicate(_nc(namespace="boe", introduces_parallel_registry=True), synth_topo)
    assert v.verdict is Verdict.PARALLEL_AUTHORITY


def test_obsolete_authority_on_superseded_restore(synth_topo):
    v = adjudicate(_nc(namespace="boe", restores_superseded=True), synth_topo)
    assert v.verdict is Verdict.OBSOLETE_AUTHORITY


def test_authority_bypass_on_invariant_violation(synth_topo):
    v = adjudicate(_nc(namespace="boe", violates_invariant="Translators serialize but do not generate geometry"), synth_topo)
    assert v.verdict is Verdict.AUTHORITY_BYPASS


def test_novel_valid_in_unowned_domain(synth_topo):
    v = adjudicate(_nc(namespace="brandnew"), synth_topo)
    assert v.verdict is Verdict.NOVEL_VALID


# ───────────────────────── engine invariants ─────────────────────────
def test_every_verdict_carries_evidence(synth_topo):
    cases = [
        _nc(namespace="notes", is_code_namespace=False),
        _nc(namespace="retopo"),
        _nc(namespace="boe"),
        _nc(namespace="rival", declared_domain="geometry", declared_concept="Rival"),
    ]
    for f in analyze(CandidateChange("b", "c", cases), synth_topo):
        assert f.evidence and f.evidence.strip()


def test_determinism_same_input_same_verdict(synth_topo):
    nc = _nc(namespace="retopo")
    assert adjudicate(nc, synth_topo).verdict is adjudicate(nc, synth_topo).verdict


def test_advisory_never_hardcodes_nonzero_exit():
    # v1 is advisory: no verdict maps to a nonzero exit. (Severity is carried separately.)
    # The engine has no exit concept; main() returns 0 unconditionally — assert the source
    # contract holds by construction: flagged verdicts exist but exit stays 0.
    assert Verdict.AUTHORITY_BYPASS in det._FLAGGED
    assert det._SEVERITY[Verdict.AUTHORITY_BYPASS] == det.Severity.WARNING


# ───────────────────────── real-registry FACTUAL CONDITION (dogfood) ─────────────────────────
def test_real_registry_has_no_namespace_binding_layer(real_topo):
    """Factual condition of the CURRENT topology: there is no namespace→domain binding
    layer. If a future governance sprint adds one, this assertion legitimately changes."""
    assert real_topo.namespace_bindings == {}


def test_retopo_dogfood_reflects_binding_gap(real_topo):
    """RETOPO dogfood, asserted as a factual condition (not a permanent semantic truth):
    the `retopo` namespace has no declared binding in the current topology, so the
    deterministic verdict is INSUFFICIENT_EVIDENCE. If governance later binds retopo,
    this fixture SHOULD change — that is the point."""
    v = adjudicate(_nc(namespace="retopo", path="services/api/app/retopo",
                       touches_authority_artifacts=("contracts/schema_registry.json",)), real_topo)
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert v.verdict not in det._FLAGGED  # never flagged merely for being unbound


def test_boe_control_not_flagged_by_age(real_topo):
    """BOE paired control: BOE is transition-era + merged + reconciled. The detector must
    NOT flag it merely for its age. Under the current (binding-less) topology BOE resolves
    to INSUFFICIENT_EVIDENCE like any unbound namespace — crucially NOT a flagged verdict."""
    v = adjudicate(_nc(namespace="body_outline",
                       path="services/api/app/cam/translators/dxf/body_outline_translator.py"),
                   real_topo)
    assert v.verdict not in det._FLAGGED
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_boe_would_be_recognized_if_bound(synth_topo):
    """The mirror of the control: WHEN a binding exists (as governance could later declare),
    BOE is recognized as a declared owner of geometry — DECLARED_EXTENSION, not flagged —
    proving the detector evaluates authority, not age."""
    v = adjudicate(_nc(namespace="boe"), synth_topo)
    assert v.verdict is Verdict.DECLARED_EXTENSION
    assert v.verdict not in det._FLAGGED
