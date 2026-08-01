# MB Sound Panel Corpus — Provenance

**Vendor:** Maderas Barber  
**Product line:** MB Sound  
**Runtime dataset:** [`mb_sound_panels.json`](./mb_sound_panels.json)  
**Field alignment:** provisional reuse of `TonewoodEntry` names — **not** specification authority  
**Namespace policy:** [`docs/reference/mb-sound/NAMESPACE.md`](../../../../../../../docs/reference/mb-sound/NAMESPACE.md) (non-authoritative)  
**Staging / evidence:** [`docs/reference/mb-sound/`](../../../../../../../docs/reference/mb-sound/)  
**Extraction playbook:** [`docs/reference/mb-sound/EXTRACTION_PLAYBOOK.md`](../../../../../../../docs/reference/mb-sound/EXTRACTION_PLAYBOOK.md)

## What this is

Per-piece tonewood characterization (tops and back/side sets) with listening samples, video, and measured acoustic parameters (density, stiffness, frequency response, etc.). Used here as a **panel-level validation corpus** for Gore-style plate math (`E∥`, `E⊥`, `ρ`, modes, thickness), not as a replacement for FPL/CIRAD species characterization in `wood_species.json`.

## What this is not

- Not species handbook averages  
- Not independent laboratory remeasure by this repo  
- Not licensed audio redistribution (store **metadata + numeric overlays** we extract; keep media references as URLs / local private paths)

## Public references (context)

- Program overview (third-party): https://luthiers.com/maderas-barber-s-mb-sound-revolutionizing-tonewood-selection-for-luthiers/  
- Example video discussion: https://www.youtube.com/watch?v=EUsiigk16Rs  
- Vendor catalog: Maderas Barber site → MB Sound section (exact listing URLs recorded per panel in `provenance.source_url`)

## Species mentioned in public MB Sound materials

Tops (as publicly described): Adirondack spruce, Alpine spruce, European spruce, red cedar.  
Backs/sides: Malaysian blackwood, Indian rosewood, American walnut.

Map each panel to `wood_species.json` via `species_id` when confident; leave `species_id` null if only a trade label is known.

## Policy

1. Extract numbers exactly as displayed; flag OCR uncertainty (`confidence`).  
2. Spanish UI labels → English schema fields per playbook glossary — do not “correct” vendor math.  
3. Prefer website data sheets over video OCR when both exist.  
4. Keep raw frames / OCR dumps under `docs/reference/mb-sound/staging/` (gitignored bulk binaries OK; commit small samples + JSONL).
