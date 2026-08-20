# Client container smoke has no readiness wait — MAINT-DEFER-008

**Registered:** 2026-08-19
**SPRINTS ID:** MAINT-DEFER-008
**Workflow:** `.github/workflows/containers.yml` (job `build-and-test`, check name **Containers (Build + Smoke)**)
**Status:** QUEUED — evidence recorded, no fix applied

## 1. Verdict

`containers.yml` waits for the **API** container to become ready and then curls the
**client** container immediately, with no wait and no retry. Client readiness is
never asserted — it is assumed, on the incidental basis that the API poll usually
takes long enough for nginx to come up too.

When it does not, the job fails with a connection-level error that looks like a
product regression and is not one.

## 2. The asymmetry, in the file

The startup step polls the API for up to 60s (30 × 2s):

```yaml
# containers.yml:54-58
docker compose up -d
# wait for health
for i in $(seq 1 30); do
  docker compose ps
  curl -fsS http://127.0.0.1:${SERVER_PORT}/health && break || sleep 2
done
```

`${CLIENT_PORT}` appears nowhere in that loop. Its first use in the whole job is
the smoke step itself:

```yaml
# containers.yml:100-106
- name: Smoke - Client container
  run: |
    echo "Testing client container..."
    curl -fsS http://127.0.0.1:${CLIENT_PORT}/ | grep "Production Shop"

    echo "Testing API proxy through client..."
    curl -fsS http://127.0.0.1:${CLIENT_PORT}/health | jq .
```

Single-shot `curl`, no `--retry`, no `--retry-connrefused`, no preceding poll.

## 3. Observed failure

PR #297, run `32183393779`, job `95861446559`:

```
Testing client container...
curl: (56) Recv failure: Connection reset by peer
##[error]Process completed with exit code 1.
```

`curl (56)` on the *first* request is the signature of a socket that is listening
but not yet serving — i.e. a readiness race, not an application fault.

**Established as a flake, not a regression, before re-run:** the PR that failed
changed only `SPRINTS.md` and a CBSP21 manifest, which cannot affect a container
image; the same workflow was green on main's preceding six commits and on all four
runs of a sibling branch; and the job passed on re-run with no code change.

## 4. Why this is CI-RED-020's defect shape

CI-RED-020 closed the same class on the **API** side: a blind reachable-check was
replaced by a readiness gate that asserts the service is actually serving rather
than merely accepting connections. That work produced a reusable helper,
`scripts/ci/wait_for_api_ready.py`, now used by `api_health_check.yml`,
`api_tests.yml`, and `api_health_and_smoke.yml`.

`containers.yml` never adopted it. It still hand-rolls the older
curl-in-a-for-loop pattern — and applies even that only to the API.

The consequence is the one CI-RED-020 exists to prevent: an ambiguous red that
costs a re-run to classify, and that trains readers to dismiss reds in this job
as "probably flaky." That habit is the actual risk, because it is indistinguishable
from how a real client-container regression would first present.

## 5. Restore trigger

Client readiness asserted before the first client curl. Either is acceptable:

- extend the existing loop to poll `http://127.0.0.1:${CLIENT_PORT}/` alongside the
  API health check, so the step cannot proceed until both are serving; or
- give the client curls `--retry`/`--retry-connrefused` with a bounded budget.

Preferred, if the helper's contract fits an nginx root rather than a JSON health
endpoint: reuse `scripts/ci/wait_for_api_ready.py` so both containers gate through
one witness instead of two divergent patterns.

Done-condition: a deliberate cold-start run in which the client container is slower
than the API still passes the smoke step.

## 6. Scope limits

No fix is applied here. Nothing in `containers.yml` is edited by the patch that
registers this record. The failure rate is not characterised — one occurrence is
recorded, and no history sweep was run to establish frequency, so this is not
evidence about how often the race is lost.

`Show logs on failure` (`containers.yml`, `if: failure()`) already dumps container
logs, so a future occurrence should carry more diagnostic detail than the run cited
above.
