# Blueprint Reader Protection Rules

**Status:** ACTIVE GOVERNANCE  
**Effective:** 2026-05-11

---

## Protection Level

**LOCKED — Development Frozen**

The Blueprint Reader vectorizer is commercially viable and frozen. No modifications without explicit reactivation approval from Ross.

---

## Protected Systems

| System | Commit | Status |
|--------|--------|--------|
| Blueprint Reader MVP | `86c49526` | LOCKED |
| `restored_baseline` mode | `e3fb4792` | LOCKED |
| DXF compliance layer | dxf_compat | LOCKED |
| Scale validation gate | `validate_scale_before_export()` | LOCKED |

---

## Forbidden Actions

Agents may NOT:

1. **Modify extraction behavior** in any mode
2. **Remove or rename** `restored_baseline` mode
3. **Alter scale validation** thresholds
4. **Change DXF output format** for existing modes
5. **Add new modes** without reactivation approval
6. **Bypass validation gates** for any reason
7. **Integrate experimental features** into production path

---

## Permitted Actions

Agents MAY:

1. **Read** vectorizer code for understanding
2. **Document** existing behavior
3. **Create handoffs** describing current state
4. **Audit** for compliance
5. **Report** issues without fixing them

---

## Reactivation Protocol

If development resumes:

1. Explicit request from Ross required
2. Start from `restored_baseline` mode
3. Do not re-implement aggressive filtering
4. Test against Melody Maker PDF (regression indicator)
5. Document all changes in handoff

---

## Recovery Mode

If production breaks:

1. Switch to `restored_baseline` mode
2. Document the failure
3. Do not attempt fixes without reactivation approval

---

## Accuracy Baseline

| Instrument | Width Error | Height Error |
|------------|-------------|--------------|
| Dreadnought | 7.1% | 2.5% |
| Gibson Les Paul 59 | 16.5% | 19.7% |
| Cuatro Puertorriqueño | 2.6% | 2.6% |

This accuracy is **commercially sufficient** for starter templates.

---

*Blueprint Reader protection rules. Frozen for stability.*
