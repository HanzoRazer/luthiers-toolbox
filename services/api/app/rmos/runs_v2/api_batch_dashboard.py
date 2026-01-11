from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/batch-summary-dashboard")
def batch_summary_dashboard(
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
    include_links: bool = True,
    include_kpis: bool = True,
):
    """
    Compact card payload for dashboards:
      counts + latest ids + KPI rollup + links
    """
    from app.rmos.runs_v2.batch_dashboard import build_batch_summary_dashboard_card

    return build_batch_summary_dashboard_card(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        include_links=include_links,
        include_kpis=include_kpis,
    )
