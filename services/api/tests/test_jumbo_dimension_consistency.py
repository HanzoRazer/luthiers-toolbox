"""
Jumbo Dimension Consistency Test

Verifies that jumbo body dimensions are consistent across every artifact in the
codebase that asserts them.

This is symptom mitigation — the architectural problem is duplicated facts that
can drift. "Single source of truth for body-family dimensions" is a future
canonicalization item.

WHY THE COVERAGE MATTERS
------------------------
This test originally guarded four paths. Two others asserted jumbo dimensions
and were not checked — the Body Outline Editor User Manual and the tools/
mirror of the editor. When commit f25bb949 (2026-05-27) realigned jumbo to the
canonical source, those two were missed, and the drift was invisible to CI for
81 days until it was found by hand on 2026-08-16.

The lesson is structural, not incidental: a consistency guard has to enumerate
its namespace, not a subset of it. Drift hides in the members nobody checks.
So this file now does two things:

  1. Asserts every known definition path against the canonical source.
  2. Fails when a NEW artifact starts asserting jumbo dimensions without being
     declared here — see TestJumboNamespaceCompleteness.

If you add an artifact that hardcodes jumbo body dimensions, add it to
DECLARED_JUMBO_ARTIFACTS and give it a test in the same change.

PATHS CHECKED
-------------
1. IBG FAMILY_DEFAULTS["jumbo"] — body_contour_solver.py (CANONICAL)
2. jumbo_j200.py MODEL_INFO
3. instrument_model_registry.json jumbo_j200.body_dimensions_mm
4. hostinger/body-outline-editor.html INSTRUMENT_TEMPLATES.jumbo
5. docs/Body_Outline_Editor_User_Manual.md Chapter 7 template table
6. tools/body-outline-editor.html INSTRUMENT_TEMPLATES.jumbo  (xfail — stale)
7. instrument_body_generator.py INSTRUMENT_SPECS["jumbo"]["expected_dimensions"]

NOT CHECKED (documented, out of scope)
--------------------------------------
- catalog.json "jumbo" — a DXF bounding box, and a demonstrably bad one.
  See TestCatalogJsonOutOfScope for the diagnosis.
"""

import json
import re
from pathlib import Path

import pytest


# Canonical jumbo dimensions (from IBG FAMILY_DEFAULTS)
CANONICAL_JUMBO = {
    "lower_bout_mm": 432.0,
    "upper_bout_mm": 305.0,
    "waist_mm": 254.0,
    "body_length_mm": 530.0,
    "waist_y_norm": 0.44,
}

API_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = API_ROOT.parent.parent


# ─── Namespace declaration ────────────────────────────────────────────────────
#
# Every artifact that asserts jumbo BODY DIMENSIONS. Repo-relative, forward
# slashes. TestJumboNamespaceCompleteness fails if something outside this set
# starts asserting them.

DECLARED_JUMBO_ARTIFACTS = {
    "services/api/app/instrument_geometry/body/ibg/body_contour_solver.py",
    "services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py",
    "services/api/app/instrument_geometry/guitars/jumbo_j200.py",
    "services/api/app/instrument_geometry/instrument_model_registry.json",
    "hostinger/body-outline-editor.html",
    "tools/body-outline-editor.html",
    "docs/Body_Outline_Editor_User_Manual.md",
}

# Files that mention jumbo alongside canonical-looking numbers but do NOT
# assert body dimensions. Each entry needs a reason — this is not a dumping
# ground for scan noise.
ACKNOWLEDGED_NON_DIMENSION_FILES = {
    # Tests, including this one.
    "services/api/tests/test_jumbo_dimension_consistency.py":
        "This file. Holds the canonical values by definition.",
    "services/api/tests/test_jumbo_family_regression.py":
        "Sibling test. Independently hardcodes the same canonical values — see "
        "test_sibling_regression_test_agrees_with_canonical below.",

    # Different facet of the namespace, not the four body dimensions.
    "services/api/app/instrument_geometry/body/body_outlines.json":
        "Outline point cloud, not named dimensions.",
    "services/api/app/instrument_geometry/body/catalog.json":
        "DXF bounding boxes, not body dimensions. See TestCatalogJsonOutOfScope.",

    # Coincidental matches.
    "services/api/app/calculators/nut_slot_calc.py":
        "'jumbo' here is a fret-wire gauge, unrelated to body geometry.",

    # Documentation that discusses the drift, including superseded values.
    "docs/Body_Outline_Editor_CHANGELOG.md":
        "Historical record. Deliberately cites the superseded 304/280 values, "
        "so it must not be asserted against canonical.",
    "docs/handoffs/BOE_BUILD_RESUMPTION_DEV_HANDOFF_2026-08-16.md":
        "Build handoff. Quotes canonical dimensions alongside the mismatched "
        "dreadnought and stratocaster template values while documenting the drift; "
        "asserting it against canonical would defeat its purpose.",
    "docs/handoffs/BODY_OUTLINE_EDITOR_V2_HANDOFF.md":
        "Historical handoff narrative.",
    "docs/handoffs/IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT_2026-05-11.md":
        "Point-in-time assessment.",
    "SPRINTS.md":
        "Sprint ledger narrative.",
    ".cbsp21/patches/boe-changelog.json":
        "CBSP21 manifest describing the drift.",
}


