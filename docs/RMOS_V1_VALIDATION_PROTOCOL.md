# RMOS v1 Validation Protocol

**Purpose**: Prove RMOS blocks unsafe operations and permits safe ones under real variance.
**Gate**: All 30 runs must pass before RMOS v1 can be declared released.
**Rule**: No feature changes during validation. Bugs only.

---

## Validation Matrix

### Tier 1: Baseline (10 runs)
Standard production scenarios. All should complete with expected decisions.

| # | Scenario | Input | Expected Decision | Actual | Pass |
|---|----------|-------|-------------------|--------|------|
| 1 | Simple pocket, softwood, conservative | 50x50mm pocket, pine, 3mm DOC | GREEN | | [ ] |
| 2 | Simple pocket, hardwood, conservative | 50x50mm pocket, maple, 2mm DOC | GREEN | | [ ] |
| 3 | Medium pocket, softwood | 100x80mm pocket, cedar, 3mm DOC | GREEN | | [ ] |
| 4 | Medium pocket, hardwood | 100x80mm pocket, walnut, 2mm DOC | GREEN/YELLOW | | [ ] |
| 5 | Deep pocket, softwood | 50x50mm, 15mm deep, pine | YELLOW (review depth) | | [ ] |
| 6 | Island geometry, softwood | Pocket with 20mm island, pine | GREEN | | [ ] |
| 7 | Island geometry, hardwood | Pocket with 20mm island, maple | GREEN/YELLOW | | [ ] |
| 8 | Multi-pocket, softwood | 3 pockets, pine, standard params | GREEN | | [ ] |
| 9 | Thin wall, conservative | 2mm wall, pine, 1mm DOC | YELLOW (thin wall warning) | | [ ] |
| 10 | Standard rosette pocket | Typical rosette dims, spruce | GREEN | | [ ] |

**Baseline Pass Criteria**:
- All GREEN scenarios return GREEN
- All YELLOW scenarios return YELLOW with correct rule IDs
- No RED unless geometry is actually unsafe
- Operator Pack exports work for all GREEN runs

---

### Tier 2: Edge Pressure (10 runs)
Push boundaries without crossing into unsafe. Tests rule sensitivity.

| # | Scenario | Input | Expected Decision | Actual | Pass |
|---|----------|-------|-------------------|--------|------|
| 11 | Max safe DOC, softwood | 5mm DOC (at limit), pine | YELLOW | | [ ] |
| 12 | Max safe DOC, hardwood | 3mm DOC (at limit), maple | YELLOW | | [ ] |
| 13 | Minimum tool diameter | 1.5mm endmill, appropriate WOC | YELLOW | | [ ] |
| 14 | Maximum pocket depth | 25mm deep (near limit), pine | YELLOW/RED | | [ ] |
| 15 | Narrow slot | 4mm wide slot, 10mm deep | YELLOW (slot ratio) | | [ ] |
| 16 | Complex island | L-shaped island, hardwood | YELLOW | | [ ] |
| 17 | Thin floor | 1.5mm floor thickness | YELLOW (thin floor) | | [ ] |
| 18 | High feed override | 150% feed rate request | YELLOW (feed warning) | | [ ] |
| 19 | Aggressive stepover | 80% WOC request | YELLOW (stepover warning) | | [ ] |
| 20 | Combined pressure | Deep + thin wall + hardwood | YELLOW/RED | | [ ] |

**Edge Pressure Pass Criteria**:
- No GREEN for any edge case (system should warn)
- YELLOW includes relevant rule IDs in explanation
- RED only for genuinely unsafe combinations
- WhyPanel shows correct triggered rules

---

### Tier 3: Adversarial (10 runs)
Intentionally unsafe inputs. RMOS must block these.

| # | Scenario | Input | Expected Decision | Actual | Pass |
|---|----------|-------|-------------------|--------|------|
| 21 | Excessive DOC | 15mm DOC in hardwood | RED | | [ ] |
| 22 | Tool breakage risk | 1mm endmill, 10mm DOC | RED | | [ ] |
| 23 | Impossible geometry | Pocket deeper than material | RED | | [ ] |
| 24 | Zero/negative dims | 0mm pocket width | RED (validation) | | [ ] |
| 25 | Missing material | No material specified | RED (incomplete) | | [ ] |
| 26 | Incompatible tool | 12mm endmill in 8mm pocket | RED | | [ ] |
| 27 | Chatter-inducing | Long thin tool, deep cut, hardwood | RED | | [ ] |
| 28 | Thermal risk | Tiny tool, no coolant, resinous wood | RED/YELLOW | | [ ] |
| 29 | Structural failure | 0.5mm wall, deep pocket | RED | | [ ] |
| 30 | Combined adversarial | Multiple unsafe params | RED | | [ ] |

**Adversarial Pass Criteria**:
- ALL must return RED (or validation error)
- Operator Pack export MUST be blocked
- Explanation includes blocking rule IDs
- No override allowed without explicit RED override flag

---

## Validation Execution Checklist

### Pre-Validation
- [ ] All code frozen (commit hash: _____________)
- [ ] Test environment clean
- [ ] Runs directory empty or archived
- [ ] WhyPanel functional
- [ ] Override flow functional

### During Validation
- [ ] Record each run's actual decision
- [ ] Screenshot WhyPanel for YELLOW/RED runs
- [ ] Verify Operator Pack export blocked for RED
- [ ] Note any unexpected behavior (even if "pass")

### Post-Validation
- [ ] All 30 checkboxes marked
- [ ] Zero RED leaks (adversarial returned GREEN)
- [ ] Zero false blocks (baseline GREEN returned RED)
- [ ] Anomalies documented and triaged

---

## Pass/Fail Criteria

### PASS (Release Authorized)
- 30/30 runs match expected decision category
- Zero unsafe operations permitted (no RED→GREEN leaks)
- Explanations accurate for all YELLOW/RED
- Operator Pack correctly gated

### CONDITIONAL PASS
- 28-29/30 with documented edge cases
- Failures are conservative (over-blocking, not under-blocking)
- Issues logged for v1.1 patch

### FAIL (Release Blocked)
- Any adversarial run returns GREEN
- Any baseline run incorrectly blocked as RED
- Explanation missing or wrong for decisions
- Operator Pack exports when it shouldn't

---

## Validation Log

| Date | Run # | Tester | Result | Notes |
|------|-------|--------|--------|-------|
| | | | | |
| | | | | |
| | | | | |

---

## Sign-Off

**Validation Complete**: [ ] Yes / [ ] No
**Release Authorized**: [ ] Yes / [ ] No
**Validated By**: _______________________
**Date**: _______________________
**Commit Hash**: _______________________

---

*This protocol gates RMOS v1 release. No exceptions.*
