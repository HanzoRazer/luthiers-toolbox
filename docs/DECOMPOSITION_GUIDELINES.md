# Vue Component Decomposition Guidelines

## LOC Targets

| Component Type | Max LOC | Notes |
|----------------|---------|-------|
| Main/orchestrator component | 400 | Imports + wiring only |
| Child component | 200 | Single responsibility |
| Composable | 150 | Focused logic unit |
| Shared styles | N/A | Import, don't duplicate |

## Extraction Checklist

Before finishing any decomposition:

- [ ] Main component <400 LOC?
- [ ] Each `v-if`/`v-else` branch → own component?
- [ ] Each `<div class="panel">` or section → own component?
- [ ] Repeated button groups → shared component?
- [ ] >3 related refs → composable?
- [ ] >2 related functions → composable?
- [ ] Styles shared with other files → shared CSS?

## Template Extraction Rules

1. **Each tab panel** → separate component
2. **Each form section** → separate component
3. **Repeated patterns** (button grids, input rows) → shared component
4. **Modal/dropdown content** → separate component

## Composable Extraction Rules

1. **State + actions for one feature** → one composable
2. **Split if >150 LOC**: state composable + actions composable
3. **Name pattern**: `use{Feature}.ts` or `use{Feature}{Aspect}.ts`

## Shared Styles

Create shared CSS modules for:
- Buttons: `.btn`, `.btn-primary`, `.btn-danger`, `.btn-small`
- Cards: `.card`, `.panel`, `.result-box`
- Forms: `.input-row`, `.input`, `.select`
- Badges: `.badge`, `.kpi`, `.risk-badge`
- Grids: `.calculator-grid`, `.form-grid`

Import with: `@import '@/styles/shared/buttons.css';`

## Directory Structure

```
components/
  {feature}/
    {FeatureMain}.vue          # Orchestrator (<400 LOC)
    {FeaturePanel}.vue         # Tab/section (<200 LOC)
    {FeatureForm}.vue          # Form section (<200 LOC)
    composables/
      use{Feature}.ts          # Main logic (<150 LOC)
      use{FeatureState}.ts     # State only if needed
      use{FeatureActions}.ts   # Actions only if needed
```

## CI Enforcement

```bash
# Fail build if any .vue exceeds 500 LOC
find src -name "*.vue" -exec wc -l {} \; | awk '$1 > 500 {print "FAIL:", $2; exit 1}'
```