# ─── Shared parsers ───────────────────────────────────────────────────────────

def _parse_editor_template(path: Path) -> dict:
    """Extract INSTRUMENT_TEMPLATES.jumbo dimensions from a Body Outline Editor HTML file."""
    content = path.read_text(encoding="utf-8")

    match = re.search(r"jumbo:\s*\{[^}]*dimensions:\s*\{([^}]+)\}", content)
    assert match, f"Could not find jumbo template in {path.name}"
    dims_str = match.group(1)

    def value(key):
        m = re.search(rf"{key}:\s*(\d+(?:\.\d+)?)", dims_str)
        return float(m.group(1)) if m else None

    return {
        "lower_bout_mm": value("lowerBout"),
        "upper_bout_mm": value("upperBout"),
        "waist_mm": value("waist"),
        "body_length_mm": value("bodyLength"),
        "waist_y_norm": value("waistYNorm"),
    }


def _assert_matches_canonical(actual: dict, source: str, keys=None):
    keys = keys or ("lower_bout_mm", "upper_bout_mm", "waist_mm", "body_length_mm")
    for key in keys:
        assert actual[key] == CANONICAL_JUMBO[key], (
            f"{source}: {key} is {actual[key]}, canonical is {CANONICAL_JUMBO[key]}. "
            f"Canonical source is FAMILY_DEFAULTS['jumbo'] in body_contour_solver.py."
        )


