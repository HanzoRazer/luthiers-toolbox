from __future__ import annotations

import importlib
import os
from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class RmosEngine(Protocol):
    """
    Minimal contract your real RMOS implementation must satisfy.
    """

    def compute_feasibility_for_design(self, design: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Must return a dict with at least:
          - score: float (0..100)
          - risk_bucket: "GREEN"|"YELLOW"|"RED"
          - warnings: list[str]
          - (optional) details: any
        """
        ...

    def generate_toolpaths_for_design(self, design: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Must return a dict with at least:
          - plan_id: str
          - (optional) ops/summary/etc
        """
        ...

    def get_policy_version(self) -> str:
        ...

    def get_calculator_versions(self) -> Dict[str, str]:
        ...


def load_rmos_engine() -> RmosEngine:
    """
    Loads RMOS engine from module path.

    Configure with env var:
      RMOS_ENGINE_MODULE="app.rmos.impl"   (example)
    The module must expose: `ENGINE` (instance) or `get_engine()` (callable returning instance).
    """
    mod_path = os.getenv("RMOS_ENGINE_MODULE", "").strip()
    if not mod_path:
        raise RuntimeError(
            "RMOS_ENGINE_MODULE is not set. Point it at your real RMOS module, "
            "which must expose ENGINE or get_engine()."
        )

    mod = importlib.import_module(mod_path)

    if hasattr(mod, "ENGINE"):
        engine = getattr(mod, "ENGINE")
        if not isinstance(engine, RmosEngine):
            # runtime_checkable Protocol allows isinstance checks
            raise RuntimeError(f"{mod_path}.ENGINE does not satisfy RmosEngine protocol.")
        return engine