"""
G-code Lexer

Tokenization and comment stripping for G-code programs.
Supports both parser and reader workflows.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# Regex patterns
NUM: str = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
TOKEN_RE = re.compile(rf"([A-Za-z])\s*({NUM})")
WORD_RE = re.compile(r"([A-Za-z])([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)")
COMMENT_PAREN_RE = re.compile(r"\(.*?\)")
COMMENT_SEMI_RE = re.compile(r";.*$")


def strip_comments(line: str) -> str:
    """Remove parenthetical and semicolon comments from a G-code line."""
    line = COMMENT_PAREN_RE.sub("", line)
    line = COMMENT_SEMI_RE.sub("", line)
    return line.strip()


def parse_words(line: str) -> Dict[str, float]:
    """Parse a line into a dict of letter -> numeric value."""
    return {m.group(1).upper(): float(m.group(2)) for m in WORD_RE.finditer(line)}


def parse_lines(gcode: str) -> List[Dict[str, Any]]:
    """
    Parse G-code into structured lines with word tokens.

    Filters comments (parentheses and semicolon) and empty lines.
    Returns list of dicts with 'raw' line and 'words' [(letter, value), ...]

    Example:
        >>> parse_lines("G0 X10 Y20\\nG1 Z-1 F500")
        [{'raw': 'G0 X10 Y20', 'words': [('G', 0.0), ('X', 10.0), ('Y', 20.0)]},
         {'raw': 'G1 Z-1 F500', 'words': [('G', 1.0), ('Z', -1.0), ('F', 500.0)]}]
    """
    out = []
    for raw in gcode.splitlines():
        line = raw.strip()
        if not line or line.startswith('(') or line.startswith(';'):
            continue
        # Remove inline comments
        line = re.sub(r"\(.*?\)", "", line)
        line = line.split(';', 1)[0].strip()
        if not line:
            continue

        # Extract word tokens (letter + number)
        words = [(m.group(1).upper(), float(m.group(2))) for m in TOKEN_RE.finditer(line)]
        if not words:
            continue

        out.append({"raw": raw, "words": words})

    return out
