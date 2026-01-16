# tap-tone-pi Scaffolding Guide

**Quick-start code examples for integration developers.**

---

## 1. Producer: Exporting a Viewer Pack (Python)

### Minimal Export Script

```python
#!/usr/bin/env python3
"""Minimal viewer_pack_v1 export example."""

import hashlib
import json
import zipfile
from pathlib import Path
from datetime import datetime, timezone

def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def infer_kind(relpath: str) -> str:
    """Map relpath to file kind."""
    if relpath.endswith("/spectrum.csv") or relpath.endswith("spectrum.csv"):
        return "spectrum_csv"
    if relpath.endswith("/analysis.json"):
        return "analysis_peaks"
    if relpath.endswith(".wav"):
        return "audio_raw"
    if relpath.endswith(".png"):
        return "plot_png"
    if "ods_snapshot" in relpath:
        return "transfer_function"
    if "wolf_candidates" in relpath:
        return "wolf_candidates"
    if "wsi_curve" in relpath:
        return "wsi_curve"
    if relpath.startswith("meta/"):
        return "session_meta"
    if "capture_meta" in relpath:
        return "provenance"
    if relpath == "manifest.json":
        return "manifest"
    return "unknown"

def infer_mime(relpath: str) -> str:
    """Map relpath to MIME type."""
    if relpath.endswith(".wav"):
        return "audio/wav"
    if relpath.endswith(".csv"):
        return "text/csv"
    if relpath.endswith(".json"):
        return "application/json"
    if relpath.endswith(".png"):
        return "image/png"
    if relpath.endswith(".md") or relpath.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"

def export_viewer_pack(session_dir: Path, output_zip: Path):
    """Export a Phase 2 session to viewer_pack_v1 ZIP."""

    # Collect files
    files = []
    file_mapping = {}  # source_path -> relpath

    # Map session structure to pack structure
    mappings = [
        ("grid.json", "meta/grid.json"),
        ("metadata.json", "meta/metadata.json"),
        ("derived/ods_snapshot.json", "ods/ods_snapshot.json"),
        ("derived/wolf_candidates.json", "wolf/wolf_candidates.json"),
        ("derived/wsi_curve.csv", "wolf/wsi_curve.csv"),
    ]

    for src_rel, dst_rel in mappings:
        src = session_dir / src_rel
        if src.exists():
            file_mapping[src] = dst_rel

    # Map point directories
    points_dir = session_dir / "points"
    if points_dir.exists():
        for point_dir in sorted(points_dir.iterdir()):
            if not point_dir.is_dir():
                continue
            pid = point_dir.name.replace("point_", "")

            # Audio
            audio = point_dir / "audio.wav"
            if audio.exists():
                file_mapping[audio] = f"audio/points/{pid}.wav"

            # Spectrum
            spectrum = point_dir / "spectrum.csv"
            if spectrum.exists():
                file_mapping[spectrum] = f"spectra/points/{pid}/spectrum.csv"

            # Analysis
            analysis = point_dir / "analysis.json"
            if analysis.exists():
                file_mapping[analysis] = f"spectra/points/{pid}/analysis.json"

            # Capture meta
            capture = point_dir / "capture_meta.json"
            if capture.exists():
                file_mapping[capture] = f"provenance/points/{pid}/capture_meta.json"

    # Map plots
    plots_dir = session_dir / "plots"
    if plots_dir.exists():
        for plot in plots_dir.glob("*.png"):
            file_mapping[plot] = f"plots/{plot.name}"

    # Build file entries
    points_set = set()
    for src, relpath in sorted(file_mapping.items(), key=lambda x: x[1]):
        sha = sha256_file(src)
        size = src.stat().st_size
        kind = infer_kind(relpath)
        mime = infer_mime(relpath)

        files.append({
            "relpath": relpath,
            "sha256": sha,
            "bytes": size,
            "mime": mime,
            "kind": kind,
        })

        # Extract point IDs
        if "/points/" in relpath:
            parts = relpath.split("/")
            idx = parts.index("points")
            if idx + 1 < len(parts):
                points_set.add(parts[idx + 1].split("/")[0])

    # Build manifest (without bundle_sha256)
    manifest = {
        "schema_version": "v1",
        "schema_id": "viewer_pack_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_capdir": session_dir.name,
        "detected_phase": "phase2",
        "measurement_only": True,
        "interpretation": "deferred",
        "points": sorted(points_set),
        "contents": {
            "audio": any(f["kind"] == "audio_raw" for f in files),
            "spectra": any(f["kind"] == "spectrum_csv" for f in files),
            "coherence": any(f["kind"] == "transfer_function" for f in files),
            "ods": any(f["kind"] == "transfer_function" for f in files),
            "wolf": any(f["kind"] == "wolf_candidates" for f in files),
            "plots": any(f["kind"] == "plot_png" for f in files),
            "provenance": any(f["kind"] == "provenance" for f in files),
        },
        "files": files,
    }

    # Compute bundle hash
    canonical = json.dumps(manifest, sort_keys=True, indent=2)
    bundle_sha = hashlib.sha256(canonical.encode()).hexdigest()
    manifest["bundle_sha256"] = bundle_sha

    # Create ZIP
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest first
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Write all files
        for src, relpath in file_mapping.items():
            zf.write(src, relpath)

    print(f"Created: {output_zip}")
    print(f"  Files: {len(files)}")
    print(f"  Bundle SHA: {bundle_sha[:16]}...")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: export_pack.py <session_dir> <output.zip>")
        sys.exit(1)
    export_viewer_pack(Path(sys.argv[1]), Path(sys.argv[2]))
```