class TestJumboDimensionConsistency:
    """Consistency check across every declared jumbo definition path."""

    def test_ibg_family_defaults_canonical(self):
        """Path 1: IBG FAMILY_DEFAULTS is the canonical source."""
        from app.instrument_geometry.body.ibg.body_contour_solver import (
            FAMILY_DEFAULTS,
        )

        jumbo = FAMILY_DEFAULTS["jumbo"]

        assert jumbo["lower_bout_mm"] == CANONICAL_JUMBO["lower_bout_mm"]
        assert jumbo["upper_bout_mm"] == CANONICAL_JUMBO["upper_bout_mm"]
        assert jumbo["waist_mm"] == CANONICAL_JUMBO["waist_mm"]
        assert jumbo["body_length_mm"] == CANONICAL_JUMBO["body_length_mm"]
        assert jumbo["waist_y_norm"] == CANONICAL_JUMBO["waist_y_norm"]

    def test_jumbo_j200_model_matches_canonical(self):
        """Path 2: jumbo_j200.py MODEL_INFO matches canonical."""
        from app.instrument_geometry.guitars.jumbo_j200 import MODEL_INFO

        _assert_matches_canonical(MODEL_INFO, "jumbo_j200.py MODEL_INFO")
        assert MODEL_INFO["ibg_family"] == "jumbo"

    def test_instrument_registry_matches_canonical(self):
        """Path 3: instrument_model_registry.json matches canonical."""
        registry_path = (
            API_ROOT / "app" / "instrument_geometry" / "instrument_model_registry.json"
        )

        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)

        jumbo = registry["models"]["jumbo_j200"]
        dims = jumbo["body_dimensions_mm"]

        assert jumbo["ibg_family"] == "jumbo"
        assert dims["lower_bout"] == CANONICAL_JUMBO["lower_bout_mm"]
        assert dims["upper_bout"] == CANONICAL_JUMBO["upper_bout_mm"]
        assert dims["waist"] == CANONICAL_JUMBO["waist_mm"]
        assert dims["body_length"] == CANONICAL_JUMBO["body_length_mm"]

    def test_body_outline_editor_matches_canonical(self):
        """Path 4: hostinger/ Body Outline Editor INSTRUMENT_TEMPLATES matches canonical."""
        editor_path = REPO_ROOT / "hostinger" / "body-outline-editor.html"

        dims = _parse_editor_template(editor_path)

        _assert_matches_canonical(dims, "hostinger/body-outline-editor.html")
        assert dims["waist_y_norm"] == CANONICAL_JUMBO["waist_y_norm"]

    def test_user_manual_matches_canonical(self):
        """Path 5: User Manual Chapter 7 template table matches canonical.

        The manual states dimensions in prose, in length/lower/upper/waist order:

            - Jumbo — 530/432/305/254

        This path was unguarded when f25bb949 realigned jumbo, which is how the
        manual carried a 26mm waist error for 81 days.
        """
        manual_path = REPO_ROOT / "docs" / "Body_Outline_Editor_User_Manual.md"
        content = manual_path.read_text(encoding="utf-8")

        # Match the Chapter 7 bullet. The em-dash separator is part of the format.
        match = re.search(
            r"^-\s*Jumbo\s*[—-]\s*(\d+)/(\d+)/(\d+)/(\d+)",
            content,
            re.MULTILINE,
        )
        assert match, (
            "Could not find the Jumbo row in User Manual Chapter 7. Expected a line "
            "like '- Jumbo — 530/432/305/254'. If the table format changed, update "
            "this parser."
        )

        body_length, lower_bout, upper_bout, waist = (float(g) for g in match.groups())

        _assert_matches_canonical(
            {
                "body_length_mm": body_length,
                "lower_bout_mm": lower_bout,
                "upper_bout_mm": upper_bout,
                "waist_mm": waist,
            },
            "User Manual Chapter 7 (order is length/lower/upper/waist)",
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "tools/body-outline-editor.html is a KNOWN-STALE mirror: a clean, "
            "unmodified snapshot of hostinger/ at commit 70a0d3ee (2026-05-12), "
            "171 lines behind and missing f25bb949's jumbo realignment. "
            "MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md marks it Production / MEDIUM / "
            "'Avoid collision', so resyncing it is a governed change that needs its "
            "own approval and must not ride along with a test or docs change. "
            "strict=True is deliberate: when the resync lands this test will XPASS "
            "and fail the suite, forcing this marker to be removed in the same "
            "change. That is the intended handshake, not a bug."
        ),
    )
    def test_tools_mirror_matches_canonical(self):
        """Path 6: tools/ mirror of the Body Outline Editor matches canonical.

        Expected to fail until the governed resync lands. See the xfail reason.
        """
        mirror_path = REPO_ROOT / "tools" / "body-outline-editor.html"

        dims = _parse_editor_template(mirror_path)

        _assert_matches_canonical(dims, "tools/body-outline-editor.html")
        assert dims["waist_y_norm"] == CANONICAL_JUMBO["waist_y_norm"]

    def test_instrument_body_generator_matches_canonical(self):
        """Path 7: instrument_body_generator.py INSTRUMENT_SPECS expected_dimensions.

        Found by the namespace scan below, not by hand — it was an undeclared,
        unguarded duplicate of the canonical values.
        """
        from app.instrument_geometry.body.ibg.instrument_body_generator import (
            INSTRUMENT_SPECS,
        )

        spec = INSTRUMENT_SPECS["jumbo"]
        assert spec["family"] == "jumbo"

        _assert_matches_canonical(
            spec["expected_dimensions"],
            "instrument_body_generator.py INSTRUMENT_SPECS['jumbo']",
        )

    def test_sibling_regression_test_agrees_with_canonical(self):
        """test_jumbo_family_regression.py hardcodes the same values independently.

        Two test files asserting the same canonical constant from separate literals
        is itself a drift risk. This pins them together so a change to one is caught.
        """
        sibling = API_ROOT / "tests" / "test_jumbo_family_regression.py"
        content = sibling.read_text(encoding="utf-8")

        for key, value in CANONICAL_JUMBO.items():
            if key == "waist_y_norm":
                continue  # the sibling does not assert this field
            literal = f"{value}"
            assert literal in content, (
                f"test_jumbo_family_regression.py no longer contains {key}={literal}. "
                f"Either it drifted from canonical, or it was refactored to import "
                f"CANONICAL_JUMBO — if the latter, drop this test."
            )


