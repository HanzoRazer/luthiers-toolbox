import os
import pytest

from app.governance.shadow_stats import reset, write_shadow_stats_json


@pytest.fixture(scope="session", autouse=True)
def _shadow_stats_write_after_tests(tmp_path_factory):
    """
    Ensures ENDPOINT_STATS_PATH is always written at the end of the test session.

    Non-breaking:
    - If nothing recorded, it still writes 0 counts (valid input for budget gate).
    - Keeps stats file isolated per CI run.
    """
    stats_dir = tmp_path_factory.mktemp("endpoint_shadow_stats")
    stats_path = stats_dir / "endpoint_shadow_stats.json"

    os.environ["ENDPOINT_STATS_PATH"] = str(stats_path)

    # Clean slate for deterministic tests
    reset()

    yield

    # Always write a stats file so the budget gate CLI can run.
    write_shadow_stats_json(str(stats_path))
