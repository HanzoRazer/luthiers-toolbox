# SG_SPEC_TOKEN (CI and Docker)

Private dependency: `sg-spec @ git+https://github.com/HanzoRazer/sg-spec.git` in `services/api/requirements.txt`.

## Required secret shape

| Property | Requirement |
|----------|-------------|
| Type | **Classic PAT** (`ghp_…`) or **fine-grained PAT** with read access to `HanzoRazer/sg-spec` |
| Scope | `repo` (classic) or repository contents read (fine-grained) |
| Storage | GitHub Actions repo secret `SG_SPEC_TOKEN`; Docker build-arg of the same name |
| Max lifetime | Prefer fine-grained with explicit expiry (≤ 1 year); record expiry below |

## Do not use

- **`gh auth token`** (OAuth user-to-server, `gho_…`) — expires with session; emergency probe only, not the long-lived repo secret.
- Empty or placeholder values — ambiguous clone errors (`Invalid username or token`, password prompts).

## Rotation log (update every time the secret changes)

When you create or rotate the PAT, GitHub shows the expiration date. **Copy it here immediately** and set a calendar reminder **30 days before** expiry so the gate never goes dead without a named recovery path.

| Set date (UTC) | Expires (UTC) | Type | Calendar reminder | Notes |
|----------------|---------------|------|-------------------|-------|
| _YYYY-MM-DD_ | _YYYY-MM-DD_ | fine-grained / classic | _expires − 30d_ | e.g. `luthiers-toolbox-ci-sg-spec`, repo `HanzoRazer/sg-spec` read |

**Calendar (cheap insurance):** Create a recurring or one-shot event titled `SG_SPEC_TOKEN expires — rotate luthiers-toolbox` on the **Expires** date minus 30 days. Link this file in the event description.

## Rotate (when preflight or Install API deps fails auth)

1. GitHub → Settings → Developer settings → [Personal access tokens](https://github.com/settings/tokens).
2. Create **fine-grained** PAT (recommended):
   - Resource owner: your account or org as appropriate
   - Repository access: **Only select** → `HanzoRazer/sg-spec`
   - Permissions: **Contents** → Read-only, **Metadata** → Read-only
   - Expiration: choose a date (max 1 year); **write that date in the table above**
3. Or classic PAT with `repo` scope and expiration set.
4. Update the repo secret (no workflow change):

   ```bash
   gh secret set SG_SPEC_TOKEN --repo HanzoRazer/luthiers-toolbox
   ```

5. Re-run **API Verify** or push an empty commit on `main`/PR branch.
6. Confirm in CI: **Preflight sg-spec token** and **Install API deps** both green.

## CI preflight

`api_verify.yml` runs `git ls-remote` on `HanzoRazer/sg-spec` immediately after git credential setup. A stale or wrong token fails in one step with an explicit message — not a silent dead gate mid-`pip install`.

## Related

- `docs/getting-started/configuration.md` — env table
- `docker/api/Dockerfile` — same credential-store pattern for image builds
- SPRINTS **CI-RED-001** — closed when auth + preflight + this doc are on `main`
- SPRINTS **CI-RED-005** — container build must not swallow sg-spec install failures
