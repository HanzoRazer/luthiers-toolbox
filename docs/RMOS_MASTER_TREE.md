# RMOS DEVELOPMENT TREE

**Legend:**
- `[x]` = complete
- `[ ]` = not started / in progress
- `(YOU ARE HERE)` = current active bundle

---

## RMOS

### Mainline (N-series)

#### N8 – Migration & Storage
- **[x] N8.1** Pattern store normalization
- **[x] N8.2** JobLog split (joblog_store + pattern_store)
- **[x] N8.3** Export pipelines (Plan → PDF/JSON + G-code)
- **[x] N8.4** Jig template exports
- **[x] N8.5** Full CAM pipeline integration
- **[x] N8.6** Persistent DB stores (patterns + joblog + strip families)
- **[x] N8.7** JSON → SQLite migration script
  - **[x] N8.7.1** Migration report (JSON/PDF)
  - **[x] N8.7.2** CI fail-on-mismatch
  - **[x] N8.7.3** Migration badge hook
  - **[x] N8.7.4** Migration dashboard viewer
  - **[x] N8.7.5** "Fix drift" wizard

#### N9 – Analytics & Artifacts
- **[x] N9.0** Core analytics engine + views
- **[x] N9.1** Strip Family Manager UI + planner binding
- **[x] N9.2** Promotion impact analytics
- **[x] N9.3** Live pipeline status polling
- **[x] N9.4** Artifact auto-preview (G-code/PDF/JSON) + websocket
- **[x] N9.5** Artifact classification + syntax highlight + thumbnails
- **[x] N9.6** Inline artifact editing + "promote result to preset"
- **[x] N9.7** Preset diff viewer (candidate vs parent)
- **[x] N9.8** Compare mode + rollback + A/B risk charts
- **[x] N9.9** Analytics consolidation patch

#### N10 – Real-Time Operations (LiveMonitor)
- **[x] N10.0** Live Monitor base (events + UI + RMOS sandbox)
- **[x] N10.1** Drill-down: subjobs, CAM events, heuristics
- **[x] N10.2** Apprenticeship mode + safety overrides
  - **[x] N10.2.1** Safety flow integration (preset promotion + pipeline run)
  - **[x] N10.2.2** Mentor override panel UI **(YOU ARE HERE)**
- **[ ] N10.3** Real-time operator warnings (feed/speed deviations)
- **[ ] N10.4** Live artifact snapshots during execution
- **[ ] N10.5** Router telemetry integration (optional future)

---

### Mixed-Material / Mosaic (MM-series)

#### Completed
- **[x] MM-1** Visual shader / preview layer for mixed materials
- **[x] MM-2** CAM profiles driven by materials (feeds/speeds/DOC/fragility)
- **[x] MM-3** PDF design sheets for mixed-material rosettes
- **[x] MM-4** Material-aware analytics (N9 integration)
- **[x] MM-5** Ultra-fragility promotion policy + lane gating
- **[x] MM-6** Fragility-aware LiveMonitor + badges + policy drawer

#### Pending / Innovation Queue
- **[ ] MM-7** Right-angle mosaic generator (pixel matrix → rod → tiles)
- **[ ] MM-8** Greek Key (Greca) generator
- **[ ] MM-9** Starburst / Spanish Cross generator
- **[ ] MM-10** Gradient / dithering pixel generator
- **[ ] MM-11** Moorish / Alhambra tessellation generator
- **[ ] MM-12** Braid / weave generator
- **[ ] MM-13** Triangular tessellation + hex-grid support
- **[ ] MM-14** Random fracture / Perlin-noise mosaics
- **[ ] MM-15** L-system fractal rosettes

---

### CI / Tooling / Automation
- **[x]** RMOS CI pack (tests + workflows)
- **[x]** Migration badge + health checks
- **[x]** JSON/SQLite diff checker
- **[x]** Artifact smoke tests (PDF/JSON/G-code)
- **[ ]** Operator-simulation suite
- **[ ]** CAM regression testing CI
- **[ ]** Promotion-policy regression suite
- **[ ]** Telemetry ingestion CI (router integration)

---

### Documentation & Onboarding
- **[x]** RMOS Developer Onboarding Guide
- **[x]** RMOS Glossary (patterns, presets, lanes, artifacts)
- **[x]** LiveMonitor User Guide
- **[x]** Drift Correction / N8.7.5 guide
- **[x]** Promotion Policy v2.0 document
- **[x]** Mixed-Material Guide (MM-1 → MM-6)
- **[ ]** Master Rosette Design Guide (after MM-7 ships)
- **[ ]** CAM Hand-Off Manual (examples + pipelines)
- **[ ]** Router Integration Playbook (if N10.5 is implemented)

---

### Future Capabilities (Ideas / Optional)
- **[ ]** Real CNC router control (USB / Ethernet)
- **[ ]** Multi-head rosette manufacturing automation
- **[ ]** Global tool library with material densities
- **[ ]** Non-rosette inlay pattern generators
- **[ ]** Bridge inlay tile generator
- **[ ]** Headstock mosaic generator
- **[ ]** Veneer optimizer (yield calculator)

---

## Maintenance Notes

**Moving the "You Are Here" marker:**  
When switching to a different active bundle, simply move the `(YOU ARE HERE)` tag to the appropriate line.

**Example:**
```markdown
- **[ ] N10.2** Apprenticeship mode + safety overrides **(YOU ARE HERE)**
```

**Updating completion status:**  
Change `[ ]` to `[x]` when a bundle is complete.
