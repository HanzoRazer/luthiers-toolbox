
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

### Wave Boundary Check (quick self-check)

This project distinguishes between:

- **Measurement display** (charts, highlighting, navigation, showing exporter fields)
- **Interpretation** (deriving meaning, scores, rankings, or recommendations)

Please check one:

- [ ] This PR stays within **measurement display**
  (no derived metrics, no scoring, no "good/bad" judgments)

- [ ] This PR begins to introduce **interpretation**
  (derived values, thresholds, rankings, or inferred meaning)

If you checked the second box, that's OK — just leave a short note below so reviewers
can route it correctly and help you land it safely.

> Tip: If you're unsure, reviewers are happy to help clarify where the boundary sits.
