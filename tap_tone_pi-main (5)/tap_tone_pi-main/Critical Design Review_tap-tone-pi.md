I'll extract and examine the project thoroughly before providing my critical design review.Now I have a comprehensive understanding of the project. Let me compile my critical design review.

---

# Critical Design Review: tap-tone-pi

## Stated Assumptions

Before scoring, I'm stating my assumptions about this design:

1. **Target User**: Luthiers (guitar builders) with moderate technical ability—comfortable with command lines but not necessarily software engineers
2. **Operating Environment**: Primarily Raspberry Pi in workshop settings, secondarily desktop (dev/analysis)
3. **Hardware Integration**: USB microphones, serial load cells/dial indicators, potentially noisy electrical environments
4. **Data Integrity Requirement**: Measurement provenance must be defensible for comparing builds over time
5. **Integration Context**: Outputs feed into a larger "Luthier's ToolBox" ecosystem (this repo is measurement-only, not advisory)
6. **Development Stage**: Late alpha / early beta—functional but not production-hardened

---

## Category Evaluations

### 1. Purpose Clarity
**Score: 9/10**

**Justification**: The project demonstrates exceptional clarity of purpose. The README, MEASUREMENT_BOUNDARY.md, and GOVERNANCE.md hammer home the "measurement-only" doctrine repeatedly. The explicit "IS / IS NOT" section prevents scope creep magnificently. The architectural decision records (ADR-0001 through ADR-0007) document the reasoning behind technical choices.

**Strengths**:
- Crystal-clear "measurement instruments, not opinions" philosophy
- Explicit contract between this repo and downstream systems (ToolBox/RMOS)
- CI guardrails that enforce the boundary (no_logic_creep.yml blocks advisory imports)

**Improvements**:
- Add a visual system diagram in README showing data flow from capture → analysis → export
- Include a one-paragraph "elevator pitch" for non-technical stakeholders

---

### 2. User Fit
**Score: 6/10**

**Justification**: The target user (luthier with workshop) faces friction. The system assumes comfort with CLI, PYTHONPATH configuration, and reading JSON schemas. The Tkinter GUI exists but feels like an afterthought—it shells out to Python scripts rather than providing native integration.

**Strengths**:
- Multiple interface options (CLI, GUI, Makefile targets)
- Simulated modes allow exploration without hardware
- Explicit device enumeration (`devices` command)

**Weaknesses**:
- No wizard for first-time setup (audio device selection, calibration verification)
- GUI requires users to know output paths, run IDs, and JSON config structure
- Error messages are developer-oriented (subprocess exit codes) not user-oriented
- Phase 2's 35-point grid capture requires physical dexterity + software coordination—no guided workflow

**Improvements**:
- Implement a "first run" wizard that validates audio setup and persists device preferences
- Add progress indicators and human-readable status messages in GUI
- Create step-by-step tutorial documents with photos for physical setup
- Consider a web-based local interface (Flask/FastAPI + lightweight frontend) for better UX than Tkinter

---

### 3. Usability
**Score: 5/10**

**Justification**: The system is usable by developers but presents significant friction for target users. The CLI is well-structured with argparse, but the multi-repo mental model (tap_tone/, tap-tone-lab/, modes/, scripts/phase2/) creates confusion. The Makefile provides 20+ targets but lacks discoverability.

**Strengths**:
- Consistent CLI patterns (`--help` works everywhere)
- Makefile with sensible defaults
- Synthetic mode allows practice without hardware

**Weaknesses**:
- Duplicate code between `tap_tone/` and `tap-tone-lab/tap_tone/` creates confusion
- `scripts/phase2/` vs `modes/` distinction is non-obvious to users
- No tab-completion support
- Output directory structure (session_YYYYMMDD/derived/points/) requires users to understand the data model
- No "last session" shortcut—users must navigate timestamp directories

**Improvements**:
- Consolidate to single canonical package location
- Add `tap-tone last` command to open most recent session
- Implement shell completion scripts (bash/zsh/fish)
- Create a "session browser" that shows past captures with thumbnails
- Add `--quiet` and `--verbose` flags consistently across all commands

---

### 4. Reliability
**Score: 7/10**

**Justification**: The architecture shows careful attention to data integrity (SHA256 hashes, schema validation, provenance tracking), but runtime reliability has gaps. Error handling is inconsistent, and hardware failure modes aren't gracefully handled.

