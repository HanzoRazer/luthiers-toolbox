import os
import subprocess
import sys

# Ensure ANTHROPIC_API_KEY is set in your environment
if not os.getenv('ANTHROPIC_API_KEY'):
    print("Error: ANTHROPIC_API_KEY environment variable not set")
    sys.exit(1)

result = subprocess.run(
    [sys.executable, 'agent.py', '--spec', 'specs/production_shop.json', '--out', './output/production_shop'],
    cwd=os.path.dirname(os.path.abspath(__file__))
)
sys.exit(result.returncode)
