
<!-- PR Template for Luthier’s Tool Box -->
## Summary
<!-- What does this change? Why? -->

## Type
- [ ] Feature
- [ ] Bug fix
- [ ] Docs
- [ ] Refactor / chore
- [ ] Test / CI

## Screenshots / Artifacts (UI/CAM output)
<!-- Drop screenshots, SVGs, NC snippets as needed -->

## How to test
```bash
python scripts/smoke_cam_essentials.py || echo "optional"
```

## Breaking changes
- [ ] No
- [ ] Yes (explain)

## Linked issues
Closes #____ / Related #____

## Checklist
- [ ] Local tests/smoke pass
- [ ] Docs updated where needed
- [ ] For CAM posts/routers: include before/after output

---

## Governance Check — Wave Boundary

**Does this PR introduce interpretation beyond measurement display?**

- [ ] **No** — This PR is Wave 6A / 6B.1–safe
  (display, navigation, highlighting, exporter-provided fields only)

- [ ] **Yes** — This PR crosses into **Wave 7+ (interpretation)**
  (derived metrics, thresholds, ranking, inference, recommendations, or judgments)

If **Yes**, briefly describe:
- What interpretation is being introduced:
- Source of the interpretation logic (exporter / documented rule / new heuristic):
- Whether this is isolated behind a feature flag, mode, or separate surface:

---

### Reviewer reminder
If this PR adds:
- derived fields (score, risk, rank, severity)
- thresholds or judgmental language
- cross-artifact aggregation used to imply meaning

→ it **must** be treated as Wave 7+ and reviewed accordingly.
