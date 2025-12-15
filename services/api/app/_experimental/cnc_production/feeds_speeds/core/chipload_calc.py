"""Basic chipload helpers."""


def calc_chipload_mm(feed_mm_min: float, rpm: int, flutes: int) -> float:
    """Return chipload in millimeters (feed / (rpm * flutes))."""
    if rpm <= 0 or flutes <= 0:
        raise ValueError("RPM and flutes must be positive to compute chipload")
    return feed_mm_min / (rpm * flutes)
