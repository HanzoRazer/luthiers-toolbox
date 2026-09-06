import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "artifacts" / "tools"
sys.path.insert(0, str(TOOLS))
