"""
Labor cost estimation.
"""

from typing import Dict


class LaborCost:
    """Represents labor cost for a task."""

    def __init__(
        self,
        task: str,
        hours: float,
        hourly_rate: float = 50.0,
    ):
        """
        Initialize labor cost.
        
        Args:
            task: Task description
            hours: Estimated hours
            hourly_rate: Hourly rate
        """
        self.task = task
        self.hours = hours
        self.hourly_rate = hourly_rate

    def calculate_cost(self) -> float:
        """Calculate total labor cost."""
        return self.hours * self.hourly_rate

    def __repr__(self) -> str:
        return f"LaborCost('{self.task}', {self.hours}h @ ${self.hourly_rate}/h)"


class LaborEstimator:
    """Estimates labor costs for guitar building tasks."""

    def __init__(self, hourly_rate: float = 50.0):
        """
        Initialize labor estimator.
        
        Args:
            hourly_rate: Default hourly rate
        """
        self.hourly_rate = hourly_rate
        self.task_estimates = self._get_default_estimates()

    def _get_default_estimates(self) -> Dict[str, float]:
        """Get default time estimates for common tasks (in hours)."""
        return {
            # Body work
            "body_rough_cut": 1.0,
            "body_routing": 2.0,
            "body_sanding": 3.0,
            "body_binding": 4.0,
            "body_finishing": 8.0,
            # Neck work
            "neck_rough_cut": 1.5,
            "neck_shaping": 4.0,
            "neck_sanding": 2.0,
            "neck_finishing": 4.0,
            # Fretboard
            "fretboard_slotting": 2.0,
            "fretboard_radius": 2.0,
            "fretboard_inlays": 3.0,
            "fretboard_finishing": 2.0,
            # Fretting
            "fret_installation": 3.0,
            "fret_leveling": 2.0,
            "fret_crowning": 2.0,
            "fret_polishing": 1.0,
            # Assembly
            "neck_attachment": 1.0,
            "hardware_installation": 2.0,
            "electronics_installation": 2.0,
            "setup_and_adjustment": 2.0,
            # Total typical build
            "complete_guitar": 45.0,
        }

    def estimate_task(self, task: str) -> LaborCost:
        """
        Estimate labor cost for a specific task.
        
        Args:
            task: Task name
            
        Returns:
            Labor cost estimate
        """
        hours = self.task_estimates.get(task, 1.0)
        return LaborCost(task, hours, self.hourly_rate)

    def estimate_custom_task(self, task: str, hours: float) -> LaborCost:
        """
        Estimate labor cost for a custom task.
        
        Args:
            task: Task description
            hours: Estimated hours
            
        Returns:
            Labor cost estimate
        """
        return LaborCost(task, hours, self.hourly_rate)

    def estimate_cnc_time(self, machine_time_minutes: float) -> LaborCost:
        """
        Estimate cost for CNC machine time.
        
        Args:
            machine_time_minutes: Machine time in minutes
            
        Returns:
            Labor cost for machine time
        """
        hours = machine_time_minutes / 60
        # CNC time typically includes setup and supervision
        # Add 20% for setup and monitoring
        total_hours = hours * 1.2
        return LaborCost("CNC machining", total_hours, self.hourly_rate)

    def get_all_estimates(self) -> Dict[str, LaborCost]:
        """Get all task estimates as LaborCost objects."""
        return {
            task: LaborCost(task, hours, self.hourly_rate)
            for task, hours in self.task_estimates.items()
        }

    def __repr__(self) -> str:
        return f"LaborEstimator(${self.hourly_rate}/h, {len(self.task_estimates)} tasks)"
