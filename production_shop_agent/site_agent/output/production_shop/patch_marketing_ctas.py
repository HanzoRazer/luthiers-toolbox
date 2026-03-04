"""
Run from inside your static marketing site folder:
    python patch_marketing_ctas.py --app-url http://localhost:5173

Updates all "Get Started", "Try Free", "Start Building" etc. hrefs
to point at the live Vue app.
"""
import re
import sys
import glob
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--app-url', default='http://localhost:5173')
args = parser.parse_args()

APP_URL = args.app_url.rstrip('/')

# Patterns that should link to the app
CTA_PATTERNS = [
    r'Get Started',
    r'Start.*[Ff]ree',
    r'Try.*[Ff]ree',
    r'Start [Bb]uilding',
    r'Start [Yy]our [Ff]ree',
    r'Launch App',
    r'Open App',
    r'Get Early Access',
]
combined = '|'.join(CTA_PATTERNS)

changed = 0
for html_file in glob.glob('*.html'):
    text = Path(html_file).read_text(encoding='utf-8')
    original = text

    # Find <a ...>TEXT</a> where TEXT matches a CTA pattern
    # Replace href="#" or href="" or href="pricing.html" with the app URL
    def replace_cta_href(m):
        tag = m.group(0)
        # If href already points to an external URL, leave it
        if re.search(r'href="https?://(?!localhost)', tag):
            return tag
        # Inject app URL
        tag = re.sub(r'href="[^"]*"', f'href="{APP_URL}"', tag)
        if 'target=' not in tag:
            tag = tag.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        return tag

    # Match <a> tags that contain CTA text
    text = re.sub(
        rf'<a\b[^>]*>(?:[^<]*?(?:{combined})[^<]*?)</a>',
        replace_cta_href,
        text,
        flags=re.IGNORECASE,
    )

    if text != original:
        Path(html_file).write_text(text, encoding='utf-8')
        print(f'  [OK] patched: {html_file}')
        changed += 1

print(f'\n[DONE] {changed} files updated -> {APP_URL}')
