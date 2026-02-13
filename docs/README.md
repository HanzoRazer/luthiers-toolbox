# Documentation Site

This directory contains the MkDocs documentation for Luthier's ToolBox.

---

## Local Preview

To preview the documentation locally:

```bash
# Install dependencies
pip install mkdocs mkdocs-material pymdown-extensions

# Start local server
cd luthiers-toolbox
mkdocs serve

# Open http://127.0.0.1:8000 in your browser
```

---

## Enable GitHub Pages

To deploy the documentation to GitHub Pages:

1. Go to your repository on GitHub
2. Navigate to **Settings > Pages**
3. Under "Build and deployment", select **GitHub Actions** as the source
4. The workflow will run automatically on the next push to `main` that modifies docs

Once deployed, the site will be available at:

```
https://hanzorazer.github.io/luthiers-toolbox/
```

---

## Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/
│   ├── installation.md         # Setup guide
│   ├── quickstart.md           # 5-minute intro
│   └── configuration.md        # Environment config
├── features/                   # Feature documentation
│   ├── overview.md
│   ├── scale-length.md
│   ├── unit-converter.md
│   ├── woodwork-calculator.md
│   ├── fret-calculator.md
│   ├── dxf-import.md
│   ├── toolpaths.md
│   └── rosette-designer.md
├── cam/                        # CAM & CNC documentation
│   ├── overview.md
│   ├── machine-profiles.md
│   ├── post-processors.md
│   ├── gcode-preview.md
│   └── safety-rmos.md
├── api/                        # API reference
│   ├── overview.md
│   ├── authentication.md
│   └── endpoints.md
├── troubleshooting.md          # Common issues
└── contributing.md             # Contribution guide
```

---

## Configuration

The site is configured via `mkdocs.yml` in the repository root.

Key settings:
- **Theme:** Material for MkDocs
- **Color scheme:** Amber/Orange with dark/light toggle
- **Features:** Instant navigation, search, code copy

---

## Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add the page to the `nav` section in `mkdocs.yml`
3. Commit and push - the site will rebuild automatically

---

## Workflow

The GitHub Actions workflow (`.github/workflows/docs.yml`) automatically:

1. Builds the documentation on push to `main`
2. Deploys to GitHub Pages
3. Only triggers on changes to `docs/**`, `mkdocs.yml`, or the workflow file
