"""
Project-level cost estimation.
"""

from typing import Dict, List
from .material import MaterialCost, MaterialDatabase
from .labor import LaborCost, LaborEstimator


class ProjectCost:
    """Represents the total cost of a guitar building project."""

    def __init__(self, project_name: str):
        """
        Initialize project cost tracker.
        
        Args:
            project_name: Name of the project
        """
        self.project_name = project_name
        self.materials: List[tuple] = []  # (MaterialCost, quantity)
        self.labor: List[LaborCost] = []
        self.overhead_rate: float = 0.15  # 15% overhead by default

    def add_material(self, material: MaterialCost, quantity: float) -> None:
        """
        Add a material to the project.
        
        Args:
            material: Material cost object
            quantity: Quantity needed
        """
        self.materials.append((material, quantity))

    def add_labor(self, labor: LaborCost) -> None:
        """
        Add labor to the project.
        
        Args:
            labor: Labor cost object
        """
        self.labor.append(labor)

    def get_material_cost(self) -> float:
        """Calculate total material cost."""
        return sum(mat.calculate_cost(qty) for mat, qty in self.materials)

    def get_labor_cost(self) -> float:
        """Calculate total labor cost."""
        return sum(labor.calculate_cost() for labor in self.labor)

    def get_overhead_cost(self) -> float:
        """Calculate overhead cost."""
        subtotal = self.get_material_cost() + self.get_labor_cost()
        return subtotal * self.overhead_rate

    def get_total_cost(self) -> float:
        """Calculate total project cost."""
        return (
            self.get_material_cost()
            + self.get_labor_cost()
            + self.get_overhead_cost()
        )

    def get_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown."""
        return {
            "materials": self.get_material_cost(),
            "labor": self.get_labor_cost(),
            "overhead": self.get_overhead_cost(),
            "total": self.get_total_cost(),
        }

    def get_detailed_breakdown(self) -> Dict:
        """Get detailed cost breakdown."""
        return {
            "project": self.project_name,
            "materials": [
                {
                    "name": mat.name,
                    "quantity": qty,
                    "unit": mat.unit,
                    "unit_price": mat.unit_price,
                    "cost": mat.calculate_cost(qty),
                }
                for mat, qty in self.materials
            ],
            "labor": [
                {
                    "task": labor.task,
                    "hours": labor.hours,
                    "rate": labor.hourly_rate,
                    "cost": labor.calculate_cost(),
                }
                for labor in self.labor
            ],
            "summary": self.get_breakdown(),
        }

    def __repr__(self) -> str:
        return (
            f"ProjectCost('{self.project_name}', "
            f"${self.get_total_cost():.2f} total)"
        )


class CostEstimator:
    """High-level cost estimator for guitar projects."""

    def __init__(self):
        """Initialize cost estimator."""
        self.material_db = MaterialDatabase()
        self.labor_estimator = LaborEstimator()

    def estimate_guitar(
        self,
        body_wood: str = "mahogany",
        neck_wood: str = "maple",
        fretboard_wood: str = "rosewood",
        hardware_level: str = "standard",
        include_electronics: bool = True,
        cnc_time_minutes: float = 120.0,
    ) -> ProjectCost:
        """
        Estimate cost for a complete guitar build.
        
        Args:
            body_wood: Wood for body
            neck_wood: Wood for neck
            fretboard_wood: Wood for fretboard
            hardware_level: 'budget', 'standard', or 'premium'
            include_electronics: Include pickups and electronics
            cnc_time_minutes: Estimated CNC machine time
            
        Returns:
            ProjectCost with full breakdown
        """
        project = ProjectCost("Electric Guitar Build")

        # Materials
        # Body (typical: 18" x 13" x 1.75")
        body_material = self.material_db.get_material(body_wood)
        if body_material:
            body_bf = self.material_db.calculate_board_feet(18, 13, 1.75)
            project.add_material(body_material, body_bf)

        # Neck (typical: 26" x 3" x 0.9")
        neck_material = self.material_db.get_material(neck_wood)
        if neck_material:
            neck_bf = self.material_db.calculate_board_feet(26, 3, 0.9)
            project.add_material(neck_material, neck_bf)

        # Fretboard (typical: 20" x 3" x 0.25")
        fb_material = self.material_db.get_material(fretboard_wood)
        if fb_material:
            fb_bf = self.material_db.calculate_board_feet(20, 3, 0.25)
            project.add_material(fb_material, fb_bf)

        # Hardware
        hardware_items = [
            "tuning_machines_set",
            "bridge",
            "nut_blank",
            "truss_rod",
            "fret_wire_2ft",
            "string_set",
        ]

        for item in hardware_items:
            material = self.material_db.get_material(item)
            if material:
                qty = 2 if item == "fret_wire_2ft" else 1
                project.add_material(material, qty)

        # Electronics
        if include_electronics:
            electronics = ["pickup_set", "potentiometer", "jack"]
            for item in electronics:
                material = self.material_db.get_material(item)
                if material:
                    qty = 2 if item == "potentiometer" else 1
                    project.add_material(material, qty)

        # Finish
        finish = self.material_db.get_material("lacquer")
        if finish:
            project.add_material(finish, 0.5)  # Half quart

        # Labor
        # Add key tasks
        tasks = [
            "body_rough_cut",
            "body_routing",
            "body_sanding",
            "body_finishing",
            "neck_rough_cut",
            "neck_shaping",
            "fretboard_slotting",
            "fret_installation",
            "fret_leveling",
            "hardware_installation",
            "setup_and_adjustment",
        ]

        if include_electronics:
            tasks.append("electronics_installation")

        for task in tasks:
            project.add_labor(self.labor_estimator.estimate_task(task))

        # Add CNC time
        if cnc_time_minutes > 0:
            project.add_labor(
                self.labor_estimator.estimate_cnc_time(cnc_time_minutes)
            )

        return project

    def __repr__(self) -> str:
        return "CostEstimator(ready)"
