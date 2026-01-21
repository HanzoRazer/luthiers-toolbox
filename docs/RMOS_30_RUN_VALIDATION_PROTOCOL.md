# RMOS 30-Run Validation Protocol

**Purpose:** Trust calibration, not QA.  
**Rule:** No new features during the 30 runs. Only fixes that preserve interfaces.  
**Exit Criteria:** No unexplained REDs, no unsafe GREENs, no nondeterminism, no repeated operator confusion.

---

## Protocol Summary

| Category | Runs | Goal | Expected Outcome |
|----------|------|------|------------------|
| A. Baseline Confidence | 1–10 | Prove repeatability | GREEN, no overrides |
| B. Edge-Pressure | 11–20 | Test feasibility boundaries | Mostly YELLOW, clear explanations |
| C. Adversarial | 21–30 | Validate safety authority | RED, hard blocks |

---

## Run Log Template

Copy this block for each run.

```
### Run #___

**Category:** [ ] A. Baseline  [ ] B. Edge-Pressure  [ ] C. Adversarial

**Date/Time:** ____________________
**Operator:** ____________________

---

#### Input

- **DXF/Design:** ____________________
- **Tool diameter (mm):** ____________________
- **Stepdown (mm):** ____________________
- **Stepover (mm):** ____________________
- **Feed XY (mm/min):** ____________________
- **Feed Z (mm/min):** ____________________
- **Other params:** ____________________

---

#### Outcome

- **Risk Level:** [ ] GREEN  [ ] YELLOW  [ ] RED
- **Run ID:** ____________________
- **Output Hash:** ____________________

---

#### Feasibility

- **Rules triggered:** ____________________
- **Explanation clear?** [ ] Yes  [ ] No  [ ] Partial
- **Override required?** [ ] Yes  [ ] No
- **Override reason (if any):** ____________________

---

#### Operator Notes

- **Did outcome match intuition?** [ ] Yes  [ ] No
- **Anything surprising?** ____________________
- **Hesitation before running?** [ ] Yes  [ ] No
- **If YELLOW: Was it justified?** [ ] Yes  [ ] No  [ ] N/A
- **If RED: Was block unambiguous?** [ ] Yes  [ ] No  [ ] N/A
- **Would junior operator understand?** [ ] Yes  [ ] No

---

#### Issues Found

- [ ] None
- [ ] Explanation gap: ____________________
- [ ] Unexpected behavior: ____________________
- [ ] Determinism concern: ____________________
- [ ] Other: ____________________
```

---

## Category A: Baseline Confidence Runs (1–10)

**Goal:** Prove repeatability. These should feel boring.

**Selection criteria:**
- Clean, well-formed DXFs
- Known-good geometries (simple pockets, standard rosettes)
- Conservative parameters (safe feeds, reasonable stepdown)
- Previously successful designs

**What you're validating:**
- Determinism (same input → same output hash)
- GREEN outcomes without surprises
- No hesitation before running

---

### Run #1

**Category:** [x] A. Baseline  [ ] B. Edge-Pressure  [ ] C. Adversarial

**Date/Time:** ____________________
**Operator:** ____________________

#### Input
- **DXF/Design:** ____________________
- **Tool diameter (mm):** ____________________
- **Stepdown (mm):** ____________________
- **Stepover (mm):** ____________________
- **Feed XY (mm/min):** ____________________
- **Feed Z (mm/min):** ____________________

#### Outcome
- **Risk Level:** [ ] GREEN  [ ] YELLOW  [ ] RED
- **Run ID:** ____________________
- **Output Hash:** ____________________

#### Feasibility
- **Rules triggered:** ____________________
- **Explanation clear?** [ ] Yes  [ ] No  [ ] Partial
- **Override required?** [ ] Yes  [ ] No

#### Operator Notes
- **Did outcome match intuition?** [ ] Yes  [ ] No
- **Anything surprising?** ____________________
- **Hesitation before running?** [ ] Yes  [ ] No

