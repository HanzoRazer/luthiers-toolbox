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


# ───────────────────────── GIT ADAPTER (previously untested) ─────────────────────────
#
# Everything above exercises the Git-independent engine. The adapter — the layer that
# turns `git diff --name-status` rows into the candidate-change model — had no direct
# coverage, which is where a namespace-identity bug lived undetected: the aggregation
# key was the bare namespace segment, so unrelated trees merged into one finding.
#
# These drive build_candidate_change() through a stubbed _git so the parsing and
# aggregation are pinned without touching a real repository.


@pytest.fixture()
def fake_git(monkeypatch):
    """Return a helper that stubs the git layer with canned --name-status output."""

    def _run(diff_output: str):
        monkeypatch.setattr(det, "_git", lambda args: diff_output)
        return det.build_candidate_change("base", "candidate")

    return _run


def _by_path(change):
    return {nc.path: nc for nc in change.namespace_changes}


def test_adapter_does_not_merge_same_named_namespaces_from_different_roots(fake_git):
    """CODE_ROOTS holds both 'services/api/app/' and 'services/', so the segment 'foo'
    is ambiguous. Two unrelated trees must stay two findings.

    Regression: keying aggregation on the bare segment collapsed them into ONE finding
    whose change type was the synthesised union of an add and a delete ('modified'),
    and whose path pointed at only one of the two trees.
    """
    change = fake_git(
        "A\tservices/api/app/foo/new.py\n"
        "D\tservices/foo/old.py\n"
    )

    assert len(change.namespace_changes) == 2, (
        "unrelated trees sharing a segment name were merged into one finding"
    )
    by_path = _by_path(change)
    assert by_path["services/api/app/foo"].change == "added"
    assert by_path["services/foo"].change == "removed"
    # both still report the same namespace identifier — that is expected and factual
    assert {nc.namespace for nc in change.namespace_changes} == {"foo"}


def test_adapter_reconstructs_the_path_from_the_matched_root(fake_git):
    """The emitted path must reflect the root that actually matched.

    Regression: the path was built from CODE_ROOTS[0] unconditionally, so a change
    under 'services/' was reported at a 'services/api/app/...' path that does not exist.
    """
    change = fake_git("M\tservices/blueprint-import/vectorizer_phase3.py\n")
    (nc,) = change.namespace_changes
    assert nc.namespace == "blueprint-import"
    assert nc.path == "services/blueprint-import"


def test_adapter_keeps_a_same_namespace_rename_as_one_modified_finding(fake_git):
    change = fake_git(
        "R100\tservices/api/app/foo/a.py\tservices/api/app/foo/b.py\n"
    )
    (nc,) = change.namespace_changes
    assert (nc.namespace, nc.change) == ("foo", "modified")


def test_adapter_surfaces_both_sides_of_a_namespace_move(fake_git):
    """A rename that moves code between namespaces must show the vacated source.

    Regression: only the last tab-separated field was read, so the source namespace
    never appeared and a move looked like an unexplained addition.
    """
    change = fake_git(
        "R100\tservices/api/app/foo/a.py\tservices/api/app/bar/a.py\n"
    )
    by_ns = {nc.namespace: nc for nc in change.namespace_changes}
    assert set(by_ns) == {"foo", "bar"}
    assert by_ns["foo"].change == "removed"
    assert by_ns["bar"].change == "added"


def test_adapter_treats_a_copy_as_destination_only(fake_git):
    """Unlike a rename, a copy leaves the source in place — it must not report a removal."""
    change = fake_git(
        "C75\tservices/api/app/foo/a.py\tservices/api/app/baz/a.py\n"
    )
    by_ns = {nc.namespace: nc for nc in change.namespace_changes}
    assert set(by_ns) == {"baz"}
    assert by_ns["baz"].change == "added"


def test_adapter_emits_no_empty_code_namespace(fake_git):
    """A bare root path names no namespace and must not adjudicate as a code namespace.

    Regression: 'services/api/app/' produced namespace '' with is_code_namespace=True,
    yielding INSUFFICIENT_EVIDENCE for a namespace that does not exist.
    """
    change = fake_git("A\tservices/api/app/\n")
    for nc in change.namespace_changes:
        assert not (nc.is_code_namespace and not nc.namespace), (
            "emitted an empty code namespace"
        )


def test_adapter_records_touched_authority_artifacts(fake_git):
    change = fake_git(
        "M\tdocs/governance/ontology/authority_chain_registry.json\n"
    )
    (nc,) = change.namespace_changes
    assert nc.touches_authority_artifacts == (
        "docs/governance/ontology/authority_chain_registry.json",
    )


