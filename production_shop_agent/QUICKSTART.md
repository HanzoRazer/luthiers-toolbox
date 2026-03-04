# Quick Start Guide

Get the Site Generator API running in 5 minutes.

## Step 1: Install Dependencies

```bash
cd production_shop_agent
pip install -r requirements.txt
```

## Step 2: Configure API Keys

```bash
# Create .env file from template
cp .env.example .env

# Edit .env and set these two keys:
# 1. SITE_GENERATOR_API_KEY - create your own secure key
# 2. ANTHROPIC_API_KEY - your Claude API key (already set)
```

**Generate a secure API key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 3: Start the Server

```bash
python main.py
```

You should see:
```
============================================================
  PRODUCTION SHOP - SITE GENERATOR API
============================================================
  Jobs Directory: C:\...\site_jobs
  Max Concurrent Jobs: 3
  Rate Limiting: Enabled
  Rate Limit: 10 requests/hour
  ...
============================================================
```

Server is running at: **http://localhost:8000**

## Step 4: Test the API

### Option A: Use the Admin UI (Easiest)

1. Open `admin_ui.html` in your browser
2. Enter your API key
3. Click "Test Connection"
4. Select a template and click "Generate Site"

### Option B: Use cURL

```bash
# Test health endpoint
curl http://localhost:8000/api/site-generator/health

# Generate a site
curl -X POST http://localhost:8000/api/site-generator/generate \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "spec": {
      "site_name": "Test Site",
      "description": "My first generated site",
      "colors": {"primary": "#2563eb"},
      "typography": {"family-sans": "system-ui"},
      "js_features": ["mobile nav"],
      "pages": [{
        "name": "Home",
        "filename": "index.html",
        "description": "Simple home page",
        "sections": ["Hero", "Footer"]
      }]
    }
  }'
```

## Step 5: View API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## What's Next?

### Generate The Production Shop Website

```bash
# Using Python
python -c "
import requests
import json

with open('site_agent/specs/production_shop.json') as f:
    spec = json.load(f)

response = requests.post(
    'http://localhost:8000/api/site-generator/generate',
    headers={'X-API-Key': 'your-api-key'},
    json={'spec': spec}
)

print(response.json())
"
```

### Wire into Your Main App

```python
# your_app.py
from fastapi import FastAPI
from api.site_generator_router import router

app = FastAPI()
app.include_router(router)

# Now you have all /api/site-generator/* endpoints
```

### Add a Frontend

Use the provided `admin_ui.html` as a starting point, or integrate into your existing Production Shop frontend:

```javascript
// In your website
async function generateCustomerSite(spec) {
  const response = await fetch('/api/site-generator/generate', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your-key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ spec })
  });

  const { job_id } = await response.json();

  // Poll for completion
  const interval = setInterval(async () => {
    const status = await fetch(`/api/site-generator/status/${job_id}`)
      .then(r => r.json());

    if (status.status === 'complete') {
      clearInterval(interval);
      window.location.href = status.download_url;
    }
  }, 2000);
}
```

## Troubleshooting

**Import error: No module named 'pydantic_settings'**
```bash
pip install pydantic-settings
```

**401 Unauthorized**
- Check you set `SITE_GENERATOR_API_KEY` in `.env`
- Make sure you're passing the key in `X-API-Key` header

**429 Rate Limit**
- Increase `RATE_LIMIT_PER_HOUR` in `.env`
- Or disable with `RATE_LIMIT_ENABLED=false`

**Claude API errors**
- Verify `ANTHROPIC_API_KEY` is correct
- Check your Claude API quota/billing

## File Structure

```
production_shop_agent/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Your configuration (create from .env.example)
├── .env.example           # Configuration template
├── admin_ui.html          # Web admin interface
├── API_README.md          # Full API documentation
├── QUICKSTART.md          # This file
├── api/
│   ├── __init__.py
│   ├── site_generator_router.py  # Enhanced API router
│   ├── config.py                 # Settings management
│   └── auth.py                   # Authentication & rate limiting
├── site_agent/
│   ├── agent.py           # Core generation logic
│   ├── specs/             # Site specification templates
│   └── output/            # Generated sites
└── site_jobs/             # API job storage (auto-created)
```

## Next Steps

1. Read `API_README.md` for full documentation
2. Customize `.env` settings for your needs
3. Add more spec templates in `site_agent/specs/`
4. Integrate into your Production Shop application
5. Deploy to production (see API_README.md)

## Support

- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/site-generator/health
- Admin UI: Open `admin_ui.html` in browser
