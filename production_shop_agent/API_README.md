# Production Shop - Site Generator API

Enhanced, production-ready REST API for generating websites using Claude AI.

## Features

✅ **Security**
- API key authentication (header or Bearer token)
- Input validation and sanitization
- Rate limiting (configurable per hour)

✅ **Job Management**
- Background processing with progress tracking
- Job cancellation support
- Auto-cleanup of old jobs (configurable retention)

✅ **Webhooks**
- Optional webhook notifications on completion
- HMAC-SHA256 signed payloads

✅ **Developer Experience**
- Preview generated files before downloading
- Comprehensive error messages
- OpenAPI/Swagger docs
- Health check endpoint

---

## Quick Start

### 1. Install Dependencies

```bash
cd production_shop_agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your keys
# - Set SITE_GENERATOR_API_KEY (your API key)
# - Set ANTHROPIC_API_KEY (Claude API key)
```

### 3. Run the Server

```bash
# Development mode
python main.py

# Or with uvicorn
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Test the API

```bash
# Check health
curl http://localhost:8000/api/site-generator/health

# View API docs
open http://localhost:8000/api/docs
```

---

## API Endpoints

### Authentication

All protected endpoints require API key via:
- **Header**: `X-API-Key: your-api-key`
- **Bearer token**: `Authorization: Bearer your-api-key`

### POST `/api/site-generator/generate`

Generate a new website from specification.

**Request:**
```json
{
  "spec": {
    "site_name": "My Guitar Shop",
    "description": "A professional lutherie business site",
    "colors": {
      "primary": "#2563eb",
      "surface": "#ffffff",
      "text": "#1e293b"
    },
    "typography": {
      "family-sans": "system-ui, sans-serif"
    },
    "js_features": ["mobile nav", "contact form validation"],
    "pages": [
      {
        "name": "Home",
        "filename": "index.html",
        "description": "Landing page with hero and features",
        "sections": [
          "Hero with CTA",
          "Feature cards",
          "Footer"
        ]
      }
    ]
  },
  "job_label": "My Custom Site",
  "webhook_url": "https://your-domain.com/webhook"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "a3f9c2d1",
  "label": "My Custom Site",
  "status": "pending",
  "progress": 0,
  "files_written": 0,
  "total_files": 3,
  "started_at": "2024-01-15T10:30:00",
  "download_url": null,
  "preview_url": null
}
```

---

### GET `/api/site-generator/status/{job_id}`

Check generation progress (no auth required).

**Response:**
```json
{
  "job_id": "a3f9c2d1",
  "status": "running",
  "progress": 60,
  "files_written": 2,
  "total_files": 3
}
```

Status values: `pending`, `running`, `complete`, `failed`, `cancelled`

---

### GET `/api/site-generator/download/{job_id}`

Download completed site as ZIP (requires auth).

**Response:** ZIP file download

---

### GET `/api/site-generator/preview/{job_id}/{filename}`

Preview a generated file in browser (no auth required).

Examples:
- `GET /api/site-generator/preview/a3f9c2d1/index.html`
- `GET /api/site-generator/preview/a3f9c2d1/styles.css`
- `GET /api/site-generator/preview/a3f9c2d1` (defaults to index.html)

---

### GET `/api/site-generator/jobs`

List all jobs (requires auth).

**Query params:**
- `status` - Filter by status
- `limit` - Max results (default: 50, max: 100)

**Response:**
```json
{
  "jobs": [...],
  "total": 25,
  "active": 2,
  "completed": 20,
  "failed": 3
}
```

---

### POST `/api/site-generator/jobs/{job_id}/cancel`

Cancel a running job (requires auth).

---

### DELETE `/api/site-generator/jobs/{job_id}`

Delete a job and its files (requires auth).

---

### GET `/api/site-generator/health`

Health check (no auth).

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "jobs": {
    "total": 10,
    "running": 2,
    "complete": 8
  },
  "config": {
    "max_concurrent_jobs": 3,
    "rate_limit_per_hour": 10
  }
}
```

---

## Usage Examples

### cURL

```bash
# Generate site
curl -X POST http://localhost:8000/api/site-generator/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @specs/production_shop.json

# Check status
curl http://localhost:8000/api/site-generator/status/a3f9c2d1

# Download
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/site-generator/download/a3f9c2d1 \
  -o site.zip

# List jobs
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/site-generator/jobs?status=complete&limit=10
```

### Python

