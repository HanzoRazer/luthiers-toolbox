"""
Material cost calculation and database.
"""

from typing import Dict, Optional
import json


class MaterialCost:
    """Represents the cost of a material."""

    def __init__(
        self,
        name: str,
        unit_price: float,
        unit: str = "board_foot",
        waste_factor: float = 1.2,
    ):
        """
        Initialize material cost.
        
        Args:
            name: Material name
            unit_price: Price per unit
            unit: Unit of measure (board_foot, square_foot, piece)
            waste_factor: Multiplier for waste (1.2 = 20% waste)
        """
        self.name = name
        self.unit_price = unit_price
        self.unit = unit
        self.waste_factor = waste_factor

    def calculate_cost(self, quantity: float) -> float:
        """
        Calculate total cost for given quantity.
        
        Args:
            quantity: Quantity in units
            
        Returns:
            Total cost including waste
        """
        return quantity * self.unit_price * self.waste_factor

    def __repr__(self) -> str:
        return f"MaterialCost('{self.name}', ${self.unit_price}/{self.unit})"


class MaterialDatabase:
    """Database of material costs."""

    def __init__(self):
        """Initialize material database with common luthier materials."""
        self.materials: Dict[str, MaterialCost] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default material costs."""
        # Tonewoods (per board foot)
        self.add_material(MaterialCost("mahogany", 15.0, "board_foot"))
        self.add_material(MaterialCost("maple", 12.0, "board_foot"))
        self.add_material(MaterialCost("rosewood", 35.0, "board_foot"))
        self.add_material(MaterialCost("ebony", 45.0, "board_foot"))
        self.add_material(MaterialCost("spruce", 10.0, "board_foot"))
        self.add_material(MaterialCost("cedar", 12.0, "board_foot"))
        self.add_material(MaterialCost("walnut", 18.0, "board_foot"))
        self.add_material(MaterialCost("ash", 10.0, "board_foot"))
        self.add_material(MaterialCost("alder", 8.0, "board_foot"))

        # Hardware and supplies (per piece)
        self.add_material(MaterialCost("tuning_machines_set", 40.0, "piece", 1.0))
        self.add_material(MaterialCost("bridge", 25.0, "piece", 1.0))
        self.add_material(MaterialCost("nut_blank", 3.0, "piece", 1.0))
        self.add_material(MaterialCost("truss_rod", 15.0, "piece", 1.0))
        self.add_material(MaterialCost("fret_wire_2ft", 8.0, "piece", 1.1))
        self.add_material(MaterialCost("string_set", 6.0, "piece", 1.0))
        self.add_material(MaterialCost("pickup_set", 120.0, "piece", 1.0))
        self.add_material(MaterialCost("potentiometer", 4.0, "piece", 1.0))
        self.add_material(MaterialCost("jack", 3.0, "piece", 1.0))

        # Finishes (per quart)
        self.add_material(MaterialCost("lacquer", 25.0, "quart", 1.3))
        self.add_material(MaterialCost("oil_finish", 15.0, "quart", 1.2))
        self.add_material(MaterialCost("poly_finish", 20.0, "quart", 1.3))

    def add_material(self, material: MaterialCost) -> None:
        """Add or update a material in the database."""
        self.materials[material.name] = material

    def get_material(self, name: str) -> Optional[MaterialCost]:
        """Get a material by name."""
        return self.materials.get(name)

    def list_materials(self) -> Dict[str, MaterialCost]:
        """Get all materials."""
        return self.materials.copy()

    def calculate_board_feet(
        self, length: float, width: float, thickness: float
    ) -> float:
        """
        Calculate board feet for given dimensions.
        
        Args:
            length: Length in inches
            width: Width in inches
            thickness: Thickness in inches
            
        Returns:
            Volume in board feet
        """
        # Board foot = (length * width * thickness) / 144
        return (length * width * thickness) / 144

    def save_to_file(self, filename: str) -> None:
        """Save material database to JSON file."""
        data = {
            name: {
                "unit_price": mat.unit_price,
                "unit": mat.unit,
                "waste_factor": mat.waste_factor,
            }
            for name, mat in self.materials.items()
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load material database from JSON file."""
        with open(filename, "r") as f:
            data = json.load(f)

        for name, mat_data in data.items():
            self.add_material(
                MaterialCost(
                    name=name,
                    unit_price=mat_data["unit_price"],
                    unit=mat_data["unit"],
                    waste_factor=mat_data["waste_factor"],
                )
            )

    def __repr__(self) -> str:
        return f"MaterialDatabase({len(self.materials)} materials)"
