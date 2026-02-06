from __future__ import annotations
import hashlib, json, time, os, pathlib
from typing import Dict, Any, Iterable

def file_hash(path: str, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(out_path: str, *, rig: Dict[str, Any] | None = None,
                   artifacts: Iterable[str] = (), notes: str | None = None) -> str:
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "artifact_type": "manifest",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rig": rig or {},
        "artifacts": [],
        "notes": notes or ""
    }
    for a in artifacts:
        a = os.fspath(a)
        entry = {"path": a, "sha256": file_hash(a), "size": os.path.getsize(a)}
        data["artifacts"].append(entry)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return os.fspath(p)