```python
import requests
import time

API_URL = "http://localhost:8000/api/site-generator"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

# Load spec
with open("specs/production_shop.json") as f:
    spec = json.load(f)

# Start generation
response = requests.post(
    f"{API_URL}/generate",
    headers=headers,
    json={"spec": spec, "job_label": "My Site"}
)
job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# Poll for completion
while True:
    status = requests.get(f"{API_URL}/status/{job_id}").json()
    print(f"Progress: {status['progress']}% - {status['status']}")

    if status["status"] == "complete":
        # Download
        download_url = f"{API_URL}/download/{job_id}"
        response = requests.get(download_url, headers=headers)
        with open("site.zip", "wb") as f:
            f.write(response.content)
        print("Downloaded site.zip")
        break

    elif status["status"] == "failed":
        print(f"Failed: {status['error']}")
        break

    time.sleep(2)
```

### JavaScript/Fetch

```javascript
const API_URL = 'http://localhost:8000/api/site-generator';
const API_KEY = 'your-api-key';

async function generateSite(spec) {
  // Start generation
  const response = await fetch(`${API_URL}/generate`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ spec })
  });

  const { job_id } = await response.json();
  console.log('Job started:', job_id);

  // Poll for completion
  while (true) {
    const status = await fetch(`${API_URL}/status/${job_id}`)
      .then(r => r.json());

    console.log(`Progress: ${status.progress}%`);

    if (status.status === 'complete') {
      // Trigger download
      window.location.href = status.download_url;
      break;
    } else if (status.status === 'failed') {
      console.error('Generation failed:', status.error);
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```

---

## Webhooks

When a job completes, the API can POST a notification to your webhook URL.

**Webhook Payload:**
```json
{
  "job_id": "a3f9c2d1",
  "status": "complete",
  "label": "My Site",
  "completed_at": "2024-01-15T10:35:00",
  "download_url": "/api/site-generator/download/a3f9c2d1",
  "error": null
}
```

**HMAC Signature:**
If `WEBHOOK_SECRET` is set, payloads are signed:
- Header: `X-Webhook-Signature: sha256=<hex-digest>`
- Algorithm: HMAC-SHA256

**Verify signature:**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={expected}" == signature
```

---

## Configuration

Edit `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SITE_GENERATOR_API_KEY` | API key for authentication | `dev-key-change-in-production` |
| `ANTHROPIC_API_KEY` | Claude API key | (required) |
| `MAX_CONCURRENT_JOBS` | Max simultaneous generations | `3` |
| `JOB_RETENTION_HOURS` | Auto-delete jobs after hours | `48` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_PER_HOUR` | Requests per hour per key | `10` |
| `WEBHOOK_ENABLED` | Enable webhook notifications | `false` |
| `WEBHOOK_SECRET` | Secret for signing webhooks | (optional) |

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `202` - Accepted (job started)
- `400` - Bad request (invalid spec)
- `401` - Unauthorized (missing API key)
- `403` - Forbidden (invalid API key)
- `404` - Not found (job doesn't exist)
- `429` - Too many requests (rate limit)
- `500` - Internal server error
- `503` - Service unavailable (too many concurrent jobs)

### Error Response Format

```json
{
  "detail": "Rate limit exceeded. Resets at 14:30:00"
}
```

---

## Production Deployment

### Using Gunicorn

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

In production:
1. Use strong random API keys
2. Set `ANTHROPIC_API_KEY` from secure storage
3. Configure CORS `allowed_origins`
4. Enable webhooks if needed
5. Set appropriate rate limits
6. Use HTTPS (reverse proxy)

---

## Security Considerations

1. **API Keys**: Generate strong random keys, rotate regularly
2. **Rate Limiting**: Adjust per your needs, monitor for abuse
3. **CORS**: Restrict to your frontend domains only
4. **File Validation**: Spec validation prevents directory traversal
5. **Webhooks**: Verify HMAC signatures before processing
6. **HTTPS**: Always use TLS in production
7. **Secrets**: Never commit `.env` to version control

---

## Monitoring

Check these endpoints:
- `/api/site-generator/health` - Service status
- `/api/site-generator/jobs` - Job statistics

Monitor:
- Job success/failure rates
- Average generation time
- API key usage patterns
- Rate limit hits
- Disk space (jobs directory)

---

## Troubleshooting

**Jobs stuck in "pending":**
- Check if Claude API key is valid
- Verify network connectivity
- Check server logs

**Rate limit errors:**
- Increase `RATE_LIMIT_PER_HOUR`
- Implement API key-based quotas

**Out of disk space:**
- Reduce `JOB_RETENTION_HOURS`
- Manually clean `SITE_JOBS_DIR`

**Jobs failing:**
- Check Claude API quota/billing
- Validate spec JSON format
- Review `.agent_logs/calls.jsonl`

---

## Support

- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health: http://localhost:8000/api/site-generator/health
