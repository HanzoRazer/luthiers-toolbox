"""
Production Shop — Website Generation Agent
==========================================
Option 1 Pipeline: Python script -> Claude API -> files on disk

Usage:
    python agent.py --spec specs/lutherie_shop.json --out ./output
    python agent.py --spec specs/lutherie_shop.json --out ./output --resume
    python agent.py --list-specs

Architecture:
    SiteSpec (JSON) -> Agent -> [PageGenerator × N] -> FileWriter -> Site on disk

The agent calls the Claude API once per page/asset, writes files
sequentially, supports resume (skips already-written files), and
logs every call so you can inspect or replay them.
"""

import anthropic
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000
RETRY_LIMIT = 3
RETRY_DELAY = 2  # seconds

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert web developer specializing in clean, 
production-ready HTML/CSS/JS sites. 

Rules you always follow:
- Output ONLY the requested file content — no markdown fences, no explanation
- Every HTML file is a complete standalone document (<!DOCTYPE html> through </html>)
- CSS uses custom properties (variables) for all colors, spacing, and typography
- JavaScript is vanilla — no frameworks, no CDN dependencies unless explicitly requested
- All internal links use relative paths
- Every page includes the shared nav and footer
- Code is commented where non-obvious
- Output is clean enough to open directly in a browser with no build step
"""

PAGE_PROMPT_TEMPLATE = """Generate a complete HTML page for a website with these specifications:

SITE NAME: {site_name}
SITE DESCRIPTION: {site_description}
COLOR SCHEME: {colors}
TYPOGRAPHY: {typography}
NAV LINKS: {nav_links}

PAGE: {page_name}
PAGE DESCRIPTION: {page_description}
PAGE SECTIONS: {sections}

SHARED DESIGN TOKENS (use these CSS variables throughout):
{design_tokens}

This page filename will be: {filename}
Other pages in this site: {other_pages}

Generate the complete HTML file now. Output only the HTML, nothing else.
"""

CSS_PROMPT_TEMPLATE = """Generate a shared CSS stylesheet for a website with these specifications:

SITE NAME: {site_name}
SITE DESCRIPTION: {site_description}
COLOR SCHEME: {colors}
TYPOGRAPHY: {typography}

Define all CSS custom properties (design tokens) in :root, then write
base styles, typography, layout utilities, nav, footer, buttons, forms,
and card components. This stylesheet will be imported by every page.

Output only the CSS, nothing else.
"""

JS_PROMPT_TEMPLATE = """Generate a shared JavaScript file for a website.

SITE NAME: {site_name}
FEATURES NEEDED: {js_features}

Write vanilla JS that handles: mobile nav toggle, smooth scroll,
form validation if needed, and any site-specific features listed above.

Output only the JavaScript, nothing else.
"""


# ---------------------------------------------------------------------------
# Spec loader
# ---------------------------------------------------------------------------

def load_spec(spec_path: str) -> dict:
    path = Path(spec_path)
    if not path.exists():
        print(f"[ERROR] Spec file not found: {spec_path}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def build_design_tokens(spec: dict) -> str:
    colors = spec.get("colors", {})
    typography = spec.get("typography", {})
    tokens = [":root {"]
    for name, value in colors.items():
        tokens.append(f"  --color-{name}: {value};")
    for name, value in typography.items():
        tokens.append(f"  --font-{name}: {value};")
    tokens.append("}")
    return "\n".join(tokens)


# ---------------------------------------------------------------------------
# Claude API caller
# ---------------------------------------------------------------------------

def call_claude(prompt: str, label: str, log_dir: Path) -> str:
    """Call Claude API with retry logic. Logs every call to log_dir."""
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            print(f"  -> Calling Claude for: {label} (attempt {attempt})")
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text

            # Log the call
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "label": label,
                "model": MODEL,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "prompt_preview": prompt[:300] + "..." if len(prompt) > 300 else prompt,
            }
            log_path = log_dir / "calls.jsonl"
            with open(log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            print(f"     OK {response.usage.output_tokens} tokens -> {label}")
            return content

        except Exception as e:
            print(f"  [WARN] Attempt {attempt} failed: {e}")
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY * attempt)
            else:
                print(f"  [ERROR] All {RETRY_LIMIT} attempts failed for: {label}")
                raise


# ---------------------------------------------------------------------------
# File writer
# ---------------------------------------------------------------------------

def write_file(out_dir: Path, filename: str, content: str, resume: bool) -> bool:
    """Write a file. If resume=True, skip if file already exists. Returns True if written."""
    filepath = out_dir / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if resume and filepath.exists():
        print(f"  [SKIP] Already exists: {filename}")
        return False

    # Strip accidental markdown fences if Claude adds them
    content = strip_fences(content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [WRITE] {filename} ({len(content):,} chars)")
    return True


def strip_fences(content: str) -> str:
    """Remove ```html, ```css, ```js fences if Claude accidentally includes them."""
    content = re.sub(r"^```[a-z]*\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
    return content.strip()


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------

