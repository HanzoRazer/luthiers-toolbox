#!/usr/bin/env python3
"""
AI Context Governance Comment Gate

Rule:
  If an AI router is registered, the mandatory governance
  comment block must be present in the same file.

This prevents undocumented AI capability creep.
"""

from pathlib import Path
import sys

REQUIRED_MARKER = "AI CONTEXT ADAPTER (v1)"
AI_ROUTER_HINTS = ("ai_context", "ai_", 'tags=["AI"', "tags=['AI'")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    main_py = repo_root / "services" / "api" / "app" / "main.py"

    if not main_py.exists():
        print("[ai-context-governance] ERROR: main.py not found", file=sys.stderr)
        return 2

    text = main_py.read_text(encoding="utf-8", errors="replace")

    ai_router_present = any(hint in text for hint in AI_ROUTER_HINTS)

    if ai_router_present and REQUIRED_MARKER not in text:
        print(
            "[ai-context-governance] FAIL:\n"
            "AI router detected but required governance comment block is missing.\n\n"
            f"Expected marker:\n  {REQUIRED_MARKER}\n\n"
            "Every AI capability must declare hard boundaries explicitly.",
            file=sys.stderr,
        )
        return 1

    print("[ai-context-governance] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
