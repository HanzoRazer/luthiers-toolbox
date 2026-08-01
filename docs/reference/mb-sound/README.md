# Maderas Barber — MB Sound reference corpus

Panel-level tonewood measurements for validating plate / SRC math in Luthiers Toolbox.

| Doc | Purpose |
|-----|---------|
| [`NAMESPACE.md`](./NAMESPACE.md) | **Read first** — field authority / collision rules |
| [`EXTRACTION_PLAYBOOK.md`](./EXTRACTION_PLAYBOOK.md) | How to get ~60 samples without 60 hand screenshots |
| [`FIELD_GLOSSARY_ES_EN.md`](./FIELD_GLOSSARY_ES_EN.md) | Spanish UI → TonewoodEntry / `panel.*` |
| [`schema/panel.example.json`](./schema/panel.example.json) | Row template |
| [`staging/rows.jsonl`](./staging/rows.jsonl) | Staging extract rows |
| Runtime JSON | [`../../../services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json`](../../../services/api/app/data_registry/system/materials/panel_acoustic/mb_sound_panels.json) |

**Boundary:** does **not** replace `wood_species.json`. Does **not** decide Inv-026-A. Empty scaffold only; field-name reuse is provisional (see [`NAMESPACE.md`](./NAMESPACE.md)).
