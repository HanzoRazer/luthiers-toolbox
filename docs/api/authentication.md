# Authentication

API authentication for secure access.

---

## Current Status

!!! note "Beta Period"
    During beta, authentication is **optional**. All endpoints are accessible
    without credentials when running locally.

---

## Authentication Methods

### API Key (Planned)

For production deployments, API key authentication will be available:

```bash
curl -H "Authorization: Bearer your-api-key" \
  http://api.toolbox.example.com/api/calculators/string-tension
```

### Session Token (Web UI)

The web UI uses session-based authentication with cookies. This is handled automatically by the frontend.

---

## Obtaining Credentials

### Local Development

No credentials required. The API accepts all requests.

### Production

Contact the system administrator for API credentials.

---

## Security Headers

### Required Headers

For authenticated requests:

```
Authorization: Bearer <token>
Content-Type: application/json
```

### CORS

Cross-origin requests require proper CORS configuration. The API allows:

- `http://localhost:5173` (Vue dev server)
- `http://localhost:3000`
- Configured production origins

---

## Environment Variables

Configure authentication via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_AUTH_ENABLED` | Enable authentication | `false` |
| `API_AUTH_SECRET` | Secret for token signing | (required if enabled) |
| `API_AUTH_EXPIRY` | Token expiry in seconds | `3600` |

---

## Rate Limiting

When authentication is enabled, rate limits apply:

| Limit | Value |
|-------|-------|
| Requests per minute | 100 |
| Requests per hour | 1000 |
| Requests per day | 10000 |

Unauthenticated requests (local development) have no rate limits.

---

## Error Responses

### 401 Unauthorized

Missing or invalid authentication:

```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

### 403 Forbidden

Valid authentication but insufficient permissions:

```json
{
  "detail": "Permission denied",
  "status_code": 403
}
```

---

## Token Management

### Refresh Tokens (Planned)

Long-lived refresh tokens will allow obtaining new access tokens:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer <refresh-token>"
```

### Token Revocation (Planned)

Revoke compromised tokens:

```bash
curl -X POST http://localhost:8000/api/auth/revoke \
  -H "Authorization: Bearer <token>"
```

---

## Best Practices

### Secure Storage

- Never commit API keys to version control
- Use environment variables or secret management
- Rotate keys periodically

### Request Security

- Always use HTTPS in production
- Validate SSL certificates
- Don't log sensitive headers

### Minimal Permissions

- Request only necessary permissions
- Use separate keys for different applications
- Audit key usage regularly

---

## Integration Examples

### Python with Environment Variable

```python
import os
import requests

API_KEY = os.environ.get("TOOLBOX_API_KEY")
API_BASE = os.environ.get("TOOLBOX_API_URL", "http://localhost:8000")

headers = {}
if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

response = requests.get(
    f"{API_BASE}/api/calculators/string-tension",
    headers=headers
)
```

### GitHub Actions

```yaml
jobs:
  api-call:
    runs-on: ubuntu-latest
    steps:
      - name: Call ToolBox API
        env:
          TOOLBOX_API_KEY: ${{ secrets.TOOLBOX_API_KEY }}
        run: |
          curl -H "Authorization: Bearer $TOOLBOX_API_KEY" \
            https://api.toolbox.example.com/health
```

---

## Related

- [API Overview](overview.md) - General API information
- [Endpoints](endpoints.md) - Full endpoint reference