#### Issues Found
- [ ] None
- [ ] Issue: ____________________

---

### Run #2

**Category:** [x] A. Baseline  [ ] B. Edge-Pressure  [ ] C. Adversarial

**Date/Time:** ____________________
**Operator:** ____________________

#### Input
- **DXF/Design:** ____________________
- **Tool diameter (mm):** ____________________
- **Stepdown (mm):** ____________________
- **Stepover (mm):** ____________________
- **Feed XY (mm/min):** ____________________
- **Feed Z (mm/min):** ____________________

#### Outcome
- **Risk Level:** [ ] GREEN  [ ] YELLOW  [ ] RED
- **Run ID:** ____________________
- **Output Hash:** ____________________

#### Feasibility
- **Rules triggered:** ____________________
- **Explanation clear?** [ ] Yes  [ ] No  [ ] Partial
- **Override required?** [ ] Yes  [ ] No

#### Operator Notes
- **Did outcome match intuition?** [ ] Yes  [ ] No
- **Anything surprising?** ____________________
- **Hesitation before running?** [ ] Yes  [ ] No

#### Issues Found
- [ ] None
- [ ] Issue: ____________________

---

### Run #3–10

_(Copy the Run #1 template for runs 3–10)_

---

## Category B: Edge-Pressure Runs (11–20)

**Goal:** Test feasibility boundaries. These should feel uncomfortable.

**Selection criteria:**
- Tool diameter near smallest feature size
- Stepdown near safety threshold
- High feed_z relative to feed_xy
- Complex geometry (many loops, tight corners)
- Parameters that are "probably fine but worth checking"

**What you're validating:**
- YELLOW outcomes with justified warnings
- Explanations that actually help decision-making
- Overrides that feel intentional, not forced

---

### Run #11

**Category:** [ ] A. Baseline  [x] B. Edge-Pressure  [ ] C. Adversarial

**Date/Time:** ____________________
**Operator:** ____________________

#### Input
- **DXF/Design:** ____________________
- **Tool diameter (mm):** ____________________
- **Stepdown (mm):** ____________________
- **Stepover (mm):** ____________________
- **Feed XY (mm/min):** ____________________
- **Feed Z (mm/min):** ____________________
- **Edge condition tested:** ____________________

#### Outcome
- **Risk Level:** [ ] GREEN  [ ] YELLOW  [ ] RED
- **Run ID:** ____________________
- **Output Hash:** ____________________

#### Feasibility
- **Rules triggered:** ____________________
- **Explanation clear?** [ ] Yes  [ ] No  [ ] Partial
- **Override required?** [ ] Yes  [ ] No
- **Override reason:** ____________________

#### Operator Notes
- **Was YELLOW justified?** [ ] Yes  [ ] No  [ ] N/A
- **Did explanation help?** [ ] Yes  [ ] No
- **Would junior operator understand?** [ ] Yes  [ ] No
- **Hesitation notes:** ____________________

#### Issues Found
- [ ] None
- [ ] Explanation gap: ____________________
- [ ] Override felt forced: ____________________
- [ ] Other: ____________________

---

### Run #12–20

_(Copy the Run #11 template for runs 12–20)_

---

## Category C: Adversarial Runs (21–30)

**Goal:** Validate safety authority. These should make you uncomfortable.

**Selection criteria:**
- No closed geometry (open paths)
- Positive z_rough (cutting upward)
- Absurd stepover (>100% tool diameter)
- Nonsense feeds (extremely high or zero)
- Missing required parameters
- Geometry that cannot be machined

**What you're validating:**
- RED outcomes with hard blocks
- No workaround except correction
- Block reasons that are unambiguous

---

### Run #21

**Category:** [ ] A. Baseline  [ ] B. Edge-Pressure  [x] C. Adversarial

**Date/Time:** ____________________
**Operator:** ____________________

#### Input (Intentionally Bad)
- **DXF/Design:** ____________________
- **Bad condition tested:** ____________________
- **Parameters:** ____________________

#### Outcome
- **Risk Level:** [ ] GREEN  [ ] YELLOW  [ ] RED
- **Run ID:** ____________________
- **Blocked?** [ ] Yes  [ ] No

#### Safety Validation
- **Was block unambiguous?** [ ] Yes  [ ] No
- **Block reason:** ____________________
- **Could unsafe work proceed?** [ ] Yes (FAIL)  [ ] No (PASS)
- **Did you trust the block?** [ ] Yes  [ ] No

#### Issues Found
- [ ] None — correctly blocked
- [ ] Unsafe condition slipped through: ____________________
- [ ] Block reason unclear: ____________________
- [ ] Other: ____________________

---

### Run #22–30

_(Copy the Run #21 template for runs 22–30)_

---

## Summary Metrics

Complete after all 30 runs.

### Outcome Distribution

| Risk Level | Count | Percentage |
|------------|-------|------------|
| GREEN | ___ / 30 | ___% |
| YELLOW | ___ / 30 | ___% |
| RED | ___ / 30 | ___% |

### Override Frequency

| Category | Runs with Override | Override Rate |
|----------|-------------------|---------------|
| A. Baseline (1–10) | ___ / 10 | ___% |
| B. Edge-Pressure (11–20) | ___ / 10 | ___% |
| C. Adversarial (21–30) | ___ / 10 | ___% |

### Determinism Check

- **Repeat runs attempted:** ___
- **Hash matches:** ___
- **Hash mismatches:** ___ (list run IDs: _______________)

### Explanation Quality

| Question | Yes | No |
|----------|-----|-----|
| Explanations clear? | ___ | ___ |
| Junior would understand? | ___ | ___ |
| YELLOW justified? | ___ | ___ |
| RED unambiguous? | ___ | ___ |

### Hesitation Tracking

- **Runs with hesitation before execution:** ___
- **Common hesitation reasons:** ____________________

### Rule Trigger Frequency

| Rule | Times Triggered |
|------|-----------------|
| __________________ | ___ |
| __________________ | ___ |
| __________________ | ___ |
| __________________ | ___ |
| __________________ | ___ |

---

## Exit Criteria Checklist

All must be true to declare v1 validated.

- [ ] **No unexplained REDs** — Every RED has a clear, correct reason
- [ ] **No unsafe GREENs** — No GREEN outcome that should have been blocked
- [ ] **No nondeterministic outputs** — Same input → same hash
- [ ] **No repeated operator confusion** — Same confusion doesn't occur >2 times

### Validation Result

- [ ] **PASS** — v1 is validated for production use
- [ ] **FAIL** — Issues found, fixes required before re-validation

**Signed:** ____________________  
**Date:** ____________________

---

## Findings Summary (2-Page Note)

Complete after validation.

### What Surprised You

1. ____________________
2. ____________________
3. ____________________

### What Operators Hesitated On

1. ____________________
2. ____________________
3. ____________________

### Explanation Gaps Identified

1. ____________________
2. ____________________
3. ____________________

### Fixes Applied During Protocol

| Issue | Fix | Run # |
|-------|-----|-------|
| __________________ | __________________ | ___ |
| __________________ | __________________ | ___ |

### Recommendation

- [ ] Freeze v1 as-is
- [ ] Freeze v1 after minor fixes (list: _______________)
- [ ] Do not freeze — significant issues remain

---

## Next Steps After Validation

If **PASS**:
1. Declare RMOS v1 frozen
2. Tag `rmos-v1.0.0` release
3. Branch `rmos-v2` for future development
4. Decide on AI assist based on explanation gaps found

If **FAIL**:
1. Document issues
2. Apply fixes (interface-preserving only)
3. Re-run affected category
4. Repeat until PASS
