# TEST / RUNTIME COMPARISON

Allowed relation: `SAME` | `DIFFERENT` | `PARTIAL` | `UNKNOWN`

`DIFFERENT` is not synonymous with defect.

Filled after Phase 10 from `artifacts/tools/test_runtime_compare.py` plus the
frozen witness bundle.

Format per specimen:

```text
TEST ENTRYPOINT
TEST IMPLEMENTATION
PRODUCTION ENTRYPOINT
PRODUCTION IMPLEMENTATION
RELATION
```
