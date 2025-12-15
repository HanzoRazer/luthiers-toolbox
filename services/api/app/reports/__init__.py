# Patch N14.x - Reports package for RMOS Studio
#
# This package contains report generators for operator checklists,
# job summaries, and other manufacturing documentation.

from .operator_report import build_operator_markdown_report
from .pdf_renderer import markdown_to_pdf_bytes

__all__ = [
    "build_operator_markdown_report",
    "markdown_to_pdf_bytes",
]
