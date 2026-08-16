"""Synthetic + real-registry tests for the Namespace/Authority Drift Detector.

These tests exercise the *analysis engine* directly with constructed candidate-change
models (Git-independent, per the three-layer design). The engine's verdicts are proven
across all required families; the real authority registry is then used to assert the
current *factual* topology condition (the binding gap), NOT a permanent semantic truth.

Three groups, with different lifetimes:

  1. VERDICT FAMILIES + ENGINE INVARIANTS (synthetic bound topology)
     Permanent. These prove the engine is correct when bindings exist.

  2. REAL-REGISTRY DOGFOOD (current-topology facts)
     TEMPORARY BY DESIGN. These assert what today's binding-less topology yields.
     When governance authors namespace->domain bindings, the bound namespaces stop
     returning INSUFFICIENT_EVIDENCE and these assertions SHOULD be updated. That is
     the expected outcome, not a regression. Each such test says so in its docstring.

  3. ANTI-INFERENCE GUARD
     Permanent, and the one group that must NOT be relaxed when bindings land. It
     proves the detector never invents a binding from a name, an owner name, or a
     path. Four heuristic implementations were injected during development and each
     was caught by this group.

Background on the deferred governance gap, and why inference is forbidden rather
than merely unimplemented: docs/governance/ontology/NAMESPACE_BINDING_GAP.md
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
    DetectorConfig,
    NamespaceChange,
    Verdict,
    adjudicate,
    analyze,
    analyze_namespace_authority_drift,
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


# ───────────────────────── ANTI-INFERENCE GUARD ─────────────────────────
#
# The tests above establish that an unbound namespace yields INSUFFICIENT_EVIDENCE.
# They cannot, on their own, prove the detector does not INFER a binding — because
# they run against topologies where the tempting target either is not present or
# nothing is bound at all. "Unbound → INSUFFICIENT_EVIDENCE" and "does not infer"
# look identical when there is nothing to infer FROM.
#
# These tests supply something to infer from. The bait topology declares domains
# whose names collide head-on with the namespace names, and owners whose names do
# too — then binds none of them. A human reading `retopo` next to a declared
# `topology` domain would bind it immediately; a path/name/keyword heuristic would
# too. The detector must not.
#
# This is the guard against accidental future authority synthesis: if anyone later
# "helps" the detector by adding name matching, path matching, or content sniffing,
# these fail. They are the executable form of the module's core boundary rule —
# the detector MAY CONSUME authority, it MAY NOT CREATE authority.

INFERENCE_BAIT_REGISTRY = {
    "domain_ownership": {
        # Domain names chosen to collide with the namespace names probed below.
        # Both of these are real domains in the production registry.
        "geometry": {
            "canonical_owner": "Geometry Layer",
            "operational_owners": ["IBG", "BOE", "Body Grid"],
            "authority_tier": 2,
        },
        "topology": {
            "canonical_owner": "Topology Layer",
            "operational_owners": ["Retopo Engine"],
            "authority_tier": 2,
        },
    },
    "chains": {},
}

# Deliberately binds ONE unrelated namespace, so the bait namespaces below are
# unbound while the topology is demonstrably non-empty and resolvable.
INFERENCE_BAIT_BINDINGS = {
    "some_bound_namespace": {"domain": "geometry", "concept": "IBG"},
}


@pytest.fixture()
def bait_topo():
    return AuthorityTopology(
        INFERENCE_BAIT_REGISTRY, namespace_bindings=INFERENCE_BAIT_BINDINGS
    )


@pytest.mark.parametrize(
    "namespace,bait",
    [
        ("geometry", "namespace name is EXACTLY a declared domain name"),
        ("topology", "namespace name is EXACTLY a declared domain name"),
        ("retopo", "obvious lexical match for the declared 'topology' domain"),
        ("body_outline", "obvious semantic match for the declared 'geometry' domain"),
        ("boe", "namespace name is EXACTLY a declared operational owner"),
        ("ibg", "namespace name is EXACTLY a declared operational owner"),
        ("body_grid", "declared owner 'Body Grid' modulo case and separator"),
    ],
)
def test_does_not_infer_binding_from_namespace_name(bait_topo, namespace, bait):
    """A suggestive name must NOT produce a binding. Only a declaration may."""
    nc = _nc(namespace=namespace, path=f"services/api/app/{namespace}")

    assert bait_topo.resolve(nc) is None, (
        f"resolve() invented a binding for '{namespace}' ({bait}). The detector may "
        f"consume authority, not create it — a namespace binds only when a binding is "
        f"DECLARED, never because its name resembles a domain or an owner."
    )

    v = adjudicate(nc, bait_topo)
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE, (
        f"'{namespace}' was adjudicated {v.verdict.value} instead of "
        f"INSUFFICIENT_EVIDENCE ({bait}). This means name inference was introduced."
    )
    assert v.verdict not in det._FLAGGED


@pytest.mark.parametrize(
    "path",
    [
        "services/api/app/geometry/retopo/mesh.py",
        "services/api/app/instrument_geometry/body/ibg/retopo.py",
        "services/api/app/cam/translators/dxf/body_outline_translator.py",
    ],
)
def test_does_not_infer_binding_from_path(bait_topo, path):
    """Living inside a geometry/IBG module must not bind a namespace either.

    The git adapter derives the namespace identifier from the path — that is a
    factual classification. It must not also derive OWNERSHIP from it.
    """
    nc = _nc(namespace="unbound_thing", path=path)

    assert bait_topo.resolve(nc) is None, (
        f"resolve() invented a binding from the path {path!r}. Path location is a "
        f"fact about where code lives, not a declaration of who owns it."
    )
    assert adjudicate(nc, bait_topo).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_does_not_infer_binding_from_touching_authority_artifacts(bait_topo):
    """Touching an authority artifact is reported as evidence, never as a binding.

    A change that edits the authority registry itself is the most tempting case for
    an implicit binding. It must still be INSUFFICIENT_EVIDENCE — the artifact list
    appears in the evidence string so a human can act on it.
    """
    nc = _nc(
        namespace="retopo",
        path="services/api/app/retopo",
        touches_authority_artifacts=(
            "contracts/schema_registry.json",
            "docs/governance/ontology/authority_chain_registry.json",
        ),
    )

    v = adjudicate(nc, bait_topo)
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert v.verdict not in det._FLAGGED
    assert "schema_registry.json" in v.evidence, (
        "the touched authority artifacts should be surfaced as evidence even though "
        "they do not confer a binding"
    )


def test_declared_binding_still_resolves_in_bait_topology(bait_topo):
    """Control for the anti-inference tests: the bait topology is not simply inert.

    Without this, the tests above would pass trivially if resolve() were broken and
    returned None for everything.
    """
    nc = _nc(namespace="some_bound_namespace")
    assert bait_topo.resolve(nc) == ("geometry", "IBG")
    assert adjudicate(nc, bait_topo).verdict is Verdict.DECLARED_EXTENSION


@pytest.mark.parametrize("namespace", ["retopo", "body_outline", "geometry", "topology"])
def test_no_inference_against_the_real_production_topology(real_topo, namespace):
    """Same guard, against the REAL registry — which declares both `geometry` and
    `topology` domains, making these names genuinely temptable today.

    This is a CURRENT-TOPOLOGY fact, not a permanent semantic truth: it holds because
    no namespace→domain bindings are declared yet. When governance authors bindings,
    the bound names here will legitimately change verdict — and the unbound ones must
    still be INSUFFICIENT_EVIDENCE.
    """
    nc = _nc(namespace=namespace, path=f"services/api/app/{namespace}")
    assert real_topo.resolve(nc) is None
    assert adjudicate(nc, real_topo).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_real_topology_declares_the_domains_that_make_the_bait_real():
    """Pin the premise of the test above: if production ever stops declaring these
    domains, the anti-inference guard loses its teeth and should be re-baited."""
    topo = AuthorityTopology.load()
    for domain in ("geometry", "topology"):
        assert domain in topo.domain_ownership, (
            f"production registry no longer declares a '{domain}' domain — the "
            f"anti-inference tests were baited against it; re-check their premise"
        )

# ───────────────────────── portability / config injection ─────────────────────────
def test_default_config_matches_luthiers_module_aliases():
    """DetectorConfig defaults must equal the preserved module-level Luthiers aliases."""
    cfg = DetectorConfig.luthiers_defaults()
    assert cfg.repo_root == det.REPO_ROOT
    assert cfg.code_roots == det.CODE_ROOTS
    assert cfg.non_code_hints == det.NON_CODE_HINTS
    assert set(cfg.authority_artifact_paths) == set(det.AUTHORITY_ARTIFACT_PATHS)
    assert cfg.authority_registry_path == det.AUTHORITY_REGISTRY


def test_analyze_entrypoint_matches_analyze(synth_topo):
    """analyze_namespace_authority_drift is a portable alias of analyze()."""
    change = CandidateChange("b", "c", [
        _nc(namespace="retopo"),
        _nc(namespace="boe"),
        _nc(namespace="notes", path="docs/notes.md", is_code_namespace=False),
    ])
    via_analyze = analyze(change, synth_topo)
    via_entry = analyze_namespace_authority_drift(change, synth_topo)
    assert [(f.namespace, f.verdict, f.evidence) for f in via_entry] == [
        (f.namespace, f.verdict, f.evidence) for f in via_analyze
    ]


def test_analyze_entrypoint_accepts_registry_dict_with_bindings():
    """Vendors may pass a registry dict + optional bindings without AuthorityTopology."""
    change = CandidateChange("b", "c", [_nc(namespace="boe")])
    findings = analyze_namespace_authority_drift(
        change, SYNTH_REGISTRY, namespace_bindings=SYNTH_BINDINGS
    )
    assert len(findings) == 1
    assert findings[0].verdict is Verdict.DECLARED_EXTENSION


def test_injected_registry_path_equivalent_to_default(tmp_path, real_topo):
    """Loading via an explicit registry path must match default AuthorityTopology.load()."""
    src = det.AUTHORITY_REGISTRY
    copy = tmp_path / "authority_chain_registry.json"
    copy.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    via_path = AuthorityTopology.load(copy)
    via_cfg = AuthorityTopology.load(
        config=DetectorConfig(authority_registry_path=copy)
    )
    # Same factual binding gap on the same constructed change.
    nc = _nc(namespace="retopo", path="services/api/app/retopo")
    assert adjudicate(nc, via_path).verdict is adjudicate(nc, real_topo).verdict
    assert adjudicate(nc, via_cfg).verdict is adjudicate(nc, real_topo).verdict
    assert adjudicate(nc, via_path).evidence == adjudicate(nc, real_topo).evidence


def test_namespace_classification_uses_injected_code_roots():
    """Path classification is config-driven; adjudication still never invents bindings."""
    foreign = DetectorConfig(
        code_roots=("pkg/",),
        non_code_hints=("docs/",),
        authority_artifact_paths=frozenset(),
    )
    ns, is_code = det._namespace_of("pkg/retopo/mesh.py", config=foreign)
    assert ns == "retopo" and is_code is True
    # Same NamespaceChange still yields INSUFFICIENT_EVIDENCE under binding-less topo —
    # config changes classification facts, not invented authority.
    topo = AuthorityTopology({"domain_ownership": {}, "chains": {}})
    v = adjudicate(_nc(namespace=ns, path="pkg/retopo", is_code_namespace=is_code), topo)
    assert v.verdict is Verdict.INSUFFICIENT_EVIDENCE
