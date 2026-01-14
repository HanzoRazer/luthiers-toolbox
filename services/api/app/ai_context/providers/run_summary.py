"""
AI Context Adapter - Run Summary Provider

Provides read-only run summary context from RMOS runs.
Excludes toolpaths and manufacturing details.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    SourceKind,
    WarningCode,
)


class RunSummaryProvider:
    """
    Provides run_summary context from RMOS.
    
    Includes:
    - Run status and state
    - Candidate counts
    - Blocker information
    - Feasibility summary
    
    Excludes:
    - Toolpath data
    - G-code
    - Detailed manufacturing parameters
    """
    
    @property
    def source_kind(self) -> SourceKind:
        return SourceKind.RUN_SUMMARY
    
    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """Provide run summary context."""
        sources: List[ContextSource] = []
        attachments: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        run_id = req.scope.run_id
        if not run_id:
            warnings.append(AdapterWarning(
                code=WarningCode.SCOPE_NOT_FOUND,
                message="No run_id in scope, skipping run_summary provider",
            ))
            return sources, attachments, warnings
        
        # Attempt to fetch run data
        run_data = self._fetch_run(run_id)
        if run_data is None:
            warnings.append(AdapterWarning(
                code=WarningCode.SCOPE_NOT_FOUND,
                message=f"Run '{run_id}' not found",
            ))
            return sources, attachments, warnings
        
        # Build sanitized summary
        summary = self._build_summary(run_data)
        
        sources.append(ContextSource(
            source_id=f"run_summary_{run_id}",
            kind=SourceKind.RUN_SUMMARY,
            content_type="application/json",
            payload=summary,
        ))
        
        return sources, attachments, warnings
    
    def _fetch_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch run data from RMOS.
        
        This is a stub that should be wired to the actual RMOS runs store.
        """
        try:
            # Import here to avoid circular imports
            from app.rmos.runs_v2.store import get_run_v2
            
            run = get_run_v2(run_id)
            if run:
                return run.dict() if hasattr(run, "dict") else dict(run)
            return None
        except ImportError:
            # Fallback for when RMOS is not available
            return None
        except Exception:
            return None
    
    def _build_summary(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a sanitized summary from run data.
        
        Only includes safe fields, no toolpaths or manufacturing details.
        """
        summary: Dict[str, Any] = {
            "run_id": run_data.get("run_id"),
            "status": run_data.get("status"),
            "created_at": run_data.get("created_at"),
            "updated_at": run_data.get("updated_at"),
        }
        
        # Include state if present
        if "state" in run_data:
            summary["state"] = run_data["state"]
        
        # Include blockers/issues if present
        if "blockers" in run_data:
            summary["blockers"] = run_data["blockers"]
        if "issues" in run_data:
            summary["issues"] = run_data["issues"]
        
        # Include candidate counts but not the candidates themselves
        if "candidates" in run_data:
            candidates = run_data["candidates"]
            if isinstance(candidates, list):
                summary["candidate_count"] = len(candidates)
                # Count by status if available
                by_status: Dict[str, int] = {}
                for c in candidates:
                    if isinstance(c, dict) and "status" in c:
                        status = c["status"]
                        by_status[status] = by_status.get(status, 0) + 1
                if by_status:
                    summary["candidates_by_status"] = by_status
        
        # Include feasibility summary (not detailed results)
        if "feasibility" in run_data:
            feas = run_data["feasibility"]
            if isinstance(feas, dict):
                summary["feasibility"] = {
                    "overall_status": feas.get("status") or feas.get("overall_status"),
                    "risk_level": feas.get("risk_level"),
                    "checked_at": feas.get("checked_at") or feas.get("timestamp"),
                }
        
        # Include artifact counts
        if "artifacts" in run_data:
            artifacts = run_data["artifacts"]
            if isinstance(artifacts, list):
                summary["artifact_count"] = len(artifacts)
                # Count by kind
                by_kind: Dict[str, int] = {}
                for a in artifacts:
                    if isinstance(a, dict) and "kind" in a:
                        kind = a["kind"]
                        by_kind[kind] = by_kind.get(kind, 0) + 1
                if by_kind:
                    summary["artifacts_by_kind"] = by_kind
        
        return summary


# Singleton instance
run_summary_provider = RunSummaryProvider()
