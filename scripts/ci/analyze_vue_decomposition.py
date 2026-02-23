#!/usr/bin/env python3
"""
Vue Component Decomposition Analyzer

Analyzes Vue SFC files to identify decomposition opportunities based on:
1. LOC violations (template, script, style sections)
2. Extractable template sections (v-if blocks, panels, button groups)
3. Composable candidates (related refs, functions)
4. Repeated patterns

Usage:
    python scripts/ci/analyze_vue_decomposition.py [path]
    python scripts/ci/analyze_vue_decomposition.py --json
    python scripts/ci/analyze_vue_decomposition.py --fix-suggestions

Respects DECOMPOSITION_GUIDELINES.md limits:
- Orchestrator: 400 LOC max
- Child component: 200 LOC max
- Composable: 150 LOC max
"""

import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


# LOC Limits from DECOMPOSITION_GUIDELINES.md
ORCHESTRATOR_LIMIT = 400
CHILD_LIMIT = 200
COMPOSABLE_LIMIT = 150
STYLE_WARNING_THRESHOLD = 150  # Warn if styles are large


@dataclass
class Section:
    """A section of a Vue SFC."""
    name: str
    start_line: int
    end_line: int
    content: str

    @property
    def loc(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass
class ExtractionCandidate:
    """A candidate for extraction into a child component or composable."""
    type: str  # 'component', 'composable', 'shared-style'
    name_suggestion: str
    reason: str
    start_line: int
    end_line: int
    confidence: str  # 'high', 'medium', 'low'
    snippet: str = ""
    estimated_loc: int = 0


@dataclass
class VueFileAnalysis:
    """Complete analysis of a Vue file."""
    file_path: str
    total_loc: int
    template_loc: int
    script_loc: int
    style_loc: int
    exceeds_limit: bool
    limit_type: str  # 'orchestrator' or 'child'
    extraction_candidates: List[ExtractionCandidate] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def reduction_needed(self) -> int:
        limit = ORCHESTRATOR_LIMIT if self.limit_type == 'orchestrator' else CHILD_LIMIT
        return max(0, self.total_loc - limit)


def parse_vue_sfc(content: str) -> Dict[str, Section]:
    """Parse a Vue SFC into template, script, and style sections."""
    sections = {}

    # Match template section
    template_match = re.search(
        r'^<template[^>]*>\s*\n(.*?)\n</template>',
        content, re.MULTILINE | re.DOTALL
    )
    if template_match:
        start = content[:template_match.start()].count('\n') + 1
        end = content[:template_match.end()].count('\n') + 1
        sections['template'] = Section('template', start, end, template_match.group(1))

    # Match script section
    script_match = re.search(
        r'^<script[^>]*>\s*\n(.*?)\n</script>',
        content, re.MULTILINE | re.DOTALL
    )
    if script_match:
        start = content[:script_match.start()].count('\n') + 1
        end = content[:script_match.end()].count('\n') + 1
        sections['script'] = Section('script', start, end, script_match.group(1))

    # Match style section
    style_match = re.search(
        r'^<style[^>]*>\s*\n(.*?)\n</style>',
        content, re.MULTILINE | re.DOTALL
    )
    if style_match:
        start = content[:style_match.start()].count('\n') + 1
        end = content[:style_match.end()].count('\n') + 1
        sections['style'] = Section('style', start, end, style_match.group(1))

    return sections


def find_vif_blocks(template_content: str, base_line: int) -> List[ExtractionCandidate]:
    """Find v-if/v-else blocks that could be extracted."""
    candidates = []

    # Find v-if blocks with substantial content
    vif_pattern = re.compile(
        r'<(\w+)[^>]*\s+v-if="([^"]+)"[^>]*>(.*?)</\1>',
        re.DOTALL
    )

    for match in vif_pattern.finditer(template_content):
        tag, condition, inner = match.groups()
        inner_lines = inner.strip().count('\n') + 1

        if inner_lines >= 10:  # Only suggest if block is substantial
            start_line = base_line + template_content[:match.start()].count('\n')
            end_line = start_line + inner.count('\n')

            # Generate component name from condition
            name = condition.split('.')[0].split('?')[0].strip()
            name = re.sub(r'[^a-zA-Z0-9]', '', name.title())
            if not name:
                name = f"{tag.title()}Block"

            candidates.append(ExtractionCandidate(
                type='component',
                name_suggestion=f"{name}Panel.vue",
                reason=f"v-if block with {inner_lines} lines could be separate component",
                start_line=start_line,
                end_line=end_line,
                confidence='high' if inner_lines >= 20 else 'medium',
                estimated_loc=inner_lines + 30  # Add boilerplate estimate
            ))

    return candidates


def find_panel_sections(template_content: str, base_line: int) -> List[ExtractionCandidate]:
    """Find distinct panel/section divs that could be extracted."""
    candidates = []

    # Common panel class patterns
    panel_patterns = [
        r'class="([^"]*(?:panel|section|card|box|container|wrapper|block)[^"]*)"',
        r'class="([^"]*(?:wf-|form-|result-|preview-)[^"]*)"',
    ]

    for pattern in panel_patterns:
        for match in re.finditer(pattern, template_content):
            class_name = match.group(1)

            # Find the containing element
            # Look backwards for the opening tag
            before = template_content[:match.start()]
            tag_match = re.search(r'<(\w+)[^>]*$', before)
            if not tag_match:
                continue

            tag = tag_match.group(1)
            tag_start = before.rfind(f'<{tag}')

            # Find closing tag
            close_pattern = f'</{tag}>'
            remaining = template_content[match.end():]

            # Simple nesting counter
            depth = 1
            pos = 0
            tag_end = None
            while depth > 0 and pos < len(remaining):
                open_match = re.search(f'<{tag}[^>]*>', remaining[pos:])
                close_match = re.search(f'</{tag}>', remaining[pos:])

                if close_match is None:
                    break

                if open_match and open_match.start() < close_match.start():
                    depth += 1
                    pos += open_match.end()
                else:
                    depth -= 1
                    if depth == 0:
                        tag_end = match.end() + pos + close_match.end()
                        break
                    pos += close_match.end()

            if tag_end is None:
                continue

            section_content = template_content[tag_start:tag_end]
            section_lines = section_content.count('\n') + 1

            if section_lines >= 15:  # Only suggest substantial sections
                start_line = base_line + template_content[:tag_start].count('\n')

                # Generate name from class
                name_parts = re.findall(r'[a-zA-Z][a-zA-Z0-9]*', class_name)
                name = ''.join(p.title() for p in name_parts[:3])
                if not name:
                    name = "Section"

                candidates.append(ExtractionCandidate(
                    type='component',
                    name_suggestion=f"{name}.vue",
                    reason=f"Panel section '{class_name}' with {section_lines} lines",
                    start_line=start_line,
                    end_line=start_line + section_lines,
                    confidence='medium',
                    estimated_loc=section_lines + 30
                ))

    # Deduplicate overlapping candidates
    candidates.sort(key=lambda c: (c.start_line, -c.estimated_loc))
    deduped = []
    last_end = 0
    for c in candidates:
        if c.start_line >= last_end:
            deduped.append(c)
            last_end = c.end_line

    return deduped


def find_button_groups(template_content: str, base_line: int) -> List[ExtractionCandidate]:
    """Find repeated button groups that could be shared components."""
    candidates = []

    # Find groups of 3+ buttons
    button_group_pattern = re.compile(
        r'(<button[^>]*>.*?</button>\s*){3,}',
        re.DOTALL
    )

    for match in button_group_pattern.finditer(template_content):
        group = match.group(0)
        button_count = group.count('<button')
        group_lines = group.count('\n') + 1

        if group_lines >= 10:
            start_line = base_line + template_content[:match.start()].count('\n')

            candidates.append(ExtractionCandidate(
                type='component',
                name_suggestion="ButtonGroup.vue",
                reason=f"Group of {button_count} buttons ({group_lines} lines)",
                start_line=start_line,
                end_line=start_line + group_lines,
                confidence='medium' if button_count >= 5 else 'low',
                estimated_loc=group_lines + 40
            ))

    return candidates


def find_composable_candidates(script_content: str, base_line: int) -> List[ExtractionCandidate]:
    """Find groups of related refs/functions that could be composables."""
    candidates = []

    # Find ref declarations
    ref_pattern = re.compile(r'const\s+(\w+)\s*=\s*ref[<(]')
    refs = [(m.group(1), m.start()) for m in ref_pattern.finditer(script_content)]

    # Find reactive declarations
    reactive_pattern = re.compile(r'const\s+(\w+)\s*=\s*reactive[<(]')
    refs.extend((m.group(1), m.start()) for m in reactive_pattern.finditer(script_content))

    # Find function declarations
    func_pattern = re.compile(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|:))')
    funcs = []
    for m in func_pattern.finditer(script_content):
        name = m.group(1) or m.group(2)
        if name and not name.startswith('use'):  # Skip existing composables
            funcs.append((name, m.start()))

    # Group by prefix (e.g., handleX, onX, fetchX)
    prefixes = defaultdict(list)
    for name, pos in refs + funcs:
        # Extract prefix
        prefix_match = re.match(r'^([a-z]+)[A-Z]', name)
        if prefix_match:
            prefixes[prefix_match.group(1)].append((name, pos))
        else:
            # Group by first word
            words = re.findall(r'[A-Z]?[a-z]+', name)
            if words:
                prefixes[words[0].lower()].append((name, pos))

    # Suggest composables for groups of 3+ related items
    for prefix, items in prefixes.items():
        if len(items) >= 3 and prefix not in ('get', 'set', 'is', 'has', 'on'):
            names = [name for name, _ in items]
            start_pos = min(pos for _, pos in items)
            start_line = base_line + script_content[:start_pos].count('\n')

            candidates.append(ExtractionCandidate(
                type='composable',
                name_suggestion=f"use{prefix.title()}.ts",
                reason=f"Related state/functions: {', '.join(names[:5])}{'...' if len(names) > 5 else ''}",
                start_line=start_line,
                end_line=start_line + 10,  # Approximate
                confidence='high' if len(items) >= 5 else 'medium',
                estimated_loc=len(items) * 10  # Rough estimate
            ))

    return candidates


