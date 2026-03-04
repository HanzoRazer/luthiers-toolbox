# Production Shop — Website Generation Agent

Python script → Claude API → complete website on disk.

Built using the **Option 1 approach** scaffolded by Claude Code:
- Deterministic, scriptable, embeddable
- Resumable on interruption
- Full call log for audit/replay
- Drop a new spec JSON → get a new site

---

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```bash
# Generate The Production Shop marketing site
python agent.py --spec specs/production_shop.json --out ./output/production_shop

# Generate a lutherie portfolio site
python agent.py --spec specs/lutherie_portfolio.json --out ./output/hartwell

# Resume an interrupted run (skips existing files)
python agent.py --spec specs/production_shop.json --out ./output/production_shop --resume

# List available spec files
python agent.py --list-specs
```

---

## Output structure

```
output/
  production_shop/
    index.html          ← Home
    features.html       ← Features
    pricing.html        ← Pricing
    about.html          ← About
    contact.html        ← Contact
    styles.css          ← Shared stylesheet (design tokens + base styles)
    main.js             ← Shared JavaScript (nav, scroll, forms)
    .agent_logs/
      spec.json         ← Copy of the spec used
      manifest.json     ← Run summary (files written, timestamps)
      calls.jsonl       ← Every Claude API call logged (tokens, timing)
```

Open `index.html` directly in a browser — no build step.

---

## Adding a new site

Create a JSON spec in `specs/`. The schema:

```json
{
  "site_name": "My Guitar Shop",
  "description": "One sentence describing the site's purpose and tone.",
  "colors": {
    "primary": "#2563eb",
    "surface": "#ffffff",
    "text": "#1e293b"
  },
  "typography": {
    "family-sans": "system-ui, sans-serif"
  },
  "js_features": ["mobile nav toggle", "contact form validation"],
  "pages": [
    {
      "name": "Home",
      "filename": "index.html",
      "description": "What this page does and its tone.",
      "sections": [
        "Hero: headline, subhead, CTA",
        "Features: 3-column cards",
        "Footer"
      ]
    }
  ]
}
```

The more specific your `description` and `sections`, the better the output.

---

## Embedding in The Production Shop

The agent can be called from a Flask/FastAPI endpoint:

```python
from agent import load_spec, generate_site
from pathlib import Path

@app.post("/api/generate-site")
def generate(spec_data: dict):
    out_dir = Path(f"./sites/{spec_data['site_name'].lower().replace(' ', '_')}")
    generate_site(spec_data, out_dir, resume=False)
    return {"status": "ok", "url": f"/sites/{out_dir.name}/index.html"}
```

---

## Model & cost

Uses `claude-sonnet-4-6`. A 5-page site runs roughly:
- ~7 API calls (1 CSS + 1 JS + 5 pages)
- ~15,000–25,000 output tokens total
- Under $0.25 per site at current API pricing
