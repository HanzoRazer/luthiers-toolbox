# Patch N14.x - Markdown → PDF rendering helper
#
# Uses:
#   - markdown (Python Markdown library) for MD → HTML
#   - weasyprint for HTML → PDF
#
# Make sure you have:
#   pip install markdown weasyprint
#
# This is intentionally minimal: we just wrap the Markdown in a basic
# HTML template and render to PDF bytes.

from __future__ import annotations

from typing import Optional

import markdown as md_lib

# WeasyPrint requires GTK system libraries on Windows
# Make import optional to allow graceful degradation
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    HTML = None
    WEASYPRINT_AVAILABLE = False
    import warnings
    warnings.warn(f"WeasyPrint not available (PDF export disabled): {e}")


def markdown_to_pdf_bytes(
    markdown_text: str,
    title: Optional[str] = None,
) -> bytes:
    """
    Render Markdown text to PDF bytes.

    Title is optional; if provided, it's used in the HTML <title> and
    as an H1 heading at the top of the document.

    Args:
        markdown_text: Markdown-formatted operator report
        title: Optional document title (appears as H1 and in PDF metadata)

    Returns:
        PDF bytes ready for HTTP response or file storage

    Example:
        pdf = markdown_to_pdf_bytes(
            markdown_text="# Test\\n\\nHello world",
            title="RMOS Operator Report"
        )
        with open("report.pdf", "wb") as f:
            f.write(pdf)
    """
    if not markdown_text:
        markdown_text = "# Empty Report\n\n(No content provided.)"

    body_html = md_lib.markdown(
        markdown_text,
        extensions=["extra", "tables", "fenced_code"],
    )

    if title:
        h1 = f"<h1>{title}</h1>"
        body_html = h1 + body_html

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title or "RMOS Studio Operator Report"}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                   sans-serif;
      font-size: 12pt;
      line-height: 1.4;
      margin: 24px;
    }}
    h1, h2, h3 {{
      margin-top: 1.0em;
      margin-bottom: 0.4em;
    }}
    ul, ol {{
      margin-left: 1.4em;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 0.5em 0;
    }}
    th, td {{
      border: 1px solid #ccc;
      padding: 4px 6px;
      font-size: 10pt;
    }}
    code {{
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono",
                   "Courier New", monospace;
      font-size: 10pt;
    }}
    blockquote {{
      border-left: 3px solid #999;
      padding-left: 8px;
      margin-left: 0;
      color: #555;
    }}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint is not available. PDF export requires GTK libraries. "
            "See https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation"
        )
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes
