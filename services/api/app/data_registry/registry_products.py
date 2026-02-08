"""Registry — Standalone product data accessors.

Extracted from registry.py (WP-3) for god-object decomposition.
These methods are mixed into the Registry class.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .registry_config import EntitlementError


class RegistryProductsMixin:
    """Mixin providing standalone product data accessors for Registry."""

    # --- ltb-parametric ($39-59) ---
    def get_guitar_templates(self) -> Dict[str, Any]:
        """Get parametric guitar templates (ltb-parametric only)"""
        self._check_entitlement("edition", "guitar_templates")
        return self._load_edition_data("guitar_templates.json")

    def get_guitar_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific parametric guitar template"""
        templates = self.get_guitar_templates()
        return templates.get("templates", {}).get(template_id)

    # --- ltb-neck-designer ($29-79) ---
    def get_neck_templates(self) -> Dict[str, Any]:
        """Get advanced neck templates (ltb-neck-designer only)"""
        self._check_entitlement("edition", "neck_templates")
        return self._load_edition_data("neck_templates.json")

    def get_neck_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific neck template"""
        templates = self.get_neck_templates()
        return templates.get("templates", {}).get(template_id)

    def get_truss_specs(self) -> Dict[str, Any]:
        """Get truss rod specifications (ltb-neck-designer only)"""
        self._check_entitlement("edition", "truss_specs")
        templates = self.get_neck_templates()
        return templates.get("truss_specs", {})

    # --- ltb-headstock-designer ($14-29) ---
    def get_headstock_templates(self) -> Dict[str, Any]:
        """Get headstock templates (ltb-headstock-designer only)"""
        self._check_entitlement("edition", "headstock_templates")
        return self._load_edition_data("headstock_templates.json")

    def get_headstock_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific headstock template"""
        templates = self.get_headstock_templates()
        return templates.get("templates", {}).get(template_id)

    def get_tuner_layouts(self) -> Dict[str, Any]:
        """Get tuner layout specifications (ltb-headstock-designer only)"""
        self._check_entitlement("edition", "tuner_layouts")
        templates = self.get_headstock_templates()
        return templates.get("tuner_layouts", {})

    # --- ltb-bridge-designer ($14-19) ---
    def get_bridge_templates(self) -> Dict[str, Any]:
        """Get bridge templates (ltb-bridge-designer only)"""
        self._check_entitlement("edition", "bridge_templates")
        return self._load_edition_data("bridge_templates.json")

    def get_bridge_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific bridge template"""
        templates = self.get_bridge_templates()
        return templates.get("templates", {}).get(template_id)

    def get_saddle_specs(self) -> Dict[str, Any]:
        """Get saddle specifications (ltb-bridge-designer only)"""
        self._check_entitlement("edition", "saddle_specs")
        templates = self.get_bridge_templates()
        return templates.get("saddle_specs", {})

    # --- ltb-fingerboard-designer ($19-29) ---
    def get_fretboard_templates(self) -> Dict[str, Any]:
        """Get fretboard templates (ltb-fingerboard-designer only)"""
        self._check_entitlement("edition", "fretboard_templates")
        return self._load_edition_data("fretboard_templates.json")

    def get_fretboard_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific fretboard template"""
        templates = self.get_fretboard_templates()
        return templates.get("templates", {}).get(template_id)

    def get_inlay_patterns(self) -> Dict[str, Any]:
        """Get inlay patterns (ltb-fingerboard-designer only)"""
        self._check_entitlement("edition", "inlay_patterns")
        templates = self.get_fretboard_templates()
        return templates.get("inlay_patterns", {})

    def get_fret_wire_specs(self) -> Dict[str, Any]:
        """Get fret wire specifications (ltb-fingerboard-designer only)"""
        self._check_entitlement("edition", "fretboard_templates")
        templates = self.get_fretboard_templates()
        return templates.get("fret_wire_specs", {})

    # --- ltb-cnc-blueprints ($29-49) ---
    def get_blueprint_standards(self) -> Dict[str, Any]:
        """Get housing industry blueprint standards (ltb-cnc-blueprints only)"""
        self._check_entitlement("edition", "blueprint_standards")
        return self._load_edition_data("blueprint_standards.json")

    def get_dimension_tables(self) -> Dict[str, Any]:
        """Get construction dimension tables (ltb-cnc-blueprints only)"""
        self._check_entitlement("edition", "dimension_tables")
        standards = self.get_blueprint_standards()
        return standards.get("dimension_tables", {})

    def get_construction_codes(self) -> Dict[str, Any]:
        """Get construction code references (ltb-cnc-blueprints only)"""
        self._check_entitlement("edition", "construction_codes")
        standards = self.get_blueprint_standards()
        return standards.get("construction_codes", {})
