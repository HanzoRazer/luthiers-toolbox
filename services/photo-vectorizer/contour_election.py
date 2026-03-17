from __future__ import annotations

from typing import Any, Iterable, Optional


def elect_body_contour_with_ownership(
    candidates: Iterable[Any],
    *,
    ownership_threshold: float = 0.60,
) -> Optional[Any]:
    """
    Elect the best body contour candidate with a hard body-ownership gate.

    Candidate contract:
      - candidate.total_score or candidate.best_score
      - candidate.ownership_score
      - candidate.diagnostics (optional)
    """
    accepted = []
    rejected = []

    for candidate in candidates:
        ownership_score = getattr(candidate, "ownership_score", None)
        if ownership_score is None:
            ownership_score = (
                getattr(candidate, "diagnostics", {}) or {}
            ).get("ownership_score", 0.0)

        if float(ownership_score) < float(ownership_threshold):
            diagnostics = dict(getattr(candidate, "diagnostics", {}) or {})
            diagnostics["rejected_by_body_ownership_gate"] = True
            diagnostics["ownership_threshold"] = float(ownership_threshold)
            candidate.diagnostics = diagnostics
            rejected.append(candidate)
            continue

        accepted.append(candidate)

    if not accepted:
        # No candidate owns the body well enough. Return highest-scoring rejected
        # candidate so downstream can surface diagnostics / manual-review semantics.
        if not rejected:
            return None
        best_rejected = max(
            rejected,
            key=lambda c: float(
                getattr(c, "total_score", getattr(c, "best_score", 0.0))
            ),
        )
        diagnostics = dict(getattr(best_rejected, "diagnostics", {}) or {})
        diagnostics["manual_review_required"] = True
        diagnostics["body_ownership_gate_failed"] = True
        best_rejected.diagnostics = diagnostics
        return best_rejected

    return max(
        accepted,
        key=lambda c: float(
            getattr(c, "total_score", getattr(c, "best_score", 0.0))
        ),
    )
