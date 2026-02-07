"""
CP-S30: JSON-backed canonical CAM-Core tool registry.

Persistence: services/api/app/data/cam_core/tools.json
- created automatically if missing
- safe for single-user desktop ToolBox usage
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .models import BaseTool


_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "cam_core"
_TOOLS_JSON = _DATA_DIR / "tools.json"
_LOCK = threading.Lock()


def _ensure_store() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _TOOLS_JSON.exists():
        _TOOLS_JSON.write_text(json.dumps({"tools": []}, indent=2), encoding="utf-8")


def _read_store() -> Dict[str, Any]:
    _ensure_store()
    raw = _TOOLS_JSON.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:  # WP-1: narrowed from except Exception
        backup = _TOOLS_JSON.with_suffix(f".corrupt.{int(time.time())}.json")
        backup.write_text(raw, encoding="utf-8")
        return {"tools": []}


def _write_store(payload: Dict[str, Any]) -> None:
    _ensure_store()
    _TOOLS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def list_tools() -> List[Dict[str, Any]]:
    with _LOCK:
        store = _read_store()
        return store.get("tools", [])


def get_tool(tool_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        for tool in list_tools():
            if tool.get("id") == tool_id:
                return tool
    return None


def upsert_tool(tool: BaseTool) -> Dict[str, Any]:
    with _LOCK:
        store = _read_store()
        tools = store.get("tools", [])

        existing_idx = None
        for idx, existing in enumerate(tools):
            if existing.get("id") == tool.id:
                existing_idx = idx
                break

        if existing_idx is None:
            tools.append(tool.model_dump())
        else:
            tools[existing_idx] = tool.model_dump()

        store["tools"] = tools
        _write_store(store)
        return tool.model_dump()


def upsert_tools(tools_in: List[BaseTool]) -> List[Dict[str, Any]]:
    return [upsert_tool(tool) for tool in tools_in]


def new_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time())}"
