#!/usr/bin/env python3
"""Fix all remaining run_artifacts imports to use runs_v2."""
import pathlib
import re

def fix_file(file_path):
    """Fix imports in a single file."""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Replace import statements
    content = content.replace(
        'from app.rmos.run_artifacts.store import query_run_artifacts',
        'from app.rmos.runs_v2.store import query_runs'
    )
    content = content.replace(
        'from app.rmos.run_artifacts.store import read_run_artifact',
        'from app.rmos.runs_v2.store import get_run'
    )
    content = content.replace(
        'from app.rmos.run_artifacts.store import write_run_artifact',
        'from app.rmos.runs_v2.store import persist_run, create_run_id'
    )
    
    # Replace function calls (careful to preserve parameters)
    content = re.sub(r'\bquery_run_artifacts\(', 'query_runs(', content)
    content = re.sub(r'\bread_run_artifact\(', 'get_run(', content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

# Find all Python files
root = pathlib.Path('app')
files_fixed = []

for py_file in root.rglob('*.py'):
    try:
        if fix_file(py_file):
            files_fixed.append(str(py_file))
            print(f"✓ Fixed: {py_file}")
    except Exception as e:
        print(f"✗ Error in {py_file}: {e}")

if files_fixed:
    print(f"\nFixed {len(files_fixed)} file(s)")
else:
    print("\nNo files needed fixing")
