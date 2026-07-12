"""
Repository review export — deterministic dict / JSON / markdown serialization of a review bundle.

Every export is derived purely from the bundle's canonical dict, so identical inputs produce
byte-stable output. No wall-clock time, environment paths, object reprs, or unordered iteration
enters any export. Markdown is rendered from the same canonical structure the JSON is, so the two
never diverge. Nothing here mutates, executes git, or touches the network.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .repository_review_bundle import RepositoryReviewBundle


def to_dict(bundle: RepositoryReviewBundle) -> Dict[str, Any]:
    """The bundle's canonical dict (single source of truth for all exports)."""
    if not isinstance(bundle, RepositoryReviewBundle):
        raise TypeError("to_dict expects a RepositoryReviewBundle")
    return bundle.to_canonical_dict()


def build_review_json(canonical: Dict[str, Any]) -> str:
    """Deterministic, human-readable JSON (sorted keys) from a canonical dict."""
    return json.dumps(canonical, sort_keys=True, indent=2, ensure_ascii=False)


def to_json(bundle: RepositoryReviewBundle) -> str:
    """Deterministic JSON export of a review bundle."""
    return build_review_json(to_dict(bundle))


def stable_review_hash(bundle: RepositoryReviewBundle) -> str:
    """Deterministic 16-hex content hash of a bundle (compact canonical JSON)."""
    canonical = to_dict(bundle)
    compact = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(compact.encode()).hexdigest()[:16]


def _kv_lines(mapping: Dict[str, Any]) -> List[str]:
    """Deterministic ``- key: value`` lines, keys sorted."""
    return [f"- {k}: {mapping[k]}" for k in sorted(mapping)]


def build_review_markdown(canonical: Dict[str, Any]) -> str:
    """
    Render deterministic markdown from a canonical review-bundle dict.

    Ordering is fixed: heading, metadata, review sections (in their canonical order), changed files,
    CBSP21 evidence, provenance, workspace. Byte-stable for identical inputs.
    """
    draft = canonical.get("draft_pull_request", {})
    lines: List[str] = []

    lines.append(f"# {draft.get('title', '')}")
    lines.append("")
    lines.append(draft.get("summary", ""))
    lines.append("")
    lines.append(f"- proposal_id: {canonical.get('proposal_id', '')}")
    lines.append(f"- head_branch: {draft.get('branch_name', '')}")
    lines.append(f"- target_branch: {draft.get('target_branch', '')}")
    lines.append(
        f"- classification: {canonical.get('constitutional_classification', '')}"
    )
    lines.append("")

    lines.append("## Review sections")
    for section in draft.get("review_sections", []):
        lines.append(f"### {section.get('heading', '')}")
        lines.append(section.get("body", ""))
        lines.append("")

    lines.append("## Changed files")
    changed = draft.get("changed_file_summary", [])
    if changed:
        lines.extend(f"- {f}" for f in changed)
    else:
        lines.append("(none declared)")
    lines.append("")

    lines.append("## CBSP21 evidence")
    lines.append(f"- patch_id: {draft.get('cbsp21_patch_id', '')}")
    lines.append(f"- packet_hash: {draft.get('cbsp21_packet_hash', '')}")
    lines.append("")

    lines.append("## Provenance")
    lines.extend(_kv_lines(canonical.get("provenance_reference", {})))
    lines.append(
        f"- full_lineage_embedded: {canonical.get('provenance_lineage_embedded', False)}"
    )
    lines.append("")

    lines.append("## Workspace")
    workspace = canonical.get("workspace_metadata")
    if workspace:
        lines.extend(_kv_lines(workspace))
    else:
        lines.append("(no workspace metadata supplied)")
    lines.append("")

    return "\n".join(lines)


def to_markdown(bundle: RepositoryReviewBundle) -> str:
    """Deterministic markdown export of a review bundle."""
    return build_review_markdown(to_dict(bundle))
