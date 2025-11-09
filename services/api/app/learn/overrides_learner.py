"""Learn feed overrides from logged CAM runs.

Simple heuristic-based learning:
- Tight arcs (radius < r_min): average observed slowdown
- Trochoids: average observed slowdown
- Minimum 50 samples per rule to avoid overfitting noise

Output: JSON file per machine with scalar feed multipliers.
"""

import os
import sqlite3
import json
from typing import Dict, Any

DB = os.getenv(
    "CAM_LOG_DB",
    os.path.join(os.path.dirname(__file__), "..", "telemetry", "cam_logs.db"),
)
OUT_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUT_DIR, exist_ok=True)


def _fetch_segments(machine_id: str):
    """Fetch all segment records for a machine from logs."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT segments.*, runs.machine_id
        FROM segments JOIN runs ON segments.run_id=runs.id
        WHERE runs.machine_id=?""",
        (machine_id,),
    ).fetchall()
    con.close()
    return rows


def train_overrides(machine_id: str, r_min_mm: float = 5.0) -> Dict[str, Any]:
    """
    Train feed override rules from logged runs.

    Args:
        machine_id: Machine profile ID to train for
        r_min_mm: Minimum radius threshold for "tight arc" rule

    Returns:
        Dictionary with learned rules and metadata:
        {
          "machine_id": "Mach4_Router_4x8",
          "rules": {
            "arc_tight_mm<=5.00": 0.75,  # 75% feed for tight arcs
            "trochoid": 0.85             # 85% feed for trochoidal moves
          },
          "meta": {"samples": 1234, "r_min": 5.0}
        }

    Saves to: learn/models/overrides_{machine_id}.json
    """
    rows = _fetch_segments(machine_id)
    if not rows:  # nothing to learn
        return {"machine_id": machine_id, "rules": {}, "meta": {"samples": 0}}

    # Heuristic aggregates
    n_arc_tight = n_arc_loose = n_tro = 0
    # Collect slowdown where present (meta.slowdown ~ engagement penalty 0..1)
    S_arc_tight = S_tro = 0.0

    for r in rows:
        code = r["code"]
        rad = r["radius_mm"] or 0.0
        slow = r["slowdown"] or 1.0
        tro = bool(r["trochoid"])

        if code in ("G2", "G3"):
            if 0 < rad <= r_min_mm:
                n_arc_tight += 1
                S_arc_tight += float(slow)
            else:
                n_arc_loose += 1

        if tro:
            n_tro += 1
            S_tro += float(slow)

    rules = {}
    # If we have enough samples, propose multipliers = average slowdown clamped
    if n_arc_tight >= 50:
        m = max(0.5, min(1.0, S_arc_tight / n_arc_tight))
        rules[f"arc_tight_mm<={r_min_mm:.2f}"] = round(m, 3)

    if n_tro >= 50:
        m = max(0.6, min(1.0, S_tro / n_tro))
        rules["trochoid"] = round(m, 3)

    out = {
        "machine_id": machine_id,
        "rules": rules,
        "meta": {"samples": len(rows), "r_min": r_min_mm},
    }

    # Save to disk
    path = os.path.join(OUT_DIR, f"overrides_{machine_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    return out