def find_duplicate_styles(style_content: str, base_line: int) -> List[ExtractionCandidate]:
    """Find styles that might be candidates for shared CSS."""
    candidates = []

    # Common utility patterns that should be shared
    shared_patterns = [
        (r'\.btn\s*\{', 'buttons.css', 'Button styles'),
        (r'\.card\s*\{', 'cards.css', 'Card styles'),
        (r'\.panel\s*\{', 'panels.css', 'Panel styles'),
        (r'\.form-', 'forms.css', 'Form styles'),
        (r'\.badge\s*\{', 'badges.css', 'Badge styles'),
        (r'\.modal\s*\{', 'modals.css', 'Modal styles'),
    ]

    for pattern, file_name, reason in shared_patterns:
        if re.search(pattern, style_content):
            candidates.append(ExtractionCandidate(
                type='shared-style',
                name_suggestion=f"@/styles/shared/{file_name}",
                reason=f"{reason} could be shared across components",
                start_line=base_line,
                end_line=base_line,
                confidence='low',
                estimated_loc=0
            ))

    return candidates


def analyze_vue_file(file_path: Path) -> Optional[VueFileAnalysis]:
    """Analyze a single Vue file for decomposition opportunities."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return None

    total_loc = content.count('\n') + 1
    sections = parse_vue_sfc(content)

    template_loc = sections.get('template', Section('', 0, 0, '')).loc if 'template' in sections else 0
    script_loc = sections.get('script', Section('', 0, 0, '')).loc if 'script' in sections else 0
    style_loc = sections.get('style', Section('', 0, 0, '')).loc if 'style' in sections else 0

    # Determine if this is an orchestrator or child based on name/path
    name = file_path.stem
    is_orchestrator = (
        'View' in name or
        'Page' in name or
        'Panel' in name or
        'Dashboard' in name or
        'Lab' in name
    )
    limit_type = 'orchestrator' if is_orchestrator else 'child'
    limit = ORCHESTRATOR_LIMIT if is_orchestrator else CHILD_LIMIT

    exceeds_limit = total_loc > limit

    analysis = VueFileAnalysis(
        file_path=str(file_path),
        total_loc=total_loc,
        template_loc=template_loc,
        script_loc=script_loc,
        style_loc=style_loc,
        exceeds_limit=exceeds_limit,
        limit_type=limit_type,
    )

    # Only find extraction candidates if file exceeds limits
    if exceeds_limit:
        # Analyze template
        if 'template' in sections:
            template = sections['template']
            analysis.extraction_candidates.extend(
                find_vif_blocks(template.content, template.start_line)
            )
            analysis.extraction_candidates.extend(
                find_panel_sections(template.content, template.start_line)
            )
            analysis.extraction_candidates.extend(
                find_button_groups(template.content, template.start_line)
            )

        # Analyze script
        if 'script' in sections:
            script = sections['script']
            analysis.extraction_candidates.extend(
                find_composable_candidates(script.content, script.start_line)
            )

        # Analyze styles
        if 'style' in sections:
            style = sections['style']
            analysis.extraction_candidates.extend(
                find_duplicate_styles(style.content, style.start_line)
            )

    # Add warnings
    if style_loc > STYLE_WARNING_THRESHOLD:
        analysis.warnings.append(
            f"Large style section ({style_loc} lines) - consider extracting to shared CSS"
        )

    if template_loc > 200:
        analysis.warnings.append(
            f"Large template ({template_loc} lines) - consider extracting sections"
        )

    return analysis


def scan_directory(root: Path, pattern: str = "**/*.vue") -> List[VueFileAnalysis]:
    """Scan a directory for Vue files and analyze them."""
    analyses = []

    for vue_file in root.glob(pattern):
        # Skip node_modules and other common excludes
        if 'node_modules' in vue_file.parts:
            continue
        if '.nuxt' in vue_file.parts:
            continue

        analysis = analyze_vue_file(vue_file)
        if analysis:
            analyses.append(analysis)

    return analyses


def print_report(analyses: List[VueFileAnalysis], verbose: bool = False):
    """Print a human-readable decomposition report."""
    # Sort by LOC descending
    analyses.sort(key=lambda a: a.total_loc, reverse=True)

    violations = [a for a in analyses if a.exceeds_limit]

    print("=" * 70)
    print("Vue Component Decomposition Analysis")
    print("=" * 70)
    print()
    print(f"Total files scanned: {len(analyses)}")
    print(f"Files exceeding limits: {len(violations)}")
    print()

    if not violations:
        print("All components are within LOC guidelines.")
        return

    print("Files Requiring Decomposition:")
    print("-" * 70)

    for analysis in violations:
        file_name = Path(analysis.file_path).name
        limit = ORCHESTRATOR_LIMIT if analysis.limit_type == 'orchestrator' else CHILD_LIMIT

        print(f"\n{file_name}")
        print(f"  LOC: {analysis.total_loc} (limit: {limit}, over by {analysis.reduction_needed})")
        print(f"  Breakdown: template={analysis.template_loc}, script={analysis.script_loc}, style={analysis.style_loc}")
        print(f"  Type: {analysis.limit_type}")

        if analysis.warnings:
            print("  Warnings:")
            for warning in analysis.warnings:
                print(f"    - {warning}")

        if analysis.extraction_candidates:
            print("  Extraction Candidates:")

            # Group by type
            by_type = defaultdict(list)
            for c in analysis.extraction_candidates:
                by_type[c.type].append(c)

            for type_name, candidates in by_type.items():
                # Sort by confidence
                candidates.sort(key=lambda c: {'high': 0, 'medium': 1, 'low': 2}[c.confidence])

                print(f"    {type_name.upper()}S:")
                for c in candidates[:5]:  # Limit to top 5 per type
                    conf_icon = {'high': '[H]', 'medium': '[M]', 'low': '[L]'}[c.confidence]
                    print(f"      {conf_icon} {c.name_suggestion}")
                    print(f"          {c.reason}")
                    if c.estimated_loc:
                        print(f"          Est. {c.estimated_loc} LOC")

                if len(candidates) > 5:
                    print(f"      ... and {len(candidates) - 5} more")

    print()
    print("=" * 70)
    print("Recommendations:")
    print("-" * 70)
    print("1. Start with HIGH confidence candidates")
    print("2. Extract largest sections first for maximum LOC reduction")
    print("3. Group related extractions (e.g., panel + its composable)")
    print("4. Run type-check after each extraction")
    print("=" * 70)


def print_json(analyses: List[VueFileAnalysis]):
    """Print JSON output."""
    violations = [a for a in analyses if a.exceeds_limit]

    output = {
        "total_files": len(analyses),
        "violations": len(violations),
        "files": [
            {
                "file": a.file_path,
                "total_loc": a.total_loc,
                "template_loc": a.template_loc,
                "script_loc": a.script_loc,
                "style_loc": a.style_loc,
                "limit_type": a.limit_type,
                "reduction_needed": a.reduction_needed,
                "extraction_candidates": [asdict(c) for c in a.extraction_candidates],
                "warnings": a.warnings,
            }
            for a in violations
        ]
    }

    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Vue components for decomposition opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python analyze_vue_decomposition.py src/components
    python analyze_vue_decomposition.py --json > report.json
    python analyze_vue_decomposition.py src/views/MyView.vue
        """
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (directory or single .vue file)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all files, not just violations"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=ORCHESTRATOR_LIMIT,
        help=f"Override orchestrator LOC limit (default: {ORCHESTRATOR_LIMIT})"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file() and path.suffix == '.vue':
        # Single file analysis
        analysis = analyze_vue_file(path)
        if analysis:
            analyses = [analysis]
        else:
            print(f"Error: Could not analyze {path}", file=sys.stderr)
            sys.exit(1)
    elif path.is_dir():
        # Directory scan
        analyses = scan_directory(path)
    else:
        print(f"Error: {path} is not a valid file or directory", file=sys.stderr)
        sys.exit(1)

    if not analyses:
        print("No Vue files found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print_json(analyses)
    else:
        print_report(analyses, verbose=args.verbose)

    # Exit with error if violations found
    violations = [a for a in analyses if a.exceeds_limit]
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
