#!/usr/bin/env python3
"""
One-shot Duplicate Code Scanner for luthiers-toolbox
Finds duplicate functions/classes via normalized AST hashing
"""

import ast
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class DuplicationDetector:
    """Detect code duplication across repository"""

    def __init__(self, min_lines: int = 8):
        self.min_lines = min_lines
        self.hash_map: Dict[str, List[dict]] = defaultdict(list)
        self.stats = {"files_scanned": 0, "blocks_analyzed": 0, "parse_errors": 0}

    def detect_duplicates(self, repo_path: str) -> List[Dict]:
        """Find duplicate code blocks"""
        repo = Path(repo_path)

        # Scan Python files
        for python_file in repo.rglob('*.py'):
            # Skip non-source directories
            rel_str = str(python_file.relative_to(repo))
            if any(skip in rel_str for skip in [
                'venv', '__pycache__', '.git', 'node_modules',
                'site-packages', '.eggs', 'build', 'dist'
            ]):
                continue

            self.stats["files_scanned"] += 1
            self._analyze_file(python_file, repo)

        # Find duplicates (same hash appears multiple times)
        duplicates = []
        for code_hash, instances in self.hash_map.items():
            if len(instances) > 1:
                # Calculate total duplicated lines
                total_lines = sum(i['lines'] for i in instances)
                duplicates.append({
                    'hash': code_hash[:12],
                    'instances': instances,
                    'count': len(instances),
                    'total_duplicated_lines': total_lines,
                    'wasted_lines': total_lines - instances[0]['lines'],  # All but one are waste
                    'suggested_refactoring': self._suggest_refactoring(instances)
                })

        # Sort by wasted lines (highest impact first)
        duplicates.sort(key=lambda x: x['wasted_lines'], reverse=True)

        return duplicates

    def _analyze_file(self, python_file: Path, repo: Path):
        """Analyze single file for duplicates"""
        try:
            content = python_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            lines = content.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._process_block(node, python_file, repo, lines, 'function')
                elif isinstance(node, ast.ClassDef):
                    # Only hash small classes (methods are hashed separately)
                    if hasattr(node, 'end_lineno'):
                        class_lines = node.end_lineno - node.lineno
                        if class_lines < 50:  # Small classes only
                            self._process_block(node, python_file, repo, lines, 'class')

        except SyntaxError:
            self.stats["parse_errors"] += 1
        except UnicodeDecodeError:
            self.stats["parse_errors"] += 1
        except Exception as e:
            self.stats["parse_errors"] += 1

    def _process_block(self, node: ast.AST, python_file: Path, repo: Path,
                       lines: List[str], block_type: str):
        """Process a code block for duplicate detection"""
        if not hasattr(node, 'end_lineno'):
            return

        line_count = node.end_lineno - node.lineno
        if line_count < self.min_lines:
            return

        self.stats["blocks_analyzed"] += 1

        # Extract code lines
        code_lines = lines[node.lineno - 1:node.end_lineno]
        code = '\n'.join(code_lines)

        # Normalize for comparison
        normalized = self._normalize_code(code)

        # Skip trivial blocks (mostly whitespace/docstrings after normalization)
        if len(normalized) < 50:
            return

        # Hash normalized code
        code_hash = hashlib.md5(normalized.encode()).hexdigest()

        self.hash_map[code_hash].append({
            'file': str(python_file.relative_to(repo)),
            'name': node.name,
            'type': block_type,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'lines': line_count
        })

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison"""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)

        # Remove docstrings (triple quotes)
        code = re.sub(r'"""[\s\S]*?"""', '""', code)
        code = re.sub(r"'''[\s\S]*?'''", "''", code)

        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)

        # Remove string contents (keep structure)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)

        return code.strip()

    def _suggest_refactoring(self, instances: List[Dict]) -> str:
        """Suggest refactoring for duplicate code"""
        count = len(instances)
        files = set(i['file'] for i in instances)

        if len(files) == 1:
            return "Consolidate within same file (extract helper)"
        elif count > 3:
            return "Extract to shared utility module"
        elif all('router' in f for f in files):
            return "Extract to router_utils or base router class"
        elif all('test' in f for f in files):
            return "Extract to test fixtures/conftest.py"
        else:
            return "Consider shared module or base class"


def main():
    repo_path = Path(__file__).parent.parent
    print(f"Scanning: {repo_path}")
    print("=" * 70)

    detector = DuplicationDetector(min_lines=8)
    duplicates = detector.detect_duplicates(str(repo_path))

    # Print stats
    print(f"\nScan Statistics:")
    print(f"  Files scanned: {detector.stats['files_scanned']}")
    print(f"  Blocks analyzed: {detector.stats['blocks_analyzed']}")
    print(f"  Parse errors: {detector.stats['parse_errors']}")
    print(f"  Duplicate clusters found: {len(duplicates)}")

    if not duplicates:
        print("\nNo significant duplicates found!")
        return 0

    # Calculate totals
    total_wasted = sum(d['wasted_lines'] for d in duplicates)
    print(f"  Total wasted lines: {total_wasted}")

    print("\n" + "=" * 70)
    print("TOP DUPLICATE CLUSTERS (by wasted lines)")
    print("=" * 70)

    # Show top 25 duplicates
    for i, dup in enumerate(duplicates[:25], 1):
        print(f"\n#{i} — {dup['wasted_lines']} wasted lines ({dup['count']} copies)")
        print(f"    Hash: {dup['hash']}")
        print(f"    Suggestion: {dup['suggested_refactoring']}")
        print(f"    Instances:")
        for inst in dup['instances']:
            print(f"      - {inst['file']}:{inst['line_start']}-{inst['line_end']} "
                  f"({inst['type']} {inst['name']}, {inst['lines']} lines)")

    # Summary by directory
    print("\n" + "=" * 70)
    print("DUPLICATES BY DIRECTORY")
    print("=" * 70)

    dir_stats = defaultdict(lambda: {"count": 0, "wasted": 0})
    for dup in duplicates:
        for inst in dup['instances']:
            parts = inst['file'].split('/')
            if len(parts) > 2:
                dir_key = '/'.join(parts[:3])
            else:
                dir_key = parts[0] if parts else 'root'
            dir_stats[dir_key]["count"] += 1
            dir_stats[dir_key]["wasted"] += inst['lines'] // dup['count']  # Proportional

    sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]["wasted"], reverse=True)
    for dir_path, stats in sorted_dirs[:15]:
        print(f"  {dir_path}: {stats['count']} instances, ~{stats['wasted']} lines")

    # Quick wins (small duplicates, easy to fix)
    print("\n" + "=" * 70)
    print("QUICK WINS (2 copies, <20 lines each)")
    print("=" * 70)

    quick_wins = [d for d in duplicates if d['count'] == 2 and d['instances'][0]['lines'] < 20]
    for dup in quick_wins[:10]:
        inst = dup['instances'][0]
        print(f"  {inst['name']} ({inst['lines']} lines): {dup['instances'][0]['file']} ↔ {dup['instances'][1]['file']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