def generate_site(spec: dict, out_dir: Path, resume: bool):
    site_name = spec["site_name"]
    print(f"\n{'='*60}")
    print(f"  PRODUCTION SHOP SITE AGENT")
    print(f"  Site: {site_name}")
    print(f"  Output: {out_dir}")
    print(f"  Resume: {resume}")
    print(f"{'='*60}\n")

    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = out_dir / ".agent_logs"
    log_dir.mkdir(exist_ok=True)

    # Write spec copy for reference
    with open(log_dir / "spec.json", "w") as f:
        json.dump(spec, f, indent=2)

    design_tokens = build_design_tokens(spec)
    nav_links = ", ".join(
        f"{p['name']} ({p['filename']})" for p in spec["pages"]
    )
    other_pages = ", ".join(p["filename"] for p in spec["pages"])
    colors_str = json.dumps(spec.get("colors", {}), indent=2)
    typography_str = json.dumps(spec.get("typography", {}), indent=2)

    total_files = 2 + len(spec["pages"])  # CSS + JS + pages
    written = 0

    # 1. Shared CSS
    print(f"[1/{total_files}] Generating shared stylesheet...")
    css_prompt = CSS_PROMPT_TEMPLATE.format(
        site_name=site_name,
        site_description=spec.get("description", ""),
        colors=colors_str,
        typography=typography_str,
    )
    css_content = call_claude(css_prompt, "styles.css", log_dir)
    if write_file(out_dir, "styles.css", css_content, resume):
        written += 1

    # 2. Shared JS
    print(f"\n[2/{total_files}] Generating shared JavaScript...")
    js_features = ", ".join(spec.get("js_features", ["mobile nav toggle", "smooth scroll"]))
    js_prompt = JS_PROMPT_TEMPLATE.format(
        site_name=site_name,
        js_features=js_features,
    )
    js_content = call_claude(js_prompt, "main.js", log_dir)
    if write_file(out_dir, "main.js", js_content, resume):
        written += 1

    # 3. Pages
    for i, page in enumerate(spec["pages"], start=3):
        print(f"\n[{i}/{total_files}] Generating: {page['name']} -> {page['filename']}")
        page_prompt = PAGE_PROMPT_TEMPLATE.format(
            site_name=site_name,
            site_description=spec.get("description", ""),
            colors=colors_str,
            typography=typography_str,
            nav_links=nav_links,
            page_name=page["name"],
            page_description=page["description"],
            sections=", ".join(page.get("sections", [])),
            design_tokens=design_tokens,
            filename=page["filename"],
            other_pages=other_pages,
        )
        html_content = call_claude(page_prompt, page["filename"], log_dir)
        if write_file(out_dir, page["filename"], html_content, resume):
            written += 1

    # 4. Summary
    print(f"\n{'='*60}")
    print(f"  COMPLETE — {written} files written to {out_dir}")
    print(f"  Logs: {log_dir}/calls.jsonl")
    print(f"  Open: {out_dir}/index.html")
    print(f"{'='*60}\n")

    # Write manifest
    manifest = {
        "site_name": site_name,
        "generated_at": datetime.utcnow().isoformat(),
        "files_written": written,
        "output_dir": str(out_dir),
        "spec_path": str(log_dir / "spec.json"),
    }
    with open(log_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Production Shop — Website Generation Agent"
    )
    parser.add_argument(
        "--spec", type=str, help="Path to site spec JSON file"
    )
    parser.add_argument(
        "--out", type=str, default="./output", help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip files that already exist (resume interrupted run)"
    )
    parser.add_argument(
        "--list-specs", action="store_true",
        help="List available spec files in ./specs/"
    )
    args = parser.parse_args()

    if args.list_specs:
        specs_dir = Path("./specs")
        if not specs_dir.exists():
            print("No specs/ directory found.")
            return
        specs = list(specs_dir.glob("*.json"))
        if not specs:
            print("No spec files found in specs/")
            return
        print(f"\nAvailable specs ({len(specs)}):")
        for s in specs:
            try:
                with open(s) as f:
                    data = json.load(f)
                print(f"  {s.name:40s} — {data.get('site_name', '?')} ({len(data.get('pages', []))} pages)")
            except Exception:
                print(f"  {s.name:40s} — (could not parse)")
        print()
        return

    if not args.spec:
        parser.print_help()
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    spec = load_spec(args.spec)
    out_dir = Path(args.out)
    generate_site(spec, out_dir, resume=args.resume)


if __name__ == "__main__":
    main()
