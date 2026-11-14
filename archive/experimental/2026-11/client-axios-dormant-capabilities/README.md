# Client Axios dormant capabilities (2026-11-14)

Preservation copies for `CLIENT-AXIOS-DORMANT-PRESERVATION-024`.

Source commit: `cfaf07751110d99b3539647e877c2ffd80f4f29c` (merge of PR #482 on main).

These files are byte-identical copies of production sources. Nothing here was reformatted. Nothing here is routed. The production tree is still the source of record.

`DORMANT_PRESERVE` does not mean safe to delete. A cluster may remain in production after this copy. Removing a production file needs a later ruling, and the clusters are not one deletion.

Axios stays installed at `^1.21.0`. This directory does not remove the dependency and does not activate a dormant screen.

## How to read it

- `MANIFEST.json` records original path, SHA-256, Git blob, source commit, cluster, callers, endpoints, and reachability for every copied file.
- `CAPABILITY_INDEX.md` is the cluster narrative, including callers and dependencies that stayed in production and why.
- `ENDPOINT_MATRIX.csv` lists each Axios operation and the contracts that must stay distinct (`/api/compare/lab`, Rosette baseline/diff, Rosette history).
- `source/` repeats the original relative paths.

The four canonical-but-unrouted importers are included with that disposition. Their production files are not retired.

`useRosetteCompareApi.ts` is the baseline/diff client. It is a different contract from `GET /api/compare/history` and from the art-rosette job compare history.

## Verify

From the repository root:

```bash
python3 scripts/investigations/client_axios_preservation.py \
  --repo-root . \
  --inventory docs/investigations/client-axios-reachability-020_2026-11-10/AXIOS_IMPORT_INVENTORY.csv \
  --archive-root archive/experimental/2026-11/client-axios-dormant-capabilities \
  --verify
```

`--dry-run` writes nothing. The tool does not delete production files, and it refuses an archive destination inside `packages/client/src`.
