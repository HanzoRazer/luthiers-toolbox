# Maderas Barber — MB Sound reference corpus

Panel-level tonewood measurements for validating plate / SRC math in Luthiers Toolbox.

| Doc | Purpose |
|-----|---------|
| [`NAMESPACE.md`](./NAMESPACE.md) | **Read first** — provisional field alignment / collision rules |
| [`LINKAGE.md`](./LINKAGE.md) | Numbered cards vs **unnumbered** spectral frames |
| [`EXTRACTION_PLAYBOOK.md`](./EXTRACTION_PLAYBOOK.md) | Batch extract path |
| [`FIELD_GLOSSARY_ES_EN.md`](./FIELD_GLOSSARY_ES_EN.md) | Vendor UI → TonewoodEntry / `panel.*` |
| [`schema/panel.example.json`](./schema/panel.example.json) | First real row shape |
| [`staging/rows.jsonl`](./staging/rows.jsonl) | Staging extract rows |
| Runtime JSON | [`../../../services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json`](../../../services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json) |

**Boundary:** does **not** replace `wood_species.json`. Does **not** decide Inv-026-A. Empty scaffold only; field-name reuse is provisional (see [`NAMESPACE.md`](./NAMESPACE.md)).
