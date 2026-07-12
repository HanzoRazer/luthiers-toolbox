"""Tests for the review summary builder and section normalization."""

from __future__ import annotations

import pytest

from app.ibg_repository import (
    ReviewSummaryError,
    build_changed_file_summary,
    build_review_summary,
    build_review_title,
    normalize_review_sections,
)


# --- normalize_review_sections -----------------------------------------

def test_normalize_accepts_tuples_and_mappings():
    out = normalize_review_sections(
        [("A", "body a"), {"heading": "B", "body": "body b"}]
    )
    assert out == ({"heading": "A", "body": "body a"}, {"heading": "B", "body": "body b"})


def test_normalize_preserves_order():
    out = normalize_review_sections([("Z", "z"), ("A", "a")])
    assert [s["heading"] for s in out] == ["Z", "A"]  # order preserved, NOT sorted


def test_normalize_rejects_duplicate_heading():
    with pytest.raises(ReviewSummaryError):
        normalize_review_sections([("A", "1"), ("a", "2")])  # case-insensitive dup


@pytest.mark.parametrize(
    "bad",
    [
        [("", "body")],
        [("   ", "body")],
        [("H", 123)],
        [("H",)],
        [42],
        [],
        None,
    ],
)
def test_normalize_fail_closed(bad):
    with pytest.raises(ReviewSummaryError):
        normalize_review_sections(bad)


# --- title / changed files ---------------------------------------------

def test_build_review_title_is_change_intent(make_proposal):
    p = make_proposal(change_intent="do the thing")
    assert build_review_title(p) == "do the thing"


def test_build_changed_file_summary(make_proposal):
    p = make_proposal()
    assert build_changed_file_summary(p) == p.changed_file_summary


def test_title_rejects_non_proposal():
    with pytest.raises(ReviewSummaryError):
        build_review_title({"not": "a proposal"})


def test_changed_file_summary_rejects_non_proposal():
    with pytest.raises(ReviewSummaryError):
        build_changed_file_summary(object())


# --- build_review_summary ----------------------------------------------

def test_build_review_summary_sections(make_proposal):
    p = make_proposal()
    sections = build_review_summary(p)
    headings = [s["heading"] for s in sections]
    assert headings == [
        "Objective",
        "Target",
        "Changed files",
        "CBSP21 evidence",
        "Provenance reference",
        "Constitutional classification",
    ]
    # every body is a string; provenance body carries the reference fields
    prov = next(s for s in sections if s["heading"] == "Provenance reference")
    assert "producing_subsystem" in prov["body"]
    assert p.target.evidence_provenance_hash in prov["body"]


def test_build_review_summary_deterministic(make_proposal):
    p = make_proposal()
    assert build_review_summary(p) == build_review_summary(p)


def test_build_review_summary_rejects_non_proposal():
    with pytest.raises(ReviewSummaryError):
        build_review_summary(object())
