#!/usr/bin/env python3
"""
Phantom Import Auditor & Cleaner

Analyzes main.py for phantom imports (try-import blocks referencing non-existent files)
and optionally removes them.

Usage:
    python scripts/audit_phantom_imports.py           # Audit only
    python scripts/audit_phantom_imports.py --clean   # Audit and clean
    python scripts/audit_phantom_imports.py --dry-run # Show what would be removed

Created: December 11, 2025
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Path configuration
REPO_ROOT = Path(__file__).parent.parent
API_APP_DIR = REPO_ROOT / "services" / "api" / "app"
MAIN_PY = API_APP_DIR / "main.py"


def find_phantom_imports(content: str) -> List[Tuple[str, str, str, int, int]]:
    """
    Find all try-import blocks that reference non-existent files.
    
    Returns list of (module_path, alias, file_path, start_line, end_line)
    """
    # Pattern matches:
    # try:
    #     from .module.path import thing as alias
    # except ...:
    #     ...
    #     alias = None
    
    pattern = r'''try:\s*
    from\s+([^\s]+)\s+import\s+[^\s]+\s+as\s+([^\s\n]+)\s*
except[^:]*:\s*
    [^\n]*\n\s*
    \2\s*=\s*None'''
    
    phantoms = []
    
    # Simpler approach: find all imports and check files
    import_pattern = r'from\s+([^\s]+)\s+import\s+[^\s]+\s+as\s+([^\s\n]+)'
    
    for match in re.finditer(import_pattern, content):
        module_path = match.group(1)
        alias = match.group(2)
        
        # Convert module path to file path
        # .routers.health_router -> routers/health_router.py
        file_path = module_path.lstrip('.').replace('.', '/') + '.py'
        full_path = API_APP_DIR / file_path
        
        # Also check for package __init__.py
        init_path = API_APP_DIR / module_path.lstrip('.').replace('.', '/') / '__init__.py'
        
        if not full_path.exists() and not init_path.exists():
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            phantoms.append((module_path, alias, file_path, line_num, line_num))
    
    return phantoms


def find_try_blocks_for_phantoms(content: str, phantoms: List[Tuple]) -> List[Tuple[int, int, str]]:
    """
    Find the full try-except blocks containing phantom imports.
    
    Returns list of (start_idx, end_idx, block_text)
    """
    phantom_aliases = {p[1] for p in phantoms}
    
    # Pattern for full try-except block
    pattern = r'(try:\s*\n\s*from[^\n]+as\s+(\w+)[^\n]*\nexcept[^:]*:[^\n]*\n(?:\s+[^\n]*\n)*?\s+\2\s*=\s*None\n?)'
    
    blocks = []
    for match in re.finditer(pattern, content):
        alias = match.group(2)
        if alias in phantom_aliases:
            blocks.append((match.start(), match.end(), match.group(1)))
    
    return blocks


def remove_phantom_blocks(content: str, blocks: List[Tuple[int, int, str]]) -> str:
    """Remove phantom import blocks from content."""
    # Sort blocks by start position, reverse order (so we don't mess up indices)
    sorted_blocks = sorted(blocks, key=lambda x: x[0], reverse=True)
    
    result = content
    for start, end, _ in sorted_blocks:
        result = result[:start] + result[end:]
    
    # Clean up multiple blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def find_include_router_for_phantoms(content: str, phantoms: List[Tuple]) -> List[Tuple[int, int, str]]:
    """
    Find include_router calls for phantom routers.
    
    Returns list of (start_idx, end_idx, line_text)
    """
    phantom_aliases = {p[1] for p in phantoms}
    
    # Pattern: if alias:\n    app.include_router(alias...)
    pattern = r'if\s+(\w+):\s*\n\s*app\.include_router\(\1[^\)]*\)[^\n]*\n?'
    
    blocks = []
    for match in re.finditer(pattern, content):
        alias = match.group(1)
        if alias in phantom_aliases:
            blocks.append((match.start(), match.end(), match.group(0)))
    
    return blocks


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit and clean phantom imports from main.py")
    parser.add_argument("--clean", action="store_true", help="Remove phantom imports")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without changing files")
    args = parser.parse_args()
    
    if not MAIN_PY.exists():
        print(f"ERROR: {MAIN_PY} not found")
        sys.exit(1)
    
    content = MAIN_PY.read_text()
    
    # Find phantoms
    phantoms = find_phantom_imports(content)
    
    print("=" * 70)
    print("PHANTOM IMPORT AUDIT")
    print("=" * 70)
    print(f"File: {MAIN_PY}")
    print(f"Found: {len(phantoms)} phantom imports")
    print()
    
    if not phantoms:
        print("✅ No phantom imports found!")
        return
    
    # Group by category
    rmos_phantoms = [p for p in phantoms if 'rmos' in p[0].lower()]
    art_phantoms = [p for p in phantoms if 'art' in p[0].lower()]
    cam_phantoms = [p for p in phantoms if 'cam' in p[0].lower()]
    other_phantoms = [p for p in phantoms if p not in rmos_phantoms + art_phantoms + cam_phantoms]
    
    print(f"RMOS subsystem: {len(rmos_phantoms)}")
    print(f"Art Studio: {len(art_phantoms)}")
    print(f"CAM: {len(cam_phantoms)}")
    print(f"Other: {len(other_phantoms)}")
    print()
    
    print("PHANTOM IMPORTS:")
    print("-" * 70)
    for module, alias, file_path, line, _ in sorted(phantoms, key=lambda x: x[0]):
        print(f"  Line {line:4d}: {alias:40s} <- {module}")
    print()
    
    if args.clean or args.dry_run:
        # Find blocks to remove
        import_blocks = find_try_blocks_for_phantoms(content, phantoms)
        router_blocks = find_include_router_for_phantoms(content, phantoms)
        
        print(f"Try-except blocks to remove: {len(import_blocks)}")
        print(f"include_router calls to remove: {len(router_blocks)}")
        print()
        
        if args.dry_run:
            print("DRY RUN - Would remove these blocks:")
            print("-" * 70)
            for _, _, block in import_blocks[:5]:
                print(block[:100] + "..." if len(block) > 100 else block)
                print()
            if len(import_blocks) > 5:
                print(f"... and {len(import_blocks) - 5} more")
        else:
            # Actually clean
            new_content = content
            all_blocks = import_blocks + router_blocks
            new_content = remove_phantom_blocks(new_content, all_blocks)
            
            # Backup original
            backup_path = MAIN_PY.with_suffix('.py.bak')
            MAIN_PY.rename(backup_path)
            print(f"Backup saved to: {backup_path}")
            
            # Write cleaned version
            MAIN_PY.write_text(new_content)
            
            original_lines = len(content.splitlines())
            new_lines = len(new_content.splitlines())
            
            print(f"✅ Cleaned main.py")
            print(f"   Original: {original_lines} lines")
            print(f"   Cleaned:  {new_lines} lines")
            print(f"   Removed:  {original_lines - new_lines} lines")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