def test_authority_artifact_edits_are_surfaced_not_swallowed(fake_git, real_topo):
    """Editing the authority registry is the most authority-relevant change there is.

    The verdict stays NO_AUTHORITY_IMPACT — a docs/config edit introduces no code
    namespace, and promoting it on the strength of a file path would be the very
    inference this detector forbids. But the touched artifact MUST reach the operator.

    Regression: touches_authority_artifacts was collected and then dropped on the
    non-code branch, so this rendered as a bare "no code namespace" line.
    """
    change = fake_git(
        "M\tdocs/governance/ontology/authority_chain_registry.json\n"
        "M\tcontracts/schema_registry.json\n"
    )
    findings = analyze(change, real_topo)

    assert findings, "no findings produced"
    for f in findings:
        assert f.verdict is Verdict.NO_AUTHORITY_IMPACT
    surfaced = " ".join(f.evidence for f in findings)
    assert "authority_chain_registry.json" in surfaced
    assert "schema_registry.json" in surfaced


def test_adapter_ignores_blank_and_malformed_rows(fake_git):
    """Defensive: blank lines and a status-only row must not raise or fabricate entries."""
    change = fake_git("\n" "   \n" "A\n" "M\tservices/api/app/foo/a.py\n")
    assert [nc.namespace for nc in change.namespace_changes] == ["foo"]


def test_adapter_surfaces_source_side_evidence_when_authority_artifact_is_renamed(fake_git):
    """Renaming a declared authority artifact away from its canonical path must still
    record the *source* path as touched — that is the declared artifact that moved.

    Without an explicit pin, destination-only recording would drop the only path that
    is in AUTHORITY_ARTIFACT_PATHS whenever the file is renamed to a non-canonical name.
    """
    old = "docs/governance/ontology/authority_chain_registry.json"
    new = "docs/governance/ontology/authority_chain_MOVED.json"
    change = fake_git(f"R100\t{old}\t{new}\n")
    (nc,) = change.namespace_changes
    assert nc.change == "modified"  # delete+add in the same non-code namespace
    assert old in nc.touches_authority_artifacts
    assert new not in nc.touches_authority_artifacts


def test_adapter_surfaces_source_artifact_when_authority_artifact_is_copied(fake_git):
    """A copy leaves the source file in place, so _parse_name_status emits destination
    only. The source is still a declared authority artifact and must appear in evidence
    on the destination finding — otherwise copy silently under-reports artifact touch.
    """
    src = "docs/governance/ontology/authority_chain_registry.json"
    dst = "docs/governance/ontology/authority_chain_COPY.json"
    change = fake_git(f"C100\t{src}\t{dst}\n")
    (nc,) = change.namespace_changes
    assert nc.change == "added"
    assert src in nc.touches_authority_artifacts


def test_under_code_root_requires_path_boundary(monkeypatch):
    """Classification must not treat a textual prefix as a directory root."""
    # Simulate a future mis-edit that drops the trailing slash — import-time guard
    # already rejects that for CODE_ROOTS; the helper itself must still refuse.
    with pytest.raises(ValueError):
        det._under_code_root("services/foo/bar.py", "services")

    assert det._under_code_root("services/foo/bar.py", "services/") is True
    assert det._under_code_root("services_backup/foo/bar.py", "services/") is False
    assert det._under_code_root("services", "services/") is True


def test_non_code_hints_match_path_segments_not_substrings():
    """'test' as a segment hint must not fire inside 'contest' or 'testdata'."""
    assert det._has_non_code_hint("docs/governance/ontology/x.md") is True
    assert det._has_non_code_hint("foo/tests/unit/x.py") is True
    assert det._has_non_code_hint("contracts/schema_registry.json") is True
    assert det._has_non_code_hint("vendor/contest/runner.py") is False
    assert det._has_non_code_hint("src/testdata/runner.py") is False
    assert det._has_non_code_hint("services/api/app/mydocs/tool.py") is False


def test_authority_artifact_evidence_string_is_sorted_not_list_repr(fake_git, real_topo):
    """Operator-facing evidence must list artifacts as a stable comma-separated string."""
    change = fake_git(
        "M\tdocs/governance/ontology/authority_chain_registry.json\n"
        "M\tcontracts/schema_registry.json\n"
    )
    findings = analyze(change, real_topo)
    surfaced = " ".join(f.evidence for f in findings)
    assert "['" not in surfaced and '["' not in surfaced
    assert "authority_chain_registry.json" in surfaced
    assert "schema_registry.json" in surfaced
