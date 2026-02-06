# Quickstart — First Measurement in 5 Minutes

Get from zero to a valid, exportable measurement.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| Python | 3.10+ |
| Microphone | USB measurement mic (UMIK-1 recommended) or built-in |
| Specimen | Flat plate, free-free support (foam blocks) |
| Striker | Wooden dowel, pencil, or knuckle |

---

## Step 1: Install (once)

```bash
git clone https://github.com/your-org/tap-tone-pi.git
cd tap-tone-pi
pip install -e .
```

Verify:
```bash
python -m tap_tone.main --help
```

---

## Step 2: List Audio Devices

```bash
python -m tap_tone.main --list-devices
```

Note your microphone's **device index** (e.g., `2`).

---

## Step 3: Capture a Tap

```bash
python -m tap_tone.main --device 2 --out ./my_first_run --label "spruce_top_center"
```

**Action:** When prompted, tap the specimen once with a sharp impulse.

**Output:**
```
./my_first_run/
├── audio.wav
├── analysis.json
├── spectrum.csv
└── session.jsonl
```

---

## Step 4: Check Results

Open `analysis.json`:
```json
{
  "dominant_hz": 187.5,
  "peaks": [
    {"freq_hz": 187.5, "magnitude": 0.82},
    {"freq_hz": 312.0, "magnitude": 0.45}
  ],
  "rms": 0.034,
  "clipped": false,
  "confidence": 0.91
}
```

**Good signs:**
- `clipped: false`
- `confidence > 0.7`
- `peaks` array has 2–6 entries in expected range (50–1000 Hz for plates)

---

## Step 5: View Spectrum (Optional)

```bash
python -c "import pandas as pd; import matplotlib.pyplot as plt; \
  df = pd.read_csv('./my_first_run/spectrum.csv'); \
  plt.plot(df['freq_hz'], df['magnitude']); \
  plt.xlabel('Hz'); plt.ylabel('Magnitude'); plt.show()"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `clipped: true` | Input too loud | Move mic back, tap softer |
| `confidence < 0.5` | Weak signal | Tap harder, check mic gain |
| No peaks detected | Noise floor too high | Reduce background noise |
| Wrong device | Incorrect index | Re-run `--list-devices` |

---

## Next Steps

| Goal | Command / Doc |
|------|---------------|
| Compare two runs | Capture second run, compare `analysis.json` |
| 2-channel ODS | See `docs/phase2/` |
| Export viewer pack | `python scripts/phase2/export_viewer_pack_v1.py` |
| Bending stiffness (MOE) | See `docs/MEASUREMENT_README.md` |

---

## Golden Rule

> **Same protocol, same position, same support = valid comparison.**

Document your setup. Mark tap locations. Control your environment.

---

## Success Criteria

You have a valid first measurement if:

- [x] `audio.wav` exists and is not silent
- [x] `clipped: false`
- [x] `confidence > 0.7`
- [x] `peaks` contains at least one entry
- [x] Peak frequencies are plausible for your specimen

**Congratulations — you now have laboratory-grade acoustic evidence.**
