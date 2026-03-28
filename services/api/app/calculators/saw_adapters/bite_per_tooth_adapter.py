"""
Bite Per Tooth Adapter

Adapts Saw Lab's bite-per-tooth calculator to the Calculator Spine interface.

MODEL NOTES:
- Assumes constant feed rate (no acceleration/deceleration)
- Assumes all teeth are engaged equally
- Does not account for gullet capacity

Formula:
    bite_per_tooth_mm = feed_mm_min / (rpm * tooth_count)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Try to import from Saw Lab if available
try:
    from ...saw_lab.calculators.bite_per_tooth import (
        compute_bite as _saw_lab_compute_bite,
    )
    _HAS_SAW_LAB = True
except ImportError:
    _HAS_SAW_LAB = False


@dataclass
class BitePerToothResult:
    """Result from bite-per-tooth calculation."""
    bite_mm: float
    in_range: bool
    min_recommended_mm: float
    max_recommended_mm: float
    message: str


def compute_bite_per_tooth(
    feed_mm_min: float,
    rpm: float,
    tooth_count: int,
    *,
    min_bite_mm: float = 0.05,
    max_bite_mm: float = 0.50,
) -> BitePerToothResult:
    """
    Calculate bite per tooth (chip thickness) for a saw blade.

    Args:
        feed_mm_min: Feed rate in mm/min
        rpm: Blade RPM
        tooth_count: Number of teeth on blade
        min_bite_mm: Minimum recommended bite (default 0.05mm)
        max_bite_mm: Maximum recommended bite (default 0.50mm)

    Returns:
        BitePerToothResult with calculated bite and range check
    """
    if rpm <= 0 or tooth_count <= 0:
        return BitePerToothResult(
            bite_mm=0.0,
            in_range=False,
            min_recommended_mm=min_bite_mm,
            max_recommended_mm=max_bite_mm,
            message="Invalid RPM or tooth count",
        )

    # Delegate to Saw Lab if available
    if _HAS_SAW_LAB:
        bite = _saw_lab_compute_bite(feed_mm_min, rpm, tooth_count)
    else:
        # Direct calculation
        bite = feed_mm_min / (rpm * tooth_count)

    in_range = min_bite_mm <= bite <= max_bite_mm

    if bite < min_bite_mm:
        message = f"Bite too low ({bite:.4f}mm < {min_bite_mm}mm) - risk of rubbing/burning"
    elif bite > max_bite_mm:
        message = f"Bite too high ({bite:.4f}mm > {max_bite_mm}mm) - risk of overload"
    else:
        message = f"Bite in range ({bite:.4f}mm)"

    return BitePerToothResult(
        bite_mm=bite,
        in_range=in_range,
        min_recommended_mm=min_bite_mm,
        max_recommended_mm=max_bite_mm,
        message=message,
    )
