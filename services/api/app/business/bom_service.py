"""
BOM Service — Bill of Materials management for instrument building.

Helps luthiers answer: "What materials do I need and what do they cost?"
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone

from .schemas import (
    Material,
    MaterialCategory,
    BOMItem,
    BillOfMaterials,
    InstrumentType,
)


class BOMService:
    """
    Bill of Materials service for guitar building.

    Responsibilities:
    - Create BOM from templates
    - Calculate material costs
    - Track supplier pricing
    - Generate shopping lists
    """

    # Default material library (user can extend)
    DEFAULT_MATERIALS: Dict[str, Material] = {
        # Tonewoods
        "sitka_top_aaa": Material(
            id="sitka_top_aaa",
            name="Sitka Spruce Top Set (AAA)",
            category=MaterialCategory.TONEWOOD,
            unit="set",
            unit_cost=85.00,
            species="Sitka Spruce",
            grade="AAA",
        ),
        "indian_rosewood_back": Material(
            id="indian_rosewood_back",
            name="Indian Rosewood Back & Sides",
            category=MaterialCategory.TONEWOOD,
            unit="set",
            unit_cost=120.00,
            species="Indian Rosewood",
            grade="A",
        ),
        "mahogany_neck": Material(
            id="mahogany_neck",
            name="Honduran Mahogany Neck Blank",
            category=MaterialCategory.TONEWOOD,
            unit="piece",
            unit_cost=45.00,
            species="Honduran Mahogany",
        ),
        "ebony_fretboard": Material(
            id="ebony_fretboard",
            name="Ebony Fretboard Blank",
            category=MaterialCategory.TONEWOOD,
            unit="piece",
            unit_cost=55.00,
            species="Ebony",
            grade="A",
        ),
        "ebony_bridge": Material(
            id="ebony_bridge",
            name="Ebony Bridge Blank",
            category=MaterialCategory.TONEWOOD,
            unit="piece",
            unit_cost=18.00,
            species="Ebony",
        ),

        # Hardware
        "tuners_gotoh_510": Material(
            id="tuners_gotoh_510",
            name="Gotoh 510 Tuners (Set of 6)",
            category=MaterialCategory.HARDWARE,
            unit="set",
            unit_cost=95.00,
        ),
        "nut_bone": Material(
            id="nut_bone",
            name="Bone Nut Blank",
            category=MaterialCategory.HARDWARE,
            unit="piece",
            unit_cost=8.00,
        ),
        "saddle_bone": Material(
            id="saddle_bone",
            name="Bone Saddle Blank",
            category=MaterialCategory.HARDWARE,
            unit="piece",
            unit_cost=8.00,
        ),
        "bridge_pins_ebony": Material(
            id="bridge_pins_ebony",
            name="Ebony Bridge Pins (Set of 6)",
            category=MaterialCategory.HARDWARE,
            unit="set",
            unit_cost=24.00,
        ),
        "truss_rod_dual": Material(
            id="truss_rod_dual",
            name="Dual Action Truss Rod",
            category=MaterialCategory.HARDWARE,
            unit="piece",
            unit_cost=22.00,
        ),
        "strap_buttons": Material(
            id="strap_buttons",
            name="Strap Buttons (Pair)",
            category=MaterialCategory.HARDWARE,
            unit="pair",
            unit_cost=6.00,
        ),

        # Fret wire
        "fret_wire_evo": Material(
            id="fret_wire_evo",
            name="EVO Gold Fret Wire (2 ft)",
            category=MaterialCategory.FRET_WIRE,
            unit="piece",
            unit_cost=28.00,
        ),

        # Binding
        "binding_abs_white": Material(
            id="binding_abs_white",
            name="ABS White Binding",
            category=MaterialCategory.BINDING,
            unit="strip",
            unit_cost=4.00,
        ),
        "purfling_bwb": Material(
            id="purfling_bwb",
            name="Black-White-Black Purfling",
            category=MaterialCategory.BINDING,
            unit="strip",
            unit_cost=3.50,
        ),

        # Finish
        "lacquer_nitro_qt": Material(
            id="lacquer_nitro_qt",
            name="Nitrocellulose Lacquer (Quart)",
            category=MaterialCategory.FINISH,
            unit="quart",
            unit_cost=32.00,
        ),

        # Adhesives
        "glue_titebond": Material(
            id="glue_titebond",
            name="Titebond Original (16 oz)",
            category=MaterialCategory.ADHESIVE,
            unit="bottle",
            unit_cost=8.00,
        ),
        "glue_hide": Material(
            id="glue_hide",
            name="Hide Glue (Granules 1 lb)",
            category=MaterialCategory.ADHESIVE,
            unit="lb",
            unit_cost=18.00,
        ),

        # Strings
        "strings_pb_light": Material(
            id="strings_pb_light",
            name="Phosphor Bronze Strings (Light)",
            category=MaterialCategory.STRINGS,
            unit="set",
            unit_cost=12.00,
        ),
    }

    # BOM templates by instrument type
    BOM_TEMPLATES: Dict[InstrumentType, List[tuple]] = {
        InstrumentType.ACOUSTIC_DREADNOUGHT: [
            ("sitka_top_aaa", 1),
            ("indian_rosewood_back", 1),
            ("mahogany_neck", 1),
            ("ebony_fretboard", 1),
            ("ebony_bridge", 1),
            ("tuners_gotoh_510", 1),
            ("nut_bone", 1),
            ("saddle_bone", 1),
            ("bridge_pins_ebony", 1),
            ("truss_rod_dual", 1),
            ("strap_buttons", 1),
            ("fret_wire_evo", 1),
            ("binding_abs_white", 4),
            ("purfling_bwb", 4),
            ("lacquer_nitro_qt", 2),
            ("glue_titebond", 0.25),
            ("strings_pb_light", 1),
        ],
        InstrumentType.CLASSICAL: [
            ("sitka_top_aaa", 1),
            ("indian_rosewood_back", 1),
            ("mahogany_neck", 1),
            ("ebony_fretboard", 1),
            ("ebony_bridge", 1),
            ("tuners_gotoh_510", 1),
            ("nut_bone", 1),
            ("saddle_bone", 1),
            ("fret_wire_evo", 1),
            ("binding_abs_white", 2),
            ("purfling_bwb", 2),
            ("lacquer_nitro_qt", 2),
            ("glue_hide", 0.25),
        ],
    }

    def __init__(self, custom_materials: Optional[Dict[str, Material]] = None):
        """Initialize with optional custom materials."""
        self.materials = {**self.DEFAULT_MATERIALS}
        if custom_materials:
            self.materials.update(custom_materials)

    def create_bom_from_template(
        self,
        instrument_type: InstrumentType,
        instrument_name: str,
        price_overrides: Optional[Dict[str, float]] = None,
    ) -> BillOfMaterials:
        """
        Create a BOM from a template.

        Args:
            instrument_type: Type of instrument
            instrument_name: Custom name for this build
            price_overrides: Override prices for specific materials

        Returns:
            Complete BillOfMaterials
        """
        template = self.BOM_TEMPLATES.get(instrument_type, [])
        items: List[BOMItem] = []
        cost_by_category: Dict[str, float] = {}

        for material_id, quantity in template:
            if material_id not in self.materials:
                continue

            material = self.materials[material_id]
            unit_cost = (
                price_overrides.get(material_id, material.unit_cost)
                if price_overrides
                else material.unit_cost
            )
            extended_cost = quantity * unit_cost

            items.append(BOMItem(
                material_id=material_id,
                material_name=material.name,
                category=material.category,
                quantity=quantity,
                unit=material.unit,
                unit_cost=unit_cost,
                extended_cost=extended_cost,
            ))

            # Accumulate by category
            cat_key = material.category.value
            cost_by_category[cat_key] = cost_by_category.get(cat_key, 0) + extended_cost

        total_cost = sum(item.extended_cost for item in items)

        return BillOfMaterials(
            instrument_type=instrument_type,
            instrument_name=instrument_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            items=items,
            total_materials_cost=total_cost,
            total_items=len(items),
            cost_by_category=cost_by_category,
        )

    def create_custom_bom(
        self,
        instrument_name: str,
        items: List[tuple],  # [(material_id, quantity), ...]
    ) -> BillOfMaterials:
        """
        Create a custom BOM from a list of items.

        Args:
            instrument_name: Name for this build
            items: List of (material_id, quantity) tuples

        Returns:
            Complete BillOfMaterials
        """
        bom_items: List[BOMItem] = []
        cost_by_category: Dict[str, float] = {}

        for material_id, quantity in items:
            if material_id not in self.materials:
                continue

            material = self.materials[material_id]
            extended_cost = quantity * material.unit_cost

            bom_items.append(BOMItem(
                material_id=material_id,
                material_name=material.name,
                category=material.category,
                quantity=quantity,
                unit=material.unit,
                unit_cost=material.unit_cost,
                extended_cost=extended_cost,
            ))

            cat_key = material.category.value
            cost_by_category[cat_key] = cost_by_category.get(cat_key, 0) + extended_cost

        total_cost = sum(item.extended_cost for item in bom_items)

        return BillOfMaterials(
            instrument_type=InstrumentType.CUSTOM,
            instrument_name=instrument_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            items=bom_items,
            total_materials_cost=total_cost,
            total_items=len(bom_items),
            cost_by_category=cost_by_category,
        )

    def get_material(self, material_id: str) -> Optional[Material]:
        """Get a material by ID."""
        return self.materials.get(material_id)

    def list_materials(
        self,
        category: Optional[MaterialCategory] = None,
    ) -> List[Material]:
        """List all materials, optionally filtered by category."""
        materials = list(self.materials.values())
        if category:
            materials = [m for m in materials if m.category == category]
        return sorted(materials, key=lambda m: m.name)

    def add_material(self, material: Material) -> None:
        """Add or update a material in the library."""
        self.materials[material.id] = material

    def generate_shopping_list(
        self,
        bom: BillOfMaterials,
        group_by_supplier: bool = True,
    ) -> Dict[str, List[Dict]]:
        """
        Generate a shopping list from a BOM.

        Returns dict grouped by supplier or category.
        """
        shopping_list: Dict[str, List[Dict]] = {}

        for item in bom.items:
            material = self.materials.get(item.material_id)
            group_key = (
                material.supplier if group_by_supplier and material and material.supplier
                else item.category.value
            )

            if group_key not in shopping_list:
                shopping_list[group_key] = []

            shopping_list[group_key].append({
                "material": item.material_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "estimated_cost": item.extended_cost,
            })

        return shopping_list
