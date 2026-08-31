# tests/test_spatial_hash.py
"""Spatial hash - O(n) point deduplication.

Split out of test_dxf_security_patch.py. Replaces that module's O(n^2) linear
scan; these tests assert the complexity property rather than wall-clock time.
"""

from app.cam.spatial_hash import SpatialHash

# A complexity-regression guard -- NOT a performance guarantee. It answers only
# "is dedup still roughly constant work per insert?", not how fast it runs,
# which is what the two wall-clock assertions it replaced tried to do and why
# they went: they graded the CI runner, not the algorithm.
#
# Sensitivity follows point DENSITY, not count. Per-insert comparisons as
# cell_size degrades (FAIL = this bound catches it):
#   1,417 random / 400x300mm:  0.1mm 0.00 | 1mm 0.06 | 10mm 5.03 | 100mm 348 FAIL
#   10,000 grid / 50x50mm:     0.1mm 0.00 | 1mm 17.0 FAIL | 10mm 1351 FAIL
# So the dense grid is the tighter guard. This is a constant-factor bound, not a
# strict complexity bound -- at 1mm the grid case is still O(1) per insert, with
# a constant of 17. Failing there is deliberate: cell_size is not a live knob.
# SpatialHash is built in one place, app/cam/graph_algorithms.py, always with
# SPATIAL_HASH_CELL_SIZE_MM (0.1mm, app/cam/dxf_limits.py, for 0.01mm CNC tol).
MAX_COMPARISONS_PER_INSERT = 10


def _counting_point_class(counter):
    """A PointLike whose is_close() increments ``counter``.

    find_existing() calls is_close() exactly once per candidate in the 3x3 cell
    neighbourhood, so the call count *is* the work the spatial hash does --
    which is what makes the claim checkable without timing anything.
    """

    class CountingPoint:
        __slots__ = ("x", "y")

        def __init__(self, x, y):
            self.x, self.y = x, y

        def is_close(self, other, tolerance=0.001):
            counter["comparisons"] += 1
            return (abs(self.x - other.x) < tolerance
                    and abs(self.y - other.y) < tolerance)

    return CountingPoint


# =============================================================================
# Deduplication behaviour
# =============================================================================

class TestSpatialHashPerformance:
    """Test O(n) spatial hash replaces O(n²) linear scan."""
    
    class MockPoint:
        """Mock point for testing."""
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y
        
        def is_close(self, other, tolerance=0.001):
            dx = abs(self.x - other.x)
            dy = abs(self.y - other.y)
            return dx < tolerance and dy < tolerance
    
    def test_deduplicate_exact_duplicates(self):
        """Should deduplicate exact duplicate points."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.0, 20.0)  # Exact duplicate
        
        idx1 = hasher.get_or_add(p1)
        idx2 = hasher.get_or_add(p2)
        
        assert idx1 == idx2  # Same index = deduplication worked
        assert len(hasher.points) == 1
    
    def test_deduplicate_within_tolerance(self):
        """Should deduplicate points within tolerance."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.0005, 20.0003)  # Within 0.001mm
        
        idx1 = hasher.get_or_add(p1, tolerance=0.001)
        idx2 = hasher.get_or_add(p2, tolerance=0.001)
        
        assert idx1 == idx2
        assert len(hasher.points) == 1
    
    def test_keep_distinct_points(self):
        """Should keep points beyond tolerance."""
        hasher = SpatialHash(cell_size=0.1)
        
        p1 = self.MockPoint(10.0, 20.0)
        p2 = self.MockPoint(10.5, 20.5)  # Far apart
        
        idx1 = hasher.get_or_add(p1)
        idx2 = hasher.get_or_add(p2)
        
        assert idx1 != idx2
        assert len(hasher.points) == 2
    
    def test_handle_cell_boundaries(self):
        """Should find duplicates across cell boundaries."""
        hasher = SpatialHash(cell_size=1.0)
        
        # Points near cell boundary (0.9999 and 1.0001 are in different cells)
        p1 = self.MockPoint(0.9999, 0.0)
        p2 = self.MockPoint(1.0001, 0.0)  # Within tolerance but different cells
        
        idx1 = hasher.get_or_add(p1, tolerance=0.001)
        idx2 = hasher.get_or_add(p2, tolerance=0.001)
        
        assert idx1 == idx2  # 3x3 neighborhood search found it
    
    def test_performance_scaling(self):
        """10K points stay O(1) per insert, not O(n^2).

        Asserted ``elapsed < 1.0`` until 2026-08-31 -- a runner-speed bound that
        had not tripped yet (~0.036s locally, but ~4s at the 110x CI contention
        its sibling hit). See MAX_COMPARISONS_PER_INSERT.
        """
        counter = {"comparisons": 0}
        point_cls = _counting_point_class(counter)

        hasher = SpatialHash(cell_size=0.1)

        # 10,000 points on a 0.5mm grid, i.e. a 50x50mm area
        points = [
            point_cls(x * 0.5, y * 0.5)
            for x in range(100)
            for y in range(100)
        ]

        for p in points:
            hasher.get_or_add(p)

        n = len(points)
        assert len(hasher.points) == n, "grid points are distinct; none may be merged"
        assert counter["comparisons"] < MAX_COMPARISONS_PER_INSERT * n, (
            f"{counter['comparisons']} comparisons for {n} inserts "
            f"({counter['comparisons'] / n:.1f} per insert) exceeds the "
            f"{MAX_COMPARISONS_PER_INSERT}/insert bound; a linear scan would be "
            f"~{n * (n - 1) // 2:,}"
        )


