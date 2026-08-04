# Instrument-building physics — knowledge index

**Lane:** Mechanisms and quantities that travel across shops.  
**Sibling lane:** [`SHOP_BUILDING_KNOWLEDGE_INDEX.md`](./SHOP_BUILDING_KNOWLEDGE_INDEX.md)  
**Developer entry:** [`KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md`](./KNOWLEDGE_PACK_DEVELOPER_ORIENTATION.md)  
**Gore-centric living summary (subset of this lane):** [`GORE_LECTURE_SERIES_SUMMARY.md`](./GORE_LECTURE_SERIES_SUMMARY.md)

## What belongs here

Energy budget, radiation paths, modes (monopole / dipoles / air), stiffness–mass–mobility, top–air–back coupling, scale/tension, intonation mechanics, material figures of merit (\(E/\rho\), SRC, Q), FRF/Chladni as *measurement of physics*.

**Deliverable for Toolbox:** meters, models, lab SOPs, unit profiles — still **NO-CALC** until gaps close.

**Canonical equation hub:** [`docs/LUTHERIE_MATH.md`](../../LUTHERIE_MATH.md) (Appendix B wires MB/TPC + Holmberg inputs into existing § / `plate_design` / `soundhole_calc` — no parallel engines).  
**Unfinished §§ handoff:** [`docs/handoffs/LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md`](../../handoffs/LUTHERIE_MATH_UNFINISHED_SECTIONS_DEV_HANDOFF_2026-08-04.md)

**Dual-file (shop primary):** Bashkin open/closed-box FRF voicing gates — [`shop_bashkin_jm_build_workflow/`](./shop_bashkin_jm_build_workflow/) BK33/BK37–BK39 (no Hz targets recorded).

**Shop cross-link (intonation setup, not a physics pack):** Schaefer compensated saddle — [`shop_schaefer_compensated_saddle/`](./shop_schaefer_compensated_saddle/) SC22–SC33 (cents ear band, 12th-fret method, envelope/transient, steel harmonics). Pair with Gore P25–P26 / H09; do not invent break-point mm (**G-SC02**).

**Does not belong here:** factory vs hand process lore, billet storytelling, client interviews, “play the guitar not the label,” species marketing folklore (those → shop lane). Overlap sentences (“light and stiff”) may appear in both; tag by *deliverable*.

## Packs in this lane

### Gore / O’Brien (priority-stack school)

| Pack | Path | Notes |
|------|------|-------|
| Shop Talk #20 | [`gore_shop_talk_20/`](./gore_shop_talk_20/) | P01–P38 |
| Wolf mailbag | [`gore_wolf_notes_mailbag/`](./gore_wolf_notes_mailbag/) | W01–W09 |
| Monopole mobility tip | [`gore_monopole_mobility_measurement/`](./gore_monopole_mobility_measurement/) | M01–M12 |
| Shop Talk #25 | [`gore_shop_talk_25/`](./gore_shop_talk_25/) | S01–S21 |
| Responsive objectives | [`gore_shop_talk_responsive_objectives/`](./gore_shop_talk_responsive_objectives/) | R + **G-R01** |
| Guitar Analysis & Testing | [`gore_guitar_analysis_testing/`](./gore_guitar_analysis_testing/) | **PARTIAL** |
| Shop Talk #44 | [`gore_shop_talk_44/`](./gore_shop_talk_44/) | U01–U23 |
| Shop Talk #51 Academy apps | [`gore_shop_talk_51_luther_academy_apps/`](./gore_shop_talk_51_luther_academy_apps/) | A01–A29 |

### Nicoletti (measurement / tonewood physics)

| Pack | Path | Notes |
|------|------|-------|
| Tonewood parameters webinar | [`nicoletti_tonewood_parameters_webinar/`](./nicoletti_tonewood_parameters_webinar/) | N69–N99 |
| EGB measuring/tuning 2022 | [`nicoletti_egb_measuring_tuning_2022/`](./nicoletti_egb_measuring_tuning_2022/) | N100–N130 |
| Science / Luthier Stories | [`nicoletti_science_luthier_stories/`](./nicoletti_science_luthier_stories/) | N43–N68 — physics primer + ETS/TPC (shop-adjacent tools) |

### Survey / doctrine with physics payload

| Pack | Path | Notes |
|------|------|-------|
| Howman — Physics Mind (Curtin 2011) | [`physics_mind_steel_string_lecture/`](./physics_mind_steel_string_lecture/) | PM01–PM36 — public seminar survey |
| Somogyi 01 — Air pump / bracing / tap | [`somogyi_01_air_pump_bracing_tap_tone/`](./somogyi_01_air_pump_bracing_tap_tone/) | ES01–ES15 — efficiency doctrine |
| Somogyi 02 — Top & Back | [`somogyi_02_top_and_back/`](./somogyi_02_top_and_back/) | ES16–ES28 — coupled-box doctrine |


### Plate flexibility / deflection

| Pack | Path | Notes |
|------|------|-------|
| Garrett Lee Ep. 13 — plate deflection | [`garrett_lee_soundboard_deflection_ep13/`](./garrett_lee_soundboard_deflection_ep13/) | GL01–GL28 — deflection SOP; t³ behavior; targets gap G-GL01; shop thinning dual-file |
### Brace-beam mechanics

| Pack | Path | Notes |
|------|------|-------|
| Jacob / Kanaka — I-beam bracing | [`jacob_ibeam_bracing_physics/`](./jacob_ibeam_bracing_physics/) | IB01–IB24 — cube/height, I-beam demos, steel X application (shop dual-file) |

### Spreadsheet / equation implementations (calculator-port)

| Pack | Path | Notes |
|------|------|-------|
| Holmberg — Gore/Gilet modeling spreadsheets | [`holmberg_gore_modeling_spreadsheets/`](./holmberg_gore_modeling_spreadsheets/) | HM01–HM49 — docs + xlsx inventory + **tab-by-tab evaluation**; **G-HM01/02 closed**; **G-HM03/04/07/10–14** open |

### Panel lab corpora (TPC / MB Sound)

| Pack | Path | Notes |
|------|------|-------|
| MB Sound — Nicoletti TPC panel laboratory records | [`mb_sound_panel_laboratory_records/`](./mb_sound_panel_laboratory_records/) | MB01–MB28 — Alpine / Red Cedar / Torrefied ADK / 30-yr cedar; **tab-by-tab**; kit SOP ≠ panel books; **G-MB01–08** |

## Standing physics blockers

See orientation §4 and Gore summary “Known absence.” Lead item: **G-R01 / G-M09** mobility δ unit profile. Holmberg mobility citations (**HM31**) stay badge-blocked on the same gap (**G-HM04**).
