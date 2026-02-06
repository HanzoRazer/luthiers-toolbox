"""tap-tone-pi: metadata writer stub (Release A.1)

Dependency-free helper to write `meta/session_meta.json`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True)
class SessionMetaV1:
    schema_id: str = "tap_tone_session_meta_v1"
    specimen_id: str = ""
    run_id: str = ""
    device_id: str = ""
    fixture_id: str = ""
    mic_id: str = ""
    mic_gain_db: Optional[float] = None
    preamp_model: Optional[str] = None
    sample_rate_hz: Optional[int] = None
    tap_count: Optional[int] = None
    tap_protocol: Optional[str] = None
    ambient_notes: Optional[str] = None
    created_at_utc: str = ""

def write_session_meta(pack_root: Path, meta: SessionMetaV1) -> Path:
    out_dir = pack_root / "meta"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = asdict(meta)
    if not payload.get("created_at_utc"):
        payload["created_at_utc"] = utc_now_rfc3339()

    out_path = out_dir / "session_meta.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path