**Strengths**:
- Bundle hashing (bundle_sha256.txt) ensures artifact integrity
- Schema versioning with explicit validation
- Immutable artifact doctrine prevents data corruption
- Session-level JSONL logging for debugging

**Weaknesses**:
- No retry logic for serial device failures
- Audio capture doesn't handle device disconnection gracefully
- Schema validation is optional (jsonschema in dev dependencies only)
- No watchdog for hung captures
- No automatic recovery from partial session failures

**Improvements**:
- Move jsonschema to core dependencies and validate all outputs before persisting
- Implement device health checks before capture sequences
- Add capture timeout with graceful failure and session recovery
- Create "session repair" tool for interrupted captures (partially implemented in test fixtures)
- Log hardware state (device IDs, sample rates) in every session for debugging

---

### 5. Manufacturability / Maintainability
**Score: 8/10**

**Justification**: The codebase is well-organized with clear module boundaries, dataclasses for structured data, and type hints throughout. The CI pipeline is comprehensive. However, the test coverage gap (55%) and duplicate code paths create maintenance burden.

**Strengths**:
- Type hints on all public APIs
- Frozen dataclasses prevent accidental mutation
- 6 CI workflows with path-based triggers
- JSON schemas as machine-readable contracts
- Explicit dependency versions in pyproject.toml

**Weaknesses**:
- Test coverage at 55% (self-reported), missing Phase 2 DSP unit tests
- Duplicate implementations (tap_tone/ vs tap-tone-lab/tap_tone/)
- pyproject.toml version stuck at 0.1.0 despite v2.0 release tag
- No pre-commit hooks for consistent formatting
- poetry.lock present but pyproject.toml uses setuptools (tooling mismatch)

**Improvements**:
- Add pre-commit config with black/isort/mypy
- Achieve 80%+ test coverage, especially for DSP modules
- Consolidate duplicate packages with deprecation warnings
- Automate version bumping from git tags
- Add CHANGELOG.md following Keep a Changelog format

---

### 6. Cost
**Score: 8/10**

**Justification**: The BOM is reasonable—Raspberry Pi + USB microphone + standard shop tools. Dependencies are pure Python with no expensive licensed components. The main cost is user time, which is high due to usability friction.

**Strengths**:
- No proprietary software dependencies
- Works on consumer-grade hardware
- Simulators allow evaluation without any hardware investment
- Standard Python stack (numpy/scipy) has broad ecosystem support

**Weaknesses**:
- Phase 2 requires two-channel audio interface (additional ~$50-150)
- Serial load cell/dial indicator integration requires specific hardware
- Learning curve represents significant time investment

**Improvements**:
- Document BOM with specific product recommendations and approximate costs
- Create "minimal viable setup" guide for Phase 1 with exact hardware links
- Add cost-benefit analysis for Phase 2 vs Phase 1 for different user profiles

---

### 7. Safety
**Score: 9/10**

**Justification**: This is primarily a data acquisition system with minimal safety concerns. The measurement-only doctrine prevents the system from providing potentially dangerous advice. Data integrity protections prevent corrupted measurements from propagating.

**Strengths**:
- Explicit "does not advise" boundary prevents safety-critical misuse
- Immutable artifacts prevent tampering
- No network exposure in normal operation
- Clipping detection prevents invalid acoustic measurements

**Weaknesses**:
- No warnings about hearing damage from tap-tone testing at high volumes
- Serial port access could theoretically interact with other shop equipment
- No input sanitization on file paths (shell injection possible in GUI)

**Improvements**:
- Add SPL warning in documentation for tap-tone testing
- Sanitize all user inputs before shell operations (use subprocess lists, not shell=True)
- Add file path validation to prevent directory traversal

---

### 8. Scalability
**Score: 6/10**

**Justification**: The system handles single-instrument workflows well but lacks infrastructure for fleet management, parallel processing, or long-term data aggregation. This is appropriate for a workshop tool but limits growth.

**Strengths**:
- File-based storage avoids database complexity
- Session isolation prevents cross-contamination
- Schema versioning supports format evolution
- Export contracts enable downstream integration

**Weaknesses**:
- No database for querying historical measurements
- No multi-instrument comparison tools built-in
- Session directories grow unbounded (no archival/cleanup)
- Phase 2's 35-point capture is linear (no parallel mic support)
- No cloud backup/sync mechanism

**Improvements**:
- Add SQLite index for session metadata queries
- Implement session archival with configurable retention
- Create comparison reports across sessions (same specimen, different dates)
- Document integration patterns for enterprise lutherie shops
- Consider optional cloud sync for backup (e.g., rclone integration)

