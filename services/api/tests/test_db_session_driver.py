"""Dependency contract tests for the synchronous production database session."""

import os
from pathlib import Path
import subprocess
import sys


API_ROOT = Path(__file__).resolve().parents[1]


def test_production_psycopg_url_imports_session_without_connecting():
    """The production SQLAlchemy URL has its selected psycopg v3 driver."""
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg://user:pass@localhost:5432/testdb"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.db.session import engine; "
                "assert engine.dialect.driver == 'psycopg'"
            ),
        ],
        cwd=API_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
