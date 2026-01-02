# Why Saw Lab Is Different (By Design)

Saw Lab operations often appear "simpler" than router-based CAM pipelines.

**This is intentional.**

---

## The Key Difference

Saw Lab operations are **deterministic machine executions**, not planning problems.

| Aspect | Router CAM | Saw Lab |
|--------|-----------|---------|
| Requires feasibility | Yes | No |
| Multi-stage planning | Yes | No |
| Heuristic optimization | Yes | No |
| Advisory generation | Yes | No |
| Deterministic output | No | Yes |

Saw Lab transforms **validated inputs → machine instructions** in a single pass.

---

## What This Means in Practice

1. Saw Lab still accepts `CamIntentV1`
2. It normalizes intent **once**
3. It does **not** interpret or optimize
4. It executes end-to-end by design

**This is not a shortcut — it is a different execution class.**

---

## Why This Matters

Blurring deterministic execution with planning logic:

- Introduces false complexity
- Creates artificial failure modes
- Breaks reproducibility

The ToolBox architecture explicitly separates:

1. **Intent normalization** — all operations
2. **Planning interpretation** — Class A only
3. **Deterministic execution** — Class B only

Saw Lab belongs to the last category.

---

## Rule of Thumb

> If the operation answers **"how should we do this?"** → Planning (Class A)
>
> If the operation answers **"do exactly this"** → Deterministic (Class B)

**Saw Lab always answers the second.**

---

## Execution Class Summary

| Class | Description | Example |
|-------|-------------|---------|
| **A** | Planning Operations | Router CAM, Rosette patterns |
| **B** | Deterministic Operations | CNC Saw Lab, Fixed drilling |

See: `OPERATION_EXECUTION_GOVERNANCE_v1.md` → Appendix D

---

## Status

- ✔ Governance-compliant
- ✔ Intent-normalized
- ✔ Artifact-persisted
- ✔ Correctly different

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `OPERATION_EXECUTION_GOVERNANCE_v1.md` | Full governance contract |
| `CNC_SAW_LAB_DEVELOPER_GUIDE.md` | Implementation guide |
| `ADR-003-cam-operation-lane-promotion.md` | Promotion plan for CAM endpoints |