---

### 9. Aesthetics (GUI/Output Quality)
**Score: 4/10**

**Justification**: The Tkinter GUI is functional but dated. Plot outputs are matplotlib defaults without branding or polish. JSON outputs are machine-readable but not presentation-ready.

**Strengths**:
- Matplotlib plots are technically correct
- JSON outputs are well-structured
- PDF report generation exists (sample_bundle_report.pdf)

**Weaknesses**:
- Tkinter GUI has no visual hierarchy or modern styling
- No dark mode support
- Plot aesthetics are default matplotlib (no custom color schemes)
- No branded templates for reports
- Session directories have cryptic names (session_20260101T234237Z)

**Improvements**:
- Apply ttk themes or migrate to CustomTkinter for modern appearance
- Create a style guide for plots (consistent colors, fonts, branding)
- Generate human-readable session names (e.g., "spruce-top-2026-01-15")
- Add report templates with professional formatting (ReportLab or WeasyPrint)
- Include thumbnail previews in session directories

---

## Summary Scorecard

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Purpose Clarity | 9 | 1.0 | 9.0 |
| User Fit | 6 | 1.5 | 9.0 |
| Usability | 5 | 1.5 | 7.5 |
| Reliability | 7 | 1.5 | 10.5 |
| Maintainability | 8 | 1.0 | 8.0 |
| Cost | 8 | 0.5 | 4.0 |
| Safety | 9 | 1.0 | 9.0 |
| Scalability | 6 | 0.5 | 3.0 |
| Aesthetics | 4 | 0.5 | 2.0 |
| **Total** | | **9.0** | **62.0/90 = 69%** |

---

## Top 5 Priority Improvements

1. **Consolidate duplicate packages** (tap_tone/ vs tap-tone-lab/) and establish single canonical import path—this is creating confusion and maintenance burden

2. **Implement first-run setup wizard** with audio device detection, test capture, and configuration persistence—critical for user adoption

3. **Increase test coverage to 80%+** with focus on DSP modules (dsp.py, metrics.py)—these are the core value proposition and currently have minimal unit tests

4. **Modernize GUI or provide web alternative**—Tkinter implementation is limiting user experience and professional perception

5. **Add session management tools** (list, browse, compare, archive)—users currently must navigate cryptic timestamp directories manually


I'll append these feature suggestions to the evaluation as a concrete roadmap section.

---

## Appendix: Feature Roadmap for Desktop Analyzer Completion

Based on the v1.0.0 baseline and the critical review above, here are prioritized feature suggestions to finish the desktop analyzer. These align with the identified gaps in **User Fit (6/10)**, **Usability (5/10)**, and **Aesthetics (4/10)**.

---

### Feature 1: GUI Polish (gui/app.py)
**Priority: HIGH** | **Effort: Medium** | **Addresses: Usability, Aesthetics**

The current GUI (~297 lines, Tkinter) is functional but minimal. Complete it with:

| Component | Current State | Target State |
|-----------|--------------|--------------|
| Device selector | Manual index entry | Dropdown with device names |
| Spectrum display | Static PNG after capture | Real-time waterfall during capture |
| Peak visualization | None | Overlay markers on spectrum |
| Session browser | None | Sidebar with recent sessions |
| Export | Manual file navigation | One-click "Export to Viewer Pack" |

**Implementation Notes**:
- Consider `matplotlib.animation` for real-time spectrum
- Use `ttk.Treeview` for session browser
- Add `tkinter.ttk` themes for modern appearance

---

### Feature 2: Phase 2 GUI Integration
**Priority: MEDIUM** | **Effort: High** | **Addresses: User Fit, Usability**

Phase 2 is currently CLI-only (`scripts/phase2_slice.py`). Add visual feedback:

| Component | Description |
|-----------|-------------|
| Grid point map | Show captured (green) vs pending (gray) vs failed (red) |
| ODS heatmap | Interactive frequency slider → magnitude heatmap at that Hz |
| Coherence indicator | Traffic light showing coherence threshold status |
| Wolf annotations | Highlight wolf candidates on grid with frequency labels |

**Implementation Notes**:
- Leverage existing `viz.py` module in `scripts/phase2/`
- Grid coordinates already available in `config/grids/guitar_top_35pt.json`
- Consider embedded matplotlib canvas or separate window

---

