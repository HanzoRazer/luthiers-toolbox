"""
RMOS Run Log - Audit surface for manufacturing runs.

This module provides:
- RunLogEntry schema for flattened run summaries
- Projector to convert RunArtifact -> RunLogEntry
- Exporters for CSV/JSON output
- API endpoints for querying run history
"""
from .schemas import RunLogEntry, InputSummary, CAMSummary, OutputsSummary, AttachmentsSummary, HashesSummary, LineageSummary
from .projector import project_run_artifact
from .exporters import export_csv, export_jsonl, regenerate_csv_from_jsonl

__all__ = [
    "RunLogEntry",
    "InputSummary",
    "CAMSummary",
    "OutputsSummary",
    "AttachmentsSummary",
    "HashesSummary",
    "LineageSummary",
    "project_run_artifact",
    "export_csv",
    "export_jsonl",
    "regenerate_csv_from_jsonl",
]
