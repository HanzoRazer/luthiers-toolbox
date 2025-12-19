# Logging Convention

## Rule

Every Python module that logs should define a module-level logger:

```python
import logging
logger = logging.getLogger(__name__)
```

## Usage

- Prefer `logger.info()/warning()/error()/exception()` over `print()`.
- Never create ad-hoc `logging.getLogger("hardcoded")` names.
- Request correlation is injected globally via `RequestIdMiddleware` + `RequestIdFilter`, so logs will automatically include `request_id` when configured.

## Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed diagnostic info (not shown in production) |
| `INFO` | Normal operational events (request processed, run created) |
| `WARNING` | Unexpected but recoverable conditions |
| `ERROR` | Errors that prevented an operation from completing |
| `EXCEPTION` | Use inside except blocks - includes stack trace |

## Examples

```python
# Standard logging
logger.info("created run", extra={"run_id": run.run_id})
logger.warning("unknown engine_id; falling back", extra={"engine_id": engine_id})
logger.exception("toolpath generation failed")

# Request correlation is automatic via ContextVar
# Logs will include [req_abc123def456] prefix
```

## Log Format

The global log format is:

```
%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s
```

Example output:
```
2025-12-19 07:30:15,123 INFO [req_abc123def456] app.rmos.feasibility_router: evaluated feasibility
2025-12-19 07:30:15,456 WARNING [-] app.rmos.runs_v2.store: run not found
```

## Request Correlation

The `RequestIdMiddleware` (in `main.py`) automatically:

1. Reads `X-Request-Id` header from client (or generates `req_{uuid12}`)
2. Attaches to `request.state.request_id`
3. Sets a `ContextVar` for deep logging
4. Echoes back in response headers

This means:
- Routes can access `request.state.request_id`
- Deep helper functions can use `get_request_id()` from `app.util.request_context`
- All logs automatically include the request ID

## Implementation Details

Files:
- `app/util/request_context.py` - ContextVar get/set
- `app/util/logging_request_id.py` - RequestIdFilter for logging
- `app/util/request_utils.py` - `require_request_id()` helper
- `app/main.py` - RequestIdMiddleware + logging configuration

## Testing

The `client` fixture in `tests/conftest.py` auto-injects `X-Request-Id` headers:

```python
def test_something(client):
    r = client.get("/health")
    # Request ID was auto-injected (test_abc123...)
    assert r.headers.get("x-request-id").startswith("test_")
```