### Feature 3: Live Mode Enhancements
**Priority: HIGH** | **Effort: Medium** | **Addresses: Usability, Reliability**

Current live mode is a simple loop. Enhance with:

| Feature | Benefit |
|---------|---------|
| Real-time FFT with rolling average | Reduces noise, shows stable peaks |
| Peak stability indicator | Distinguishes consistent modes from transients |
| Audio level meter | Prevents clipping before it happens |
| Auto-trigger on transient | "Good tap" detection eliminates manual timing |

**Implementation Notes**:
- Use ring buffer for rolling FFT average
- Transient detection: threshold on RMS derivative
- Level meter: simple VU-style bar updated at ~30fps

---

### Feature 4: Session Management Panel
**Priority: MEDIUM** | **Effort: Medium** | **Addresses: Usability, Scalability**

Currently users navigate cryptic `session_YYYYMMDDTHHMMSS/` directories. Add:

| Feature | Description |
|---------|-------------|
| Session browser | List `runs_phase2/` and `out/` sessions with metadata |
| Side-by-side compare | Select two sessions, show diff in peaks/coherence |
| Archive/delete | Move old sessions to archive folder or delete |
| Quick stats | Point count, mean coherence, dominant frequencies |

**Implementation Notes**:
- Parse `session_manifest.jsonl` for metadata
- Store comparison results as new artifact type
- Add confirmation dialog for destructive operations

---

### Feature 5: Export UX
**Priority: LOW** | **Effort: Low** | **Addresses: Usability**

Export is functional but opaque. Improve with:

| Feature | Description |
|---------|-------------|
| Progress bar | Show ZIP creation progress for large sessions |
| Validation preview | Run schema validation and show pass/fail before export |
| "Open in ToolBox" | If ToolBox server detected, offer direct handoff |

**Implementation Notes**:
- Use `tkinter.ttk.Progressbar`
- Leverage existing `validate_viewer_pack_v1.py`
- ToolBox detection: check for localhost:8000 or configured endpoint

---

### Feature 6: Hardware Setup Wizard
**Priority: HIGH** | **Effort: Medium** | **Addresses: User Fit, Reliability**

No first-run experience exists. Create guided setup:

| Step | Action |
|------|--------|
| 1. Device scan | List available audio devices with channel counts |
| 2. Device selection | User picks input device from dropdown |
| 3. Test recording | 2-second capture with playback |
| 4. Level check | Show peak level, warn if too low/high |
| 5. Save config | Persist to `~/.tap_tone_pi/config.json` |

**Implementation Notes**:
- Run on first launch or via menu item
- Store device index + name (handle device reordering)
- Include "Re-run wizard" option in settings

---

### Recommended Implementation Order

Given the current stable DSP core, focus on **user-facing polish** without touching signal processing:

```
Phase A (Quick Wins - 1-2 weeks)
├── Feature 3: Live Mode Enhancements ← Day-to-day workflow improvement
└── Feature 6: Hardware Setup Wizard ← First-run experience

Phase B (Core UX - 2-4 weeks)
├── Feature 1: GUI Polish ← Make capture workflow feel finished
└── Feature 4: Session Management ← Reduce friction for repeat users

Phase C (Advanced - 4+ weeks)
├── Feature 2: Phase 2 GUI Integration ← Complex, can remain CLI for now
└── Feature 5: Export UX ← Nice-to-have, low priority
```

---

### Current GUI State Reference

The existing `gui/app.py` (297 lines) provides:
- Run ID entry field
- Tap-tone live/offline capture buttons
- MOE single/batch calculation
- Provenance hash generation
- Load cell and dial indicator serial capture
- Manifest emission
- Chladni Wizard (multi-step workflow)

**What's Missing** (per Feature 1):
- No device dropdown (requires manual index)
- No real-time visualization (static post-capture only)
- No session browsing (requires manual file navigation)
- No integrated export workflow

The foundation exists—the GUI successfully orchestrates the underlying scripts. The gap is **feedback and discoverability**, not functionality.

---

### Updated Summary Scorecard (Post-Roadmap)

If Features 1, 3, and 6 are implemented:

| Category | Current | Projected | Delta |
|----------|---------|-----------|-------|
| User Fit | 6 | 8 | +2 |
| Usability | 5 | 7 | +2 |
| Aesthetics | 4 | 6 | +2 |
| **Overall** | **69%** | **78%** | **+9%** |

The DSP core is solid. The path to a "finished" desktop analyzer is primarily UI/UX work.