# =============================================================================
# Complexity guards
# =============================================================================

class TestSpatialHashComplexity:
    """Comparison-count guards against a regression to linear scan."""

    def test_spatial_hash_does_not_degenerate_to_linear_scan(self):
        """Realistic guitar-body point count stays O(1) per insert.

        Replaces ``elapsed < 0.1``, which measured the runner (~0.005s locally,
        0.604s on a contended CI box, failing an unrelated PR). What matters is
        that dedup has not regressed to the O(n^2) scan this module replaced,
        and comparison count measures that directly.
        """
        import random

        from app.cam.spatial_hash import SpatialHash

        counter = {"comparisons": 0}
        point_cls = _counting_point_class(counter)

        # Simulate Stratocaster body (1,417 points from user's test data)
        random.seed(42)
        points = [
            point_cls(random.uniform(0, 400), random.uniform(0, 300))
            for _ in range(1417)
        ]

        hasher = SpatialHash()
        for p in points:
            hasher.get_or_add(p)

        n = len(points)
        naive_comparisons = n * (n - 1) // 2

        assert len(hasher) == n, "distinct points must not be deduplicated away"

        # A linear scan would average n/2 comparisons per insert. See
        # MAX_COMPARISONS_PER_INSERT for the bound's headroom and rationale.
        assert counter["comparisons"] < MAX_COMPARISONS_PER_INSERT * n, (
            f"Spatial hash made {counter['comparisons']} comparisons for {n} points "
            f"({counter['comparisons'] / n:.1f} per insert), above the "
            f"{MAX_COMPARISONS_PER_INSERT}/insert complexity-regression bound. "
            f"That is not O(1) per insert; a linear scan would be ~{n // 2}. This is "
            "not a speed regression -- check cell_size against the coordinate range."
        )
        assert counter["comparisons"] < naive_comparisons // 100

    def test_spatial_hash_deduplicates_coincident_points(self):
        """Exercise the collision path the sparse-random case never reaches.

        With 0.1mm cells over 400x300mm, 1,417 random points produce a single
        is_close() call, so the matching logic was untested. This forces it.
        """
        import random

        from app.cam.spatial_hash import SpatialHash

        counter = {"comparisons": 0}
        point_cls = _counting_point_class(counter)

        random.seed(42)
        distinct = [
            point_cls(random.uniform(0, 400), random.uniform(0, 300))
            for _ in range(500)
        ]
        # Each distinct point repeated four times, well inside the 0.001mm
        # tolerance, interleaved so matches are found across the whole run.
        points = []
        for p in distinct:
            points.append(p)
            for _ in range(3):
                points.append(point_cls(p.x + 1e-6, p.y - 1e-6))
        random.shuffle(points)

        hasher = SpatialHash()
        indices = [hasher.get_or_add(p) for p in points]

        assert len(hasher) == len(distinct), (
            f"expected {len(distinct)} unique points, got {len(hasher)}"
        )
        assert len(set(indices)) == len(distinct)
        assert counter["comparisons"] < MAX_COMPARISONS_PER_INSERT * len(points), (
            f"{counter['comparisons']} comparisons for {len(points)} inserts is not "
            "O(1) per insert even with duplicates present"
        )
