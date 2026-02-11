"""Allow running as python -m app.ci.boundary_imports."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
