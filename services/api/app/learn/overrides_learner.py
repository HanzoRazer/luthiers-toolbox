"""
================================================================================
Feed Override ML Training Module
================================================================================

PURPOSE:
--------
Learns optimal feed override rules from logged CAM operation data.
Trains machine-specific models using heuristic-based analysis of segment performance.
Outputs JSON files consumed by app.util.overrides for runtime feed modulation.

CORE FUNCTIONS:
--------------
1. train_overrides(machine_id, r_min_mm=5.0)
   - Trains feed override rules from historical segment logs
   - Analyzes tight arcs, trochoidal moves, and engagement patterns
   - Returns trained model + metadata (sample count, thresholds)
   - Saves to: learn/models/overrides_{machine_id}.json

2. _fetch_segments(machine_id)
   - Fetches all segment records for a machine from SQLite logs
   - Joins segments with runs table to filter by machine_id
   - Returns sqlite3.Row objects with segment metrics

LEARNING ALGORITHM:
------------------
**Heuristic-Based Training:**

1. **Data Collection:**
   - Query all segments for target machine from cam_logs.db
   - Extract: code (G0/G1/G2/G3), radius_mm, slowdown, trochoid flag
   - Join with runs table to filter by machine_id

2. **Feature Aggregation:**
   - **Tight Arcs**: G2/G3 with radius_mm <= r_min (default: 5mm)
   - **Trochoidal Moves**: Segments with trochoid=1
   - **Slowdown Values**: meta.slowdown field (0.0-1.0 engagement penalty)

3. **Rule Generation:**
   - **Minimum Sample Threshold**: >=50 samples per rule (prevents overfitting noise)
   - **Tight Arc Rule**: Average slowdown clamped to [0.5, 1.0]
   - **Trochoid Rule**: Average slowdown clamped to [0.6, 1.0]
   - **Output Format**: {"arc_tight_mm<=5.00": 0.75, "trochoid": 0.85}

4. **Model Persistence:**
   - Save to: learn/models/overrides_{machine_id}.json
   - Format: {machine_id, rules, meta: {samples, r_min}}
   - Consumed by: app.util.overrides.load_overrides()

INTEGRATION POINTS:
------------------
- Data Source: app.telemetry.cam_logs (SQLite segment/run logs)
- Used by: app.util.overrides.load_overrides() (runtime evaluation)
- Output Dir: learn/models/overrides_{machine_id}.json
- Environment: CAM_LOG_DB env var (default: ../telemetry/cam_logs.db)
- Exports: train_overrides(), _fetch_segments()

CRITICAL SAFETY RULES:
---------------------
1. **Minimum Sample Threshold**: >=50 samples per rule
2. **Feed Factor Clamping**: Always within [0.5, 1.0]
3. **Graceful Degradation**: No crashes on missing data

================================================================================
"""

import os
import sqlite3
import json
from typing import Dict, Any, Optional

DB: str = os.getenv(
    "CAM_LOG_DB",
    os.path.join(os.path.dirname(__file__), "..", "telemetry", "cam_logs.db"),
)
OUT_DIR: str = os.path.join(os.path.dirname(__file__), "models")


# =============================================================================
# DATA COLLECTION (SEGMENT QUERIES)
# =============================================================================

def _fetch_segments(machine_id: str):
    """Fetch all segment records for a machine from logs.

    Returns empty list if database or tables don't exist (graceful degradation).
    """
    try:
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
    except sqlite3.OperationalError:
        # Table doesn't exist yet (no logs recorded) - return empty list
        return []


# =============================================================================
# HEURISTIC MODEL TRAINING
# =============================================================================

def train_overrides(
    machine_id: Optional[str] = None,
    *,
    machine_profile: Optional[str] = None,
    r_min_mm: float = 5.0,
) -> Dict[str, Any]:
    """
    Train feed override rules from logged runs.

    Args:
        machine_id: Machine profile ID to train for
        r_min_mm: Minimum radius threshold for "tight arc" rule

    Returns:
        Dictionary with learned rules and metadata.

    Saves to: learn/models/overrides_{machine_id}.json
    """
    mid = machine_profile or machine_id
    if not mid:
        raise ValueError("train_overrides requires machine_id or machine_profile")

    rows = _fetch_segments(mid)
    if not rows:  # nothing to learn
        return {"machine_id": mid, "machine_profile": mid, "rules": {}, "meta": {"samples": 0}}

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
        "machine_id": mid,
        "machine_profile": mid,
        "rules": rules,
        "meta": {"samples": len(rows), "r_min": r_min_mm},
    }

    # Save to disk (lazy create output directory)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"overrides_{mid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    return out