---

## 2. Consumer: Loading a Viewer Pack (TypeScript)

### Using the Evidence Loader

```typescript
import { loadNormalizedPack, type NormalizedPack } from "@/evidence";

async function loadViewerPack(file: File): Promise<void> {
  try {
    const pack: NormalizedPack = await loadNormalizedPack(file);

    console.log("Schema:", pack.schema_id);
    console.log("Created:", pack.created_at_utc);
    console.log("Phase:", pack.detected_phase);
    console.log("Files:", pack.files.length);

    // List spectrum files
    const spectra = pack.files.filter(f => f.kind === "spectrum_csv");
    console.log("Spectrum files:", spectra.map(f => f.relpath));

    // Get file bytes
    const firstSpectrum = spectra[0];
    if (firstSpectrum) {
      const bytes = pack.resolveFile(firstSpectrum.relpath);
      const text = new TextDecoder().decode(bytes!);
      console.log("First 200 chars:", text.slice(0, 200));
    }
  } catch (err) {
    console.error("Failed to load pack:", err);
  }
}
```

### Picking a Renderer

```typescript
import { pickRenderer, getRendererCategory } from "@/tools/audio_analyzer/renderers";

function getRendererForFile(kind: string) {
  const category = getRendererCategory(kind);
  const renderer = pickRenderer(kind);

  console.log(`Kind: ${kind} → Category: ${category}`);
  return renderer;
}

// Examples:
getRendererForFile("spectrum_csv");     // → SpectrumChartRenderer
getRendererForFile("transfer_function"); // → TransferFunctionRenderer
getRendererForFile("audio_raw");         // → AudioRenderer
getRendererForFile("wsi_curve");         // → CsvRenderer
```

### Parsing Spectrum CSV

```typescript
interface SpectrumRow {
  freq_hz: number;
  H_mag: number;
  coherence: number;
  phase_deg: number;
}

function parseSpectrumCsv(bytes: Uint8Array): SpectrumRow[] {
  const text = new TextDecoder("utf-8").decode(bytes);
  const lines = text.trim().split(/\r?\n/);

  if (lines.length < 2) {
    throw new Error("CSV has no data rows");
  }

  // Parse header
  const header = lines[0].toLowerCase().split(",").map(h => h.trim());
  const freqIdx = header.findIndex(h => h.includes("freq"));
  const magIdx = header.findIndex(h => h.includes("mag") || h === "h_mag");
  const cohIdx = header.findIndex(h => h.includes("coh"));
  const phaseIdx = header.findIndex(h => h.includes("phase"));

  if (freqIdx === -1 || magIdx === -1) {
    throw new Error(`Missing required columns. Found: ${header.join(", ")}`);
  }

  // Parse rows
  const rows: SpectrumRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(",");
    const freq = parseFloat(cells[freqIdx]);
    const mag = parseFloat(cells[magIdx]);
    const coh = cohIdx >= 0 ? parseFloat(cells[cohIdx]) : 0;
    const phase = phaseIdx >= 0 ? parseFloat(cells[phaseIdx]) : 0;

    if (!isNaN(freq) && !isNaN(mag)) {
      rows.push({ freq_hz: freq, H_mag: mag, coherence: coh, phase_deg: phase });
    }
  }

  return rows;
}
```

### Resolving Sibling Peaks

```typescript
import { findSiblingPeaksRelpath } from "@/tools/audio_analyzer/packHelpers";

function getPeaksForSpectrum(pack: NormalizedPack, spectrumPath: string) {
  const peaksPath = findSiblingPeaksRelpath(spectrumPath);
  if (!peaksPath) return null;

  const peaksBytes = pack.resolveFile(peaksPath);
  if (!peaksBytes) return null;

  const text = new TextDecoder().decode(peaksBytes);
  const json = JSON.parse(text);

  // Extract peaks array
  const peaks = Array.isArray(json) ? json : (json.peaks ?? []);
  return peaks.map((p: any) => ({
    freq_hz: p.freq_hz ?? p.frequency_hz,
    label: p.label ?? p.note,
  }));
}

// Usage:
// spectrumPath = "spectra/points/A1/spectrum.csv"
// → peaksPath = "spectra/points/A1/analysis.json"
// → peaks = [{ freq_hz: 187.5, label: "Mode 1" }, ...]
```

---

## 3. Adding a New File Kind

### Step 1: Add Kind to Schema (tap-tone-pi)

