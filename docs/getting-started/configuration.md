# Configuration

Customize The Production Shop for your workflow.

---

## Environment Variables

Create a `.env` file in `services/api/`:

```env
# === Core Settings ===
APP_ENV=development          # development | production
DEBUG=1                      # Enable debug logging

# === Data Storage ===
RMOS_RUNS_DIR=./data/runs    # Manufacturing run storage
DATA_DIR=./data              # General data directory

# === AI Features (Optional) ===
OPENAI_API_KEY=sk-...        # For AI-assisted features
ANTHROPIC_API_KEY=sk-...     # Alternative AI provider

# === Safety Settings ===
RMOS_STRICT_STARTUP=1        # Fail fast if safety modules missing
RMOS_ALLOW_RED_OVERRIDE=0    # Block dangerous operations

# === Analytics (Optional) ===
ANALYTICS_VERBOSE=0          # Log route usage to stdout
```

---

## Machine Profiles

Configure your CNC machine in the UI:

1. Navigate to **Settings > Machine Profiles**
2. Click **Add Profile**
3. Enter machine parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| Name | Profile identifier | "Shapeoko 4 XXL" |
| Work Area X | Max X travel (mm) | 838 |
| Work Area Y | Max Y travel (mm) | 838 |
| Work Area Z | Max Z travel (mm) | 95 |
| Max Feed XY | Max XY feed (mm/min) | 10000 |
| Max Feed Z | Max Z feed (mm/min) | 5000 |
| Max RPM | Spindle max speed | 30000 |

---

## Post Processors

Select the right post processor for your controller:

| Controller | Post Processor |
|------------|----------------|
| Grbl | `grbl` |
| Mach3/4 | `mach` |
| LinuxCNC | `linuxcnc` |
| Centroid | `centroid` |
| Generic | `generic` |

Configure in **Settings > Post Processors**.

---

## Tool Library

Pre-define your cutting tools:

1. Navigate to **Settings > Tool Library**
2. Add tools with parameters:

```yaml
- name: "1/4 inch Endmill"
  diameter: 6.35  # mm
  flutes: 2
  type: endmill
  material: carbide

- name: "1/8 inch Ball Nose"
  diameter: 3.175  # mm
  flutes: 2
  type: ballnose
  material: carbide
```

---

## UI Preferences

Stored in browser localStorage:

| Setting | Options |
|---------|---------|
| Theme | Dark / Light |
| Units | Metric / Imperial |
| Grid Size | 1mm / 5mm / 10mm |
| Show Tooltips | On / Off |

Access via **Settings > Preferences**.

---

## API Configuration

For headless/scripted usage:

```python
import requests

API_BASE = "http://localhost:8000"

# Health check
response = requests.get(f"{API_BASE}/health")
print(response.json())

# Generate toolpath
response = requests.post(
    f"{API_BASE}/api/cam/pocket",
    json={
        "dxf_path": "body.dxf",
        "tool_diameter": 6.0,
        "stepover_pct": 45,
        "stepdown": 2.0
    }
)
```

---

## GitHub Secrets (CI/CD)

Required secrets for GitHub Actions workflows:

| Secret | Required | Purpose |
|--------|----------|---------|
| `SG_SPEC_TOKEN` | Yes | PAT with read access to private `sg-spec` repo |
| `RAILWAY_TOKEN` | For deploy | Railway API token for deployment |
| `SLACK_WEBHOOK_URL` | Optional | Slack notifications for CI failures |

### Email Alerting (Optional)

For email notifications on CI failures:

| Secret | Purpose |
|--------|---------|
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USERNAME` | SMTP auth username |
| `SMTP_PASSWORD` | SMTP auth password |
| `MAIL_TO` | Alert recipient email |
| `MAIL_FROM` | Sender email address |

### Creating SG_SPEC_TOKEN

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Create token with `repo` scope (read access to private repos)
3. Add to repository: Settings → Secrets → Actions → New repository secret

---

## Supabase (Optional)

For authentication features:

```env
# === Supabase Auth ===
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Server-side only
```

See [Supabase Auth Setup](../SUPABASE_AUTH_SETUP.md) for details.

---

## Next Steps

- [Machine Profiles](../cam/machine-profiles.md) - Detailed machine setup
- [Post Processors](../cam/post-processors.md) - G-code customization
