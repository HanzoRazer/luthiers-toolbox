"""
RMOS Engine Registry

Single source of truth for engine/toolchain/post-processor versions.
Ensures consistent version stamping across all run artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any, Literal


EngineKind = Literal["feasibility", "toolchain", "post_processor"]


@dataclass(frozen=True)
class EngineDescriptor:
    """Descriptor for a registered engine/toolchain/post-processor."""
    kind: EngineKind
    engine_id: str               # stable id (e.g., "feas_v1")
    version: str                 # human-readable version (e.g., "1.0.0")
    impl: str                    # import path or label
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


class EngineRegistry:
    """
    Registry for all execution engines.
    
    Keep this deterministic and static. Changes require version bumps.
    """

    def __init__(self):
        # Feasibility engine
        self.feasibility_engine = EngineDescriptor(
            kind="feasibility",
            engine_id="feas_v1",
            version="1.0.0",
            impl="app.rmos.feasibility:score_design_feasibility",
            description="Authoritative server-side feasibility scorer",
        )

        # Toolchain registry
        self.toolchains: Dict[str, EngineDescriptor] = {
            "rosette_cam_v1": EngineDescriptor(
                kind="toolchain",
                engine_id="rosette_cam_v1",
                version="1.0.0",
                impl="app.rmos.toolpaths:generate_toolpaths_server_side",
                description="Rosette CAM toolpath generator",
            ),
        }

        # Post-processor registry
        self.post_processors: Dict[str, EngineDescriptor] = {
            "grbl_post_v2": EngineDescriptor(
                kind="post_processor",
                engine_id="grbl_post_v2",
                version="2.0.0",
                impl="app.rmos.posts.grbl:render",
                description="GRBL post-processor templates v2",
            ),
            "fanuc_post_v1": EngineDescriptor(
                kind="post_processor",
                engine_id="fanuc_post_v1",
                version="1.0.0",
                impl="app.rmos.posts.fanuc:render",
                description="FANUC post-processor templates v1",
            ),
        }

    # -------- Resolution helpers --------

    def resolve_feasibility(self) -> EngineDescriptor:
        """Get the active feasibility engine."""
        return self.feasibility_engine

    def resolve_toolchain(self, toolchain_id: Optional[str]) -> EngineDescriptor:
        """Resolve toolchain by ID, with fallback to default."""
        if toolchain_id and toolchain_id in self.toolchains:
            return self.toolchains[toolchain_id]
        return self.toolchains["rosette_cam_v1"]

    def resolve_post_processor(self, post_processor_id: Optional[str]) -> Optional[EngineDescriptor]:
        """Resolve post-processor by ID."""
        if not post_processor_id:
            return None
        return self.post_processors.get(post_processor_id)

    # -------- Config summaries for stamping --------

    def approval_config_summary(
        self,
        *,
        workflow_mode: Optional[str],
        tool_id: Optional[str],
        material_id: Optional[str],
        machine_id: Optional[str],
    ) -> Dict[str, Any]:
        """Build config summary for approval artifacts."""
        feas = self.resolve_feasibility()
        return {
            "policy": "server_side_feasibility_enforced",
            "feasibility_engine_id": feas.engine_id,
            "feasibility_engine_version": feas.version,
            "workflow_mode": workflow_mode,
            "tool_id": tool_id,
            "material_id": material_id,
            "machine_id": machine_id,
        }

    def toolpaths_config_summary(
        self,
        *,
        toolchain_id: Optional[str],
        post_processor_id: Optional[str],
        workflow_mode: Optional[str],
        tool_id: Optional[str],
        material_id: Optional[str],
        machine_id: Optional[str],
    ) -> Dict[str, Any]:
        """Build config summary for toolpaths artifacts."""
        feas = self.resolve_feasibility()
        tc = self.resolve_toolchain(toolchain_id)
        pp = self.resolve_post_processor(post_processor_id)
        return {
            "policy": "server_side_feasibility_enforced",
            "feasibility_engine_id": feas.engine_id,
            "feasibility_engine_version": feas.version,
            "toolchain_id": tc.engine_id,
            "toolchain_version": tc.version,
            "post_processor_id": pp.engine_id if pp else None,
            "post_processor_version": pp.version if pp else None,
            "workflow_mode": workflow_mode,
            "tool_id": tool_id,
            "material_id": material_id,
            "machine_id": machine_id,
        }


# Singleton instance
REGISTRY = EngineRegistry()
