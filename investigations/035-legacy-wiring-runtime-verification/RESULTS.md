# RESULTS

Five-specimen sample after runtime freeze (SHA `cab91edacaedc66a0492c35275ce2c255935bf8e`).

```text
D0 = 0
D1 = 0
D2 = 3   (S2 handler ownership, S3 N17 vs governed NC, S4 legacy vs governed DXF)
D3 = 0
D4 = 0
D5 = 1   (S5 fret slots preview)
D6 = 1   (S1 SimLab FE URL)
D7 = 0
```

```text
CONFIRMED FALSE-INTEGRATION COUNT   3  (S1, S3, S4)
  S2 is D2 at HTTP ownership but the same facade compute ran — counted in D2,
  not in the “obsolete calculator” subclass.
CORRECTLY-WIRED COUNT               1  (S5)
UNKNOWN COUNT                       0  at handler identity
```

```text
SEVERE STOP TRIGGERED? = YES  (S3 polygon offset NC)
ROUTE-TRUTH DEFECT TOUCHED? = NO
PRODUCTION MODIFIED? = NO
```

## Current census (not mixed with PR #17)

```text
CURRENT  (Investigation 035 Lab workaround)
  live routes                 1157
  dump_and_assert_routes as-is  10
  collisions                    15
  name-hint modules             23
  FE API literals              276
  FE literals absent from live 137
  test files                   455 (185 TestClient)

HISTORICAL (PR #17)
  historical count = unavailable in this environment
  historical SHA   = cab91edacaedc66a0492c35275ce2c255935bf8e
  comparison not normalized
```

`dump_and_assert_routes.collect_routes()` returned 10 rows because FastAPI
0.137 `_IncludedRouter` has no `.path`. Lab workaround walked included
routers (1157). Production script was not modified.

## Recommendation

```text
TARGET_SPECIFIC_FAILURE_CLASS
```

The sample is not “everything is a wrapper.” S5 was high-risk on paper and
was D5. The repeating class is **wire-URL / first-match ownership**: FE or
docs name an implementation whose live first-match (or live path) is
different.

Do **not** `EXPAND_RUNTIME_AUDIT` to all 15 collisions or 137 unmatched FE
literals. Those sets are noisy (health duplicates, prefix typos, optional
labs).

Do **not** `STATIC_CENSUS_TOO_NOISY` as the sole conclusion: three of five
selected high-risk specimens diverged at runtime, including one manufacturing
G-code path.

`INSUFFICIENT_EVIDENCE` does not apply: IW-03 control fired; S1–S5 handler
identity was measured.

Owner adjudication of S3 is the next production decision. This increment
proposes no patch.
