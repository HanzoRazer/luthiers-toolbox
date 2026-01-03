#!/usr/bin/env python3
"""
DXF Fixture Extraction Helper

This script generates workflow patch code that replaces inline DXF content
with fixture file reads. Run this to see the YAML changes needed.

Created: 2025-01-xx (CBSP21 DXF Fixture Extraction)
Target: .github/workflows/blueprint_phase3.yml

Usage:
    python scripts/governance/generate_dxf_fixture_patch.py

Fixtures Created:
    services/api/tests/fixtures/dxf/minimal.dxf
    services/api/tests/fixtures/dxf/contours_rectangle.dxf
"""

import textwrap
from pathlib import Path

# Path constants
FIXTURES_DIR = Path("services/api/tests/fixtures/dxf")
WORKFLOW_FILE = Path(".github/workflows/blueprint_phase3.yml")

# The workflow steps that need refactoring
STEPS_USING_DXF = [
    {
        "name": "Test Phase 3.2 - DXF Preflight (Mock)",
        "fixture": "minimal.dxf",
        "description": "JSON format preflight validation"
    },
    {
        "name": "Test Phase 3.2 - DXF Preflight (HTML)",
        "fixture": "minimal.dxf", 
        "description": "HTML format preflight validation"
    },
    {
        "name": "Test Phase 3.2 - Contour Reconstruction (Mock)",
        "fixture": "contours_rectangle.dxf",
        "description": "Rectangle contour from 4 LINE entities on 'Contours' layer"
    }
]


def generate_fixture_loader_snippet() -> str:
    """Generate Python snippet for loading DXF fixtures in workflow."""
    return textwrap.dedent('''
        # Load DXF fixture instead of inline content
        from pathlib import Path
        FIXTURES_DIR = Path("services/api/tests/fixtures/dxf")
        
        # Read fixture file
        dxf_path = FIXTURES_DIR / "minimal.dxf"  # or "contours_rectangle.dxf"
        dxf_content = dxf_path.read_bytes()
        
        # Use in requests
        files = {'file': ('test.dxf', io.BytesIO(dxf_content), 'application/dxf')}
    ''').strip()


def generate_workflow_step_pattern(fixture_name: str, endpoint_path: str) -> str:
    """Generate a refactored workflow step using fixture file."""
    return textwrap.dedent(f'''
        - name: Test DXF endpoint ({endpoint_path})
          run: |
            python - <<'PYEOF'
            import requests
            import io
            import sys
            from pathlib import Path
            
            FIXTURES_DIR = Path("services/api/tests/fixtures/dxf")
            
            try:
                # Load DXF from fixture (not inline)
                dxf_path = FIXTURES_DIR / "{fixture_name}"
                if not dxf_path.exists():
                    print(f"✗ Fixture not found: {{dxf_path}}")
                    sys.exit(1)
                    
                dxf_content = dxf_path.read_bytes()
                files = {{'file': ('test.dxf', io.BytesIO(dxf_content), 'application/dxf')}}
                
                # ... rest of test logic
                r = requests.post(
                    'http://localhost:8000{endpoint_path}',
                    files=files,
                    data={{...}}
                )
                
                # Assertions...
                
            except Exception as e:
                print(f"✗ Test error: {{e}}")
                sys.exit(1)
            PYEOF
    ''').strip()


def print_refactoring_guide():
    """Print the complete refactoring guide."""
    print("=" * 70)
    print("DXF FIXTURE EXTRACTION - REFACTORING GUIDE")
    print("=" * 70)
    print()
    
    print("📁 FIXTURES CREATED:")
    print("-" * 40)
    for fixture in ["minimal.dxf", "contours_rectangle.dxf"]:
        fixture_path = FIXTURES_DIR / fixture
        print(f"  ✓ {fixture_path}")
    print()
    
    print("📝 FIXTURE CONTENTS:")
    print("-" * 40)
    print()
    print("minimal.dxf:")
    print("  - DXF R12 format (AC1009)")
    print("  - Single LINE entity on layer '0'")
    print("  - From (0,0) to (100,0)")
    print("  - Used for: preflight JSON/HTML tests")
    print()
    print("contours_rectangle.dxf:")
    print("  - DXF R12 format (AC1009)")
    print("  - 4 LINE entities on layer 'Contours'")
    print("  - Forms 50x30 rectangle")
    print("  - Used for: reconstruct-contours test")
    print()
    
    print("🔧 WORKFLOW STEPS TO REFACTOR:")
    print("-" * 40)
    for step in STEPS_USING_DXF:
        print(f"\n  Step: {step['name']}")
        print(f"  Fixture: {step['fixture']}")
        print(f"  Purpose: {step['description']}")
    print()
    
    print("📋 PYTHON FIXTURE LOADER PATTERN:")
    print("-" * 40)
    print()
    print(generate_fixture_loader_snippet())
    print()
    
    print("🔄 REPLACEMENT PATTERN:")
    print("-" * 40)
    print()
    print("BEFORE (inline DXF):")
    print(textwrap.indent('''
dxf_content = b"""0
SECTION
2
HEADER
...
0
EOF"""
'''.strip(), "    "))
    print()
    print("AFTER (fixture read):")
    print(textwrap.indent('''
FIXTURES_DIR = Path("services/api/tests/fixtures/dxf")
dxf_content = (FIXTURES_DIR / "minimal.dxf").read_bytes()
'''.strip(), "    "))
    print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
The inline DXF content in blueprint_phase3.yml has been extracted to:
    
    services/api/tests/fixtures/dxf/minimal.dxf
    services/api/tests/fixtures/dxf/contours_rectangle.dxf

Benefits:
    - Fixtures can be validated independently
    - Real DXF parsers can test against fixture files
    - Workflow YAML is cleaner and more maintainable
    - Fixtures are reusable across multiple tests
    
Next Steps:
    1. Update blueprint_phase3.yml to use fixture reads
    2. Verify checkout action fetches services/api/tests/fixtures/
    3. Run workflow to confirm fixture loading works
    """)


def verify_fixtures_exist():
    """Verify that fixture files exist."""
    missing = []
    for fixture in ["minimal.dxf", "contours_rectangle.dxf"]:
        fixture_path = FIXTURES_DIR / fixture
        if not fixture_path.exists():
            missing.append(fixture_path)
    
    if missing:
        print("⚠️  Missing fixture files:")
        for path in missing:
            print(f"    {path}")
        return False
    return True


if __name__ == "__main__":
    # When run from repo root
    import os
    
    # Try to find fixtures relative to script or repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent  # scripts/governance -> repo root
    
    # Adjust FIXTURES_DIR to absolute path for verification
    fixtures_abs = repo_root / FIXTURES_DIR
    
    if fixtures_abs.exists():
        print(f"✓ Fixtures directory exists: {fixtures_abs}")
        for f in fixtures_abs.glob("*.dxf"):
            print(f"  ✓ Found: {f.name}")
    
    print()
    print_refactoring_guide()
