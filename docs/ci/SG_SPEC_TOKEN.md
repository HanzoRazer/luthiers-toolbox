# SG_SPEC_TOKEN (CI and Docker)

Private dependency: `sg-spec @ git+https://github.com/HanzoRazer/sg-spec.git` in `services/api/requirements.txt`.

## Required secret shape

| Property | Requirement |
|----------|-------------|
| Type | **Classic PAT** (`ghp_…`) or **fine-grained PAT** with read access to `HanzoRazer/sg-spec` |
| Scope | `repo` (classic) or repository contents read (fine-grained) |
| Storage | GitHub Actions repo secret `SG_SPEC_TOKEN`; Docker build-arg of the same name |

## Do not use

- **`gh auth token`** (OAuth user-to-server, `gho_…`) — expires with session; acceptable only as an emergency probe, not as the long-lived repo secret.
- Empty or placeholder values — produces ambiguous clone errors (`Invalid username or token`, password prompts).

## Rotate (when Install API deps or container sg-spec step fails auth)

1. GitHub → Settings → Developer settings → [Personal access tokens](https://github.com/settings/tokens).
2. Generate classic PAT with `repo`, or fine-grained PAT limited to `HanzoRazer/sg-spec` (read).
3. Update the repo secret (no workflow change needed):

   ```bash
   gh secret set SG_SPEC_TOKEN --repo HanzoRazer/luthiers-toolbox
   ```

4. Re-run **API Verify** or push an empty commit; confirm **Preflight sg-spec token** and **Install API deps** green in CI.

## CI preflight

`api_verify.yml` runs `git ls-remote` on `HanzoRazer/sg-spec` immediately after git credential setup so a dead token fails in one step with an explicit message, not mid-`pip install`.

## Related

- `docs/getting-started/configuration.md` — env table
- `docker/api/Dockerfile` — same credential-store pattern for image builds
- SPRINTS **CI-RED-005** — container build must not swallow sg-spec install failures
