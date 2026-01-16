# Wave 6A Code Bundle (Safe Sync / Linked Cursor) — SPEC IMPLEMENTATION

This bundle contains **code changes** to add Wave 6A “linked cursor” plumbing to the Audio Analyzer Viewer.

## What this bundle implements

- Viewer-owned `EvidenceSelection` state (cursor): `{ pointId, freqHz, source }`
- Cursor persists across file switches until cleared
- No manual frequency entry
- Renderers receive `selection` as a prop
- `SpectrumChartRenderer`:
  - emits `select` on peak click
  - draws a vertical cursor line at `selection.freqHz` (exact value)

## What this bundle does NOT implement

- Any interpretation / scoring / filtering (Wave 6B)
- Audio time seeking (no time offsets exist)
- WSI / TransferFunction cursor highlighting (can be added next)

## Files

- `packages/client/src/tools/audio_analyzer/selection.ts` (new)
- `packages/client/src/tools/audio_analyzer/renderers/types.ts` (update)
- `packages/client/src/tools/audio_analyzer/AudioAnalyzerViewer.vue` (update)
- `packages/client/src/tools/audio_analyzer/renderers/SpectrumChartRenderer.vue` (update)

## Apply

Copy the files into your repo at the same paths, or apply the changes manually by diffing against your current HEAD.

If you want this as a git patch instead, tell me what your current file contents look like for the 3 edited files and I’ll generate a clean `git apply` patch.
