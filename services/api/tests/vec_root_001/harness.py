"""Driver for the VEC-ROOT-001 harness.

Runs the *production* extraction path
(``blueprint_extract.extract_blueprint_to_dxf`` -> ``edge_to_dxf.convert``) with
``isolate_body=True``, wrapping two module-level functions to observe the
eligibility gate in ``edge_to_dxf._build_hierarchy_nodes``
(``edge_to_dxf.py:963-976`` at main blob c847c043). Nothing in the repository is
edited; the wrappers are installed and removed inside a try/finally.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
_API = REPO_ROOT / "services" / "api"
_PV = REPO_ROOT / "services" / "photo-vectorizer"
for _p in (_API, _PV):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@dataclass
class NodeObs:
    idx: int
    bbox: tuple[int, int, int, int]  # x, y, w, h
    area_ratio: float
    reject_reason: str


@dataclass
class GroupObs:
    score: float
    bbox: tuple[int, int, int, int]
    member_count: int


@dataclass
class RunResult:
    plan_key: str
    image_size: tuple[int, int] = (0, 0)  # width, height
    eligible: list[NodeObs] = field(default_factory=list)
    rejects: dict[str, int] = field(default_factory=dict)
    groups: list[GroupObs] = field(default_factory=list)
    failed: bool = False
    error: str = ""

    @property
    def eligible_count(self) -> int:
        return len(self.eligible)

    @property
    def winner(self) -> GroupObs | None:
        return max(self.groups, key=lambda g: g.score) if self.groups else None


_RUN_CACHE: dict[tuple[str, str], "RunResult"] = {}


def run_plan_cached(plan_key: str, source: Path) -> RunResult:
    """Run each plan at most once per session.

    The criteria interrogate different facets of one run, so re-extracting per
    assertion costs ~6s each and measures nothing new.
    """
    key = (plan_key, str(source))
    if key not in _RUN_CACHE:
        _RUN_CACHE[key] = run_plan(plan_key, source)
    return _RUN_CACHE[key]


def run_plan(plan_key: str, source: Path) -> RunResult:
    """Extract ``source`` through the production path and report what the gate did."""
    import edge_to_dxf as etd
    from app.services.blueprint_extract import extract_blueprint_to_dxf

    result = RunResult(plan_key=plan_key)

    orig_nodes = etd._build_hierarchy_nodes
    orig_score = etd._score_contour_group

    def wrapped_nodes(contours, hierarchy, iw, ih,
                      min_area_ratio=0.005, max_area_ratio=0.95, *a, **k):
        nodes = orig_nodes(contours, hierarchy, iw, ih,
                           min_area_ratio, max_area_ratio, *a, **k)
        result.image_size = (int(iw), int(ih))
        for n in nodes:
            obs = NodeObs(
                idx=int(n.idx),
                bbox=tuple(int(v) for v in n.bbox),
                area_ratio=float(n.area_ratio),
                reject_reason=str(getattr(n, "reject_reason", "") or ""),
            )
            if getattr(n, "is_eligible_root", False):
                result.eligible.append(obs)
            else:
                key = obs.reject_reason or "(blank)"
                result.rejects[key] = result.rejects.get(key, 0) + 1
        return nodes

    def wrapped_score(group, iw, ih):
        score = orig_score(group, iw, ih)
        members = getattr(group, "member_contours", None) or []
        bbox = getattr(group, "bbox", (0, 0, 0, 0))
        result.groups.append(
            GroupObs(score=float(score),
                     bbox=tuple(int(v) for v in bbox),
                     member_count=len(members))
        )
        return score

    work = Path(tempfile.mkdtemp(prefix="vec_root_001_"))
    try:
        etd._build_hierarchy_nodes = wrapped_nodes
        etd._score_contour_group = wrapped_score
        staged = work / source.name
        shutil.copyfile(source, staged)
        try:
            extract_blueprint_to_dxf(
                source_path=str(staged),
                output_path=str(work / "out.dxf"),
                target_height_mm=500.0,
                warnings=[],
                isolate_body=True,
            )
        except Exception as exc:  # the L-00 lane raises; that is data, not an error
            result.failed = True
            result.error = str(exc)
    finally:
        etd._build_hierarchy_nodes = orig_nodes
        etd._score_contour_group = orig_score
        shutil.rmtree(work, ignore_errors=True)

    return result


def overlaps(bbox: tuple[int, int, int, int],
             region: tuple[int, int, int, int]) -> bool:
    """``bbox`` is (x, y, w, h); ``region`` is (x0, y0, x1, y1)."""
    x, y, w, h = bbox
    rx0, ry0, rx1, ry1 = region
    return not (x + w <= rx0 or x >= rx1 or y + h <= ry0 or y >= ry1)


def contained_in(bbox: tuple[int, int, int, int],
                 region: tuple[int, int, int, int],
                 tol: int = 40) -> bool:
    """True when ``bbox`` sits inside ``region``, allowing ``tol`` px of slop."""
    x, y, w, h = bbox
    rx0, ry0, rx1, ry1 = region
    return (x >= rx0 - tol and y >= ry0 - tol
            and x + w <= rx1 + tol and y + h <= ry1 + tol)
