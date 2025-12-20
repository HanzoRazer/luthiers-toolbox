"""
REFERENCE ONLY - DO NOT IMPORT IN PRODUCTION

This folder contains reference implementations preserved for documentation.
Production code lives in: services/api/app/rmos/runs_v2/

See: docs/Runs_Advisory_Integration/README.md
"""

# Legacy exports - DO NOT USE
# Production imports should come from:
#   from app.rmos.runs_v2 import RunArtifact, RunStore, ...

from .schemas import RunArtifact, RunDecision, Hashes, RunOutputs, AdvisoryInputRef
from .hashing import sha256_text, sha256_json, sha256_toolpaths_payload, summarize_request
from .store import RunStore
