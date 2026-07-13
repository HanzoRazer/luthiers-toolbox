"""
Review summary builder — deterministic, human-facing structured sections from a proposal.

A review summary is a DERIVED, advisory artifact: an ordered set of ``(heading, body)`` sections
built from a governed ``RepositoryChangeProposal``. It never re-derives, promotes, or mutates the
proposal — it only reads canonical facts already on it. Output is deterministic: the section set and
their order are fixed by this builder, section bodies contain no wall-clock time, environment paths,
or object reprs, and duplicate headings are rejected rather than silently merged.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Tuple, Union

from .cbsp21_patch_adapter import compute_packet_hash
from .repository_change_proposal import RepositoryChangeProposal


class ReviewSummaryError(Exception):
    """Raised when review sections are malformed or a summary cannot be built."""


SectionInput = Union[Mapping[str, Any], Tuple[str, str]]


def _coerce_section(raw: SectionInput) -> Dict[str, str]:
    """Coerce one section input into a validated ``{"heading","body"}`` mapping."""
    if isinstance(raw, Mapping):
        heading = raw.get("heading")
        body = raw.get("body")
    elif isinstance(raw, tuple) and len(raw) == 2:
        heading, body = raw
    else:
        raise ReviewSummaryError(f"unsupported review section form: {raw!r}")
    if not isinstance(heading, str) or not heading.strip():
        raise ReviewSummaryError(f"section heading must be a non-empty string: {raw!r}")
    if not isinstance(body, str):
        raise ReviewSummaryError(f"section body must be a string: {raw!r}")
    return {"heading": heading.strip(), "body": body}


def normalize_review_sections(sections: Iterable[SectionInput]) -> Tuple[Dict[str, str], ...]:
    """
    Normalize an ordered set of review sections.

    Order is preserved (sections carry meaning by position); duplicate headings are rejected so a
    review can never present two conflicting bodies under one heading. Fail-closed on any malformed
    section.
    """
    if sections is None:
        raise ReviewSummaryError("review sections are required")
    out: list[Dict[str, str]] = []
    seen: set[str] = set()
    for raw in sections:
        section = _coerce_section(raw)
        key = section["heading"].lower()
        if key in seen:
            raise ReviewSummaryError(f"duplicate review section heading: {section['heading']!r}")
        seen.add(key)
        out.append(section)
    if not out:
        raise ReviewSummaryError("review sections must be non-empty")
    return tuple(out)


def build_review_title(proposal: RepositoryChangeProposal) -> str:
    """Deterministic human-facing title derived from the proposal's change intent."""
    if not isinstance(proposal, RepositoryChangeProposal):
        raise ReviewSummaryError("proposal must be a RepositoryChangeProposal")
    return proposal.target.change_intent.strip()


def build_changed_file_summary(proposal: RepositoryChangeProposal) -> Tuple[str, ...]:
    """The proposal's declared changed-file summary (already sorted+deduped on the proposal)."""
    if not isinstance(proposal, RepositoryChangeProposal):
        raise ReviewSummaryError("proposal must be a RepositoryChangeProposal")
    return tuple(proposal.changed_file_summary)


def build_review_summary(proposal: RepositoryChangeProposal) -> Tuple[Dict[str, str], ...]:
    """
    Build the canonical ordered review sections for a proposal.

    Every body is composed only from canonical facts already on the proposal (change intent, target
    context, declared files, CBSP21 packet reference, provenance reference, classification). No
    timestamps, paths outside the repo-relative declared set, or object reprs are emitted.
    """
    if not isinstance(proposal, RepositoryChangeProposal):
        raise ReviewSummaryError("proposal must be a RepositoryChangeProposal")

    target = proposal.target
    packet = proposal.cbsp21_packet
    patch_id = str(packet.get("patch_id", ""))
    packet_hash = compute_packet_hash(packet)
    changed = build_changed_file_summary(proposal)

    sections = [
        ("Objective", target.change_intent.strip()),
        (
            "Target",
            "\n".join(
                [
                    f"repository: {target.repository_id}",
                    f"base_revision: {target.base_revision}",
                    "authorized_paths:",
                    *[f"  - {p}" for p in target.authorized_target_paths],
                ]
            ),
        ),
        (
            "Changed files",
            "\n".join(f"  - {f}" for f in changed) if changed else "(none declared)",
        ),
        ("CBSP21 evidence", f"patch_id: {patch_id}\npacket_hash: {packet_hash}"),
        (
            "Provenance reference",
            "\n".join(
                [
                    f"evidence_candidate_id: {target.evidence_candidate_id}",
                    f"evidence_provenance_hash: {target.evidence_provenance_hash}",
                    f"producing_subsystem: {target.producing_subsystem}",
                    f"source_authority_state: {target.source_authority_state}",
                ]
            ),
        ),
        ("Constitutional classification", proposal.constitutional_classification),
    ]
    return normalize_review_sections(sections)
