# Pack Metadata Additions (Release A.1 follow-on)

Goal: include **setup + capture metadata** in the exported evidence pack so ToolBox can display and compare runs.

## Where it lives (recommended)

### Session-level metadata (global)
File: `meta/session_meta.json`
Kind in manifest: `session_meta` (already supported by ToolBox JsonRenderer)

Schema (additive; safe for existing viewers):
```json
{
  "schema_id": "tap_tone_session_meta_v1",
  "specimen_id": "S-0001",
  "run_id": "2026-01-22T1723Z_A1",
  "device_id": "tap-tone-pi-01",
  "fixture_id": "fixture_v3",
  "mic_id": "mic_sm57_01",
  "mic_gain_db": 28.0,
  "preamp_model": "scarlett_solo",
  "sample_rate_hz": 48000,
  "tap_count": 5,
  "tap_protocol": "center_tap_light",
  "ambient_notes": "quiet room",
  "created_at_utc": "2026-01-22T17:23:00Z"
}
```

## Manifest entries

Add:
- relpath: `meta/session_meta.json`
- kind: `session_meta`
- mime: `application/json`

## Why this structure
- Adds no new rendering type (JsonRenderer already exists)
- Stable location for "compare runs" UI
- Keeps measurement files pure (spectrum.csv unchanged)

## Minimal acceptance criteria
- Pack contains `meta/session_meta.json`
- ToolBox can display it via JSON renderer
- Compare UI can extract: fixture_id, mic_gain_db, tap_count, sample_rate_hz, device_id
