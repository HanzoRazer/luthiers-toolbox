from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import RunArtifact, AdvisoryInputRef


class RunStore:
    """
    Minimal filesystem store:
      - writes each run to <root>/<run_id>.json
      - patch operations are implemented by load-modify-save (v1 simplicity)

    Replace with SQLite/DB later if desired.
    """

    def __init__(self, root_dir: str):
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, run_id: str) -> Path:
        # very conservative filename sanitation
        safe = run_id.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe}.json"

    def put(self, run: RunArtifact) -> None:
        path = self._path_for(run.run_id)
        tmp = path.with_suffix(".json.tmp")

        payload = run.model_dump(mode="json")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)

    def get(self, run_id: str) -> Optional[RunArtifact]:
        path = self._path_for(run_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return RunArtifact.model_validate(raw)

    def patch_meta(self, run_id: str, meta_updates: Dict[str, Any]) -> Optional[RunArtifact]:
        run = self.get(run_id)
        if run is None:
            return None
        run.meta.update(meta_updates)
        self.put(run)
        return run

    def attach_advisory(
        self,
        run_id: str,
        advisory_id: str,
        kind: str = "unknown",
        engine_id: Optional[str] = None,
        engine_version: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[RunArtifact]:
        """
        Attach an advisory reference to a run.
        
        Returns None if run not found.
        Silently skips if advisory already attached.
        """
        run = self.get(run_id)
        if run is None:
            return None
        
        # Check for duplicate
        for ref in run.advisory_inputs:
            if ref.advisory_id == advisory_id:
                return run
        
        ref = AdvisoryInputRef(
            advisory_id=advisory_id,
            kind=kind,
            engine_id=engine_id,
            engine_version=engine_version,
            request_id=request_id,
        )
        run.advisory_inputs.append(ref)
        self.put(run)
        return run

    def set_explanation(
        self,
        run_id: str,
        status: str,
        summary: Optional[str] = None,
    ) -> Optional[RunArtifact]:
        """Update explanation status and summary on a run."""
        run = self.get(run_id)
        if run is None:
            return None
        run.explanation_status = status
        if summary is not None:
            run.explanation_summary = summary
        self.put(run)
        return run

    def list_all(self, limit: int = 100) -> List[RunArtifact]:
        """List all runs, newest first."""
        runs = []
        for p in self.root.glob("*.json"):
            if p.suffix == ".json" and not p.name.endswith(".tmp"):
                try:
                    raw = json.loads(p.read_text(encoding="utf-8"))
                    runs.append(RunArtifact.model_validate(raw))
                except Exception:
                    continue
        runs.sort(key=lambda r: r.created_at_utc, reverse=True)
        return runs[:limit]