class TestJumboNamespaceCompleteness:
    """Fail when a new artifact starts asserting jumbo dimensions undeclared.

    This is the durable half of the fix. Guarding seven paths is only correct
    until someone adds an eighth.
    """

    SCAN_ROOTS = [
        "services/api/app",
        "services/api/tests",
        "hostinger",
        "tools",
        "docs",
        ".cbsp21",
    ]
    SCAN_EXTENSIONS = (".py", ".json", ".html", ".md", ".ts", ".vue", ".js")
    SKIP_DIR_NAMES = {
        ".git", ".venv", "node_modules", "__pycache__", "htmlcov", "dist",
        ".mypy_cache", ".pytest_cache", "site-packages", "archive",
    }
    # A file is a candidate if it mentions jumbo and carries at least three of
    # the four canonical magnitudes. Three of four keeps the signal while
    # tolerating a file that legitimately omits one.
    CANONICAL_MAGNITUDES = ["530", "432", "305", "254"]
    MIN_MAGNITUDE_HITS = 3

    def _scan(self):
        found = set()
        for root_name in self.SCAN_ROOTS:
            root = REPO_ROOT / root_name
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in self.SCAN_EXTENSIONS:
                    continue
                if any(part in self.SKIP_DIR_NAMES for part in path.parts):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if "jumbo" not in text.lower():
                    continue
                hits = sum(1 for m in self.CANONICAL_MAGNITUDES if m in text)
                if hits >= self.MIN_MAGNITUDE_HITS:
                    rel = path.relative_to(REPO_ROOT).as_posix()
                    found.add(rel)
        return found

    def test_no_undeclared_jumbo_dimension_artifacts(self):
        """Every candidate must be either guarded or explicitly acknowledged."""
        found = self._scan()
        known = DECLARED_JUMBO_ARTIFACTS | set(ACKNOWLEDGED_NON_DIMENSION_FILES)

        undeclared = sorted(found - known)

        assert not undeclared, (
            "These files mention jumbo alongside canonical body dimensions but are "
            "neither guarded nor acknowledged:\n  "
            + "\n  ".join(undeclared)
            + "\n\nIf a file asserts jumbo BODY DIMENSIONS, add it to "
            "DECLARED_JUMBO_ARTIFACTS and write a test for it. If it only mentions "
            "jumbo incidentally, add it to ACKNOWLEDGED_NON_DIMENSION_FILES with a "
            "reason. Do not widen the scan filters to make this pass."
        )

    def test_declared_artifacts_all_exist(self):
        """A declared path that no longer exists means the declaration is stale."""
        missing = sorted(
            p for p in DECLARED_JUMBO_ARTIFACTS if not (REPO_ROOT / p).exists()
        )
        assert not missing, (
            "Declared jumbo definition paths that do not exist:\n  "
            + "\n  ".join(missing)
            + "\n\nRemove them from DECLARED_JUMBO_ARTIFACTS along with their tests."
        )

    def test_acknowledged_files_have_reasons(self):
        """Acknowledgements must carry a non-trivial reason."""
        thin = sorted(
            path for path, reason in ACKNOWLEDGED_NON_DIMENSION_FILES.items()
            if not reason or len(reason) < 20
        )
        assert not thin, (
            "These acknowledgements need a real reason, not a placeholder:\n  "
            + "\n  ".join(thin)
        )


class TestCatalogJsonOutOfScope:
    """catalog.json 'jumbo' is a DXF bounding box — and a bad one.

    DIAGNOSIS (2026-08-16). Previously logged as "needs investigation"; the
    investigation is done and recorded here.

    catalog.json stores DXF-extracted bounding boxes as {width, height}. For its
    siblings those track the nominal dimensions with the small positive margin a
    bounding box should have:

        dreadnought   w/lower_bout 1.025   h/body_length 1.004
        classical     w/lower_bout 1.025   h/body_length 1.017

    jumbo does not:

        jumbo         w/lower_bout 1.098   h/body_length 0.727

    But swapping the axes makes it coherent, at a consistent scale:

        jumbo         w/body_length 0.895  h/lower_bout 0.891

    So acoustic/Jumbo_body.dxf appears to be rotated 90 degrees relative to the
    other extractions AND uniformly scaled to roughly 89.3% of nominal. That is a
    defect in the DXF extraction, not a dimension that should be aligned to
    canonical — aligning it would paper over a bad source asset.

    Out of scope here: this test file guards named body dimensions, and fixing a
    rotated/scaled DXF is a separate geometry change.
    """

    @pytest.mark.skip(
        reason=(
            "catalog.json 'jumbo' is a DXF bounding box that is axis-swapped and "
            "~10.7% undersized relative to canonical — a source-asset defect, not "
            "a dimension to align. Diagnosis in the class docstring."
        )
    )
    def test_catalog_json_jumbo_dimensions(self):
        pass

    def test_catalog_json_diagnosis_still_holds(self):
        """Pin the diagnosis so it fails loudly if catalog.json is regenerated."""
        catalog_path = (
            API_ROOT / "app" / "instrument_geometry" / "body" / "catalog.json"
        )
        with open(catalog_path, encoding="utf-8") as f:
            catalog = json.load(f)

        jumbo = catalog["bodies"]["jumbo"]["dimensions_mm"]

        assert jumbo["width"] == pytest.approx(474.2, abs=0.1), (
            "catalog.json jumbo width changed — re-run the diagnosis in this "
            "class's docstring before trusting it."
        )
        assert jumbo["height"] == pytest.approx(385.1, abs=0.1), (
            "catalog.json jumbo height changed — re-run the diagnosis in this "
            "class's docstring before trusting it."
        )