```json
// contracts/viewer_pack_v1.schema.json
{
  "definitions": {
    "file_kind": {
      "enum": [
        "audio_raw",
        "spectrum_csv",
        "my_new_kind",  // ← Add here
        ...
      ]
    }
  }
}
```

### Step 2: Add Kind Mapping (luthiers-toolbox)

```typescript
// packages/client/src/tools/audio_analyzer/renderers/types.ts
export function kindToCategory(kind: string): RendererCategory {
  switch (kind) {
    // ... existing cases ...
    case "my_new_kind":
      return "csv";  // or "json", "image", etc.
    default:
      return "unknown";
  }
}
```

### Step 3: Add Tests

```typescript
// packages/client/src/tools/audio_analyzer/renderers/__tests__/types.spec.ts
it("maps my_new_kind to csv", () => {
  expect(kindToCategory("my_new_kind")).toBe("csv");
});
```

### Step 4: Update MIME Map (if needed)

```typescript
// packages/client/src/evidence/zip_loader.ts
const KIND_TO_MIME: Record<string, string> = {
  // ... existing ...
  my_new_kind: "text/csv",
};
```

---

## 4. Integrity Verification Examples

### Verify File Integrity

```typescript
import { verifyFileIntegrity } from "@/evidence/validate";

async function checkFileIntegrity(pack: NormalizedPack) {
  for (const entry of pack.files) {
    const bytes = pack.resolveFile(entry.relpath);
    if (!bytes) {
      console.error(`Missing: ${entry.relpath}`);
      continue;
    }

    const result = verifyFileIntegrity(entry, bytes);
    if (!result.valid) {
      console.error(`Invalid: ${entry.relpath}`, result.errors);
    }
  }
}
```

### Verify Bundle Hash

```typescript
import { verifyBundleHash } from "@/evidence/validate";

async function checkBundleHash(manifest: ViewerPackManifestV1) {
  const result = await verifyBundleHash(manifest);

  if (!result.valid) {
    console.error("Bundle hash mismatch!");
    console.error("  Expected:", result.expected);
    console.error("  Actual:", result.actual);
  }
}
```

---

## 5. Vue Component Template

### Minimal Renderer Component

```vue
<template>
  <div class="my-renderer">
    <div class="header">
      <span class="kind">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-else class="content">
      <!-- Your visualization here -->
      <pre>{{ parsedData }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();
const error = ref<string | null>(null);

const parsedData = computed(() => {
  try {
    const text = new TextDecoder().decode(props.bytes);
    return JSON.parse(text);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    return null;
  }
});
</script>

<style scoped>
.my-renderer {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 1rem;
}

.header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.kind {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.path {
  color: #aaa;
  font-family: monospace;
}

.error {
  color: #f44;
  background: rgba(255, 68, 68, 0.1);
  padding: 1rem;
  border-radius: 4px;
}

.content pre {
  overflow: auto;
  max-height: 400px;
}
</style>
```

---

## 6. Testing Fixtures

### Creating Test ZIP in Python

```python
import io
import json
import zipfile

def create_test_pack() -> bytes:
    """Create minimal test viewer pack."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w") as zf:
        # Spectrum CSV
        csv_content = "freq_hz,H_mag,coherence,phase_deg\n10.5,0.001,0.95,-10\n"
        zf.writestr("spectra/points/A1/spectrum.csv", csv_content)

        # Manifest
        manifest = {
            "schema_version": "v1",
            "schema_id": "viewer_pack_v1",
            "created_at_utc": "2026-01-16T00:00:00Z",
            "measurement_only": True,
            "files": [
                {
                    "relpath": "spectra/points/A1/spectrum.csv",
                    "kind": "spectrum_csv",
                    "mime": "text/csv",
                    "bytes": len(csv_content),
                }
            ],
        }
        zf.writestr("manifest.json", json.dumps(manifest))

    return buf.getvalue()
```

### Vitest Test Example

```typescript
import { describe, it, expect } from "vitest";
import { loadNormalizedPack } from "@/evidence";

describe("viewer_pack_v1 loading", () => {
  it("loads minimal pack", async () => {
    // Create test file (use fixture or blob)
    const zipBytes = new Uint8Array([/* ... */]);
    const file = new File([zipBytes], "test.zip", { type: "application/zip" });

    const pack = await loadNormalizedPack(file);

    expect(pack.schema_id).toBe("viewer_pack_v1");
    expect(pack.files.length).toBeGreaterThan(0);
    expect(pack.files[0].kind).toBe("spectrum_csv");
  });
});
```

---

## Quick Commands

```bash
# tap-tone-pi: Export pack
python scripts/export/viewer_pack_v1_export.py \
  --session runs_phase2/session_XYZ \
  --out out/viewer_packs/session_XYZ.zip

# luthiers-toolbox: Run tests
npm run test --workspace=packages/client

# luthiers-toolbox: Type check
npm run type-check --workspace=packages/client

# luthiers-toolbox: Build
npm run build --workspace=packages/client
```

---

*Scaffolding guide for tap-tone-pi ↔ luthiers-toolbox integration.*
