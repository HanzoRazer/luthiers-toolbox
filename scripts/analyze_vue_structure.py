#!/usr/bin/env python3
"""
Vue Component Structure Analyzer

Identifies:
1. Potential duplicates (same filename in different locations)
2. Scattered file groups (related files in different directories)
3. Large files without accompanying composables
4. Naming convention violations

Usage:
    python scripts/analyze_vue_structure.py [--json] [--fix-suggestions]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def extract_naming_prefix(name: str) -> str:
    """Extract the semantic prefix from a component name (e.g., 'ArtStudio' from 'ArtStudioInlay')."""
    # Remove common suffixes first
    clean = re.sub(r'(V\d+|Panel|View|Modal|Card|List|Item|Button|Row|Cell)$', '', name)
    # Split on camelCase boundaries
    parts = re.findall(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)', clean)
    if len(parts) >= 2:
        # Check if second part is a common modifier
        if parts[1] in ['Studio', 'Lab', 'Pipeline', 'Pattern', 'Preset', 'Risk', 'Decision']:
            return parts[0] + parts[1]
        return parts[0]
    return parts[0] if parts else name


def analyze_vue_structure(root_path: Path):
    """Analyze Vue component structure and return findings."""

    findings = {
        'duplicates': [],
        'scattered_groups': [],
        'large_without_composables': [],
        'suggested_moves': []
    }

    # Find all Vue files with line counts
    vue_files = []
    for f in root_path.rglob('*.vue'):
        try:
            lines = len(f.read_text(encoding='utf-8').splitlines())
            vue_files.append({'path': f, 'lines': lines, 'name': f.stem})
        except Exception:
            pass

    # 1. Find duplicates
    by_name = defaultdict(list)
    for item in vue_files:
        by_name[item['path'].name].append(item)

    for name, items in by_name.items():
        if len(items) > 1:
            findings['duplicates'].append({
                'filename': name,
                'locations': [
                    {'path': str(i['path'].relative_to(root_path)), 'lines': i['lines']}
                    for i in items
                ]
            })

    # 2. Find scattered groups
    by_prefix = defaultdict(list)
    for item in vue_files:
        prefix = extract_naming_prefix(item['name'])
        by_prefix[prefix].append(item)

    for prefix, items in by_prefix.items():
        if len(items) >= 3:
            dirs = set(str(i['path'].parent.relative_to(root_path)) for i in items)
            if len(dirs) > 1:
                findings['scattered_groups'].append({
                    'prefix': prefix,
                    'count': len(items),
                    'directories': sorted(dirs),
                    'files': [
                        {'path': str(i['path'].relative_to(root_path)), 'lines': i['lines']}
                        for i in sorted(items, key=lambda x: str(x['path']))
                    ]
                })

    # 3. Find large files without composables
    for item in sorted(vue_files, key=lambda x: -x['lines']):
        if item['lines'] > 300:
            parent = item['path'].parent
            has_composables = (parent / 'composables').exists()

            # Check if in a dedicated directory
            dir_name = parent.name.lower().replace('_', '')
            file_stem = item['name'].lower().replace('v2', '').replace('panel', '').replace('view', '').replace('_', '')
            in_dedicated_dir = dir_name == file_stem

            if not has_composables and not in_dedicated_dir:
                findings['large_without_composables'].append({
                    'path': str(item['path'].relative_to(root_path)),
                    'lines': item['lines'],
                    'name': item['name']
                })

    # 4. Generate suggested moves
    # Files in root components/ that should be in subdirectories
    components_root = root_path / 'components'
    if components_root.exists():
        for f in components_root.glob('*.vue'):
            name = f.stem
            prefix = extract_naming_prefix(name)
            # Check if there's already a subdirectory with this prefix
            potential_dirs = [
                d for d in components_root.iterdir()
                if d.is_dir() and prefix.lower() in d.name.lower()
            ]
            if potential_dirs:
                suggested_dir = potential_dirs[0].name
                findings['suggested_moves'].append({
                    'file': f.name,
                    'current': str(f.relative_to(root_path)),
                    'suggested': f'components/{suggested_dir}/{f.name}',
                    'reason': f'Matches prefix "{prefix}" with existing directory'
                })

    return findings


def print_report(findings: dict, show_suggestions: bool = False):
    """Print a human-readable report."""

    print("=" * 70)
    print("VUE COMPONENT STRUCTURE ANALYSIS")
    print("=" * 70)

    # Duplicates
    if findings['duplicates']:
        print("\n## POTENTIAL DUPLICATES")
        print("Files with the same name in different locations:\n")
        for dup in findings['duplicates']:
            print(f"  {dup['filename']}:")
            for loc in dup['locations']:
                print(f"    - {loc['path']} ({loc['lines']} LOC)")
            print()

    # Scattered groups
    if findings['scattered_groups']:
        print("\n## SCATTERED FILE GROUPS")
        print("Related files spread across multiple directories:\n")
        for group in sorted(findings['scattered_groups'], key=lambda x: -x['count']):
            print(f"  {group['prefix']} ({group['count']} files across {len(group['directories'])} directories):")
            for f in group['files'][:5]:  # Show first 5
                print(f"    - {f['path']}")
            if len(group['files']) > 5:
                print(f"    ... and {len(group['files']) - 5} more")
            print()

    # Large files without composables
    if findings['large_without_composables']:
        print("\n## LARGE FILES WITHOUT COMPOSABLES")
        print("Files >300 LOC that may benefit from decomposition:\n")
        for f in findings['large_without_composables'][:20]:  # Top 20
            print(f"  {f['lines']:4d} LOC  {f['path']}")
        if len(findings['large_without_composables']) > 20:
            print(f"\n  ... and {len(findings['large_without_composables']) - 20} more")

    # Suggested moves
    if show_suggestions and findings['suggested_moves']:
        print("\n## SUGGESTED MOVES")
        print("Files that could be moved to existing subdirectories:\n")
        for move in findings['suggested_moves']:
            print(f"  {move['file']}:")
            print(f"    Current:   {move['current']}")
            print(f"    Suggested: {move['suggested']}")
            print(f"    Reason:    {move['reason']}")
            print()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Duplicate filenames:      {len(findings['duplicates'])}")
    print(f"  Scattered file groups:    {len(findings['scattered_groups'])}")
    print(f"  Large files (no composables): {len(findings['large_without_composables'])}")
    print(f"  Suggested moves:          {len(findings['suggested_moves'])}")


def main():
    parser = argparse.ArgumentParser(description='Analyze Vue component structure')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--fix-suggestions', action='store_true', help='Show suggested file moves')
    parser.add_argument('--root', type=str, default='packages/client/src', help='Root directory to analyze')
    args = parser.parse_args()

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    root_path = repo_root / args.root

    if not root_path.exists():
        print(f"Error: {root_path} does not exist", file=sys.stderr)
        sys.exit(1)

    findings = analyze_vue_structure(root_path)

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print_report(findings, show_suggestions=args.fix_suggestions)


if __name__ == '__main__':
    main()
