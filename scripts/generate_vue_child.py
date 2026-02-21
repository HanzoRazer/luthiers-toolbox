#!/usr/bin/env python3
"""
Vue Child Component Generator

Generates boilerplate for extracted child components based on
the extraction patterns documented in VUE_DECOMPOSITION_GUIDE.md.

Usage:
    python scripts/generate_vue_child.py --parent src/MyComponent.vue --name ChildName --lines 50-120
    python scripts/generate_vue_child.py --parent src/MyComponent.vue --name ChildName --lines 50-120 --css-modules
    python scripts/generate_vue_child.py --parent src/MyComponent.vue --name ChildName --lines 50-120 --output-dir src/my_component/

Author: Claude Code
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def parse_line_range(line_range: str) -> Tuple[int, int]:
    """Parse a line range like '50-120' into (start, end)."""
    if '-' not in line_range:
        raise ValueError(f"Invalid line range: {line_range}. Use format: START-END")

    parts = line_range.split('-')
    return int(parts[0]), int(parts[1])


def extract_section(content: str, start_line: int, end_line: int) -> str:
    """Extract lines from content."""
    lines = content.split('\n')
    # Line numbers are 1-indexed
    return '\n'.join(lines[start_line - 1:end_line])


def find_bindings(template_section: str) -> Dict[str, List[str]]:
    """Find Vue bindings in template section."""
    bindings = {
        'props': set(),
        'emits': set(),
        'mustache': set(),
    }

    # Mustache bindings {{ foo }}
    for match in re.finditer(r'\{\{\s*([^}\s|]+)', template_section):
        binding = match.group(1).strip()
        if binding and not binding.startswith('$'):
            bindings['mustache'].add(binding)

    # Prop bindings :prop="value"
    for match in re.finditer(r':([\w-]+)="\s*([^"]+)\s*"', template_section):
        prop_name = match.group(1)
        value = match.group(2).strip()
        if value and not value.startswith('$'):
            bindings['props'].add(value)

    # v-model bindings v-model="value" or v-model:prop="value"
    for match in re.finditer(r'v-model(?::([\w-]+))?="\s*([^"]+)\s*"', template_section):
        value = match.group(2).strip()
        if value:
            bindings['props'].add(value)
            # v-model implies emit
            prop_part = match.group(1) or 'modelValue'
            bindings['emits'].add(f'update:{prop_part}')

    # Event bindings @event="handler"
    for match in re.finditer(r'@([\w-]+)(?:\.[\w]+)*="\s*([^"]+)\s*"', template_section):
        event_name = match.group(1)
        handler = match.group(2).strip()
        # Emit pattern: @click="emit('foo')" or just @click="doSomething"
        if 'emit' in handler:
            emit_match = re.search(r"emit\(['\"]([^'\"]+)['\"]", handler)
            if emit_match:
                bindings['emits'].add(emit_match.group(1))
        else:
            # This is a method call that parent should handle
            bindings['emits'].add(event_name)

    return {k: list(v) for k, v in bindings.items()}


def infer_prop_type(prop_name: str, template_section: str) -> str:
    """Infer TypeScript type for a prop based on usage."""
    prop_escaped = re.escape(prop_name)

    # Check for array methods
    if re.search(rf'{prop_escaped}\s*\.(?:length|map|filter|forEach|find)', template_section):
        return 'unknown[]'

    # Check for object access
    if re.search(rf'{prop_escaped}\s*\.\w+', template_section):
        return 'Record<string, unknown>'

    # Check for boolean comparison
    if re.search(rf'{prop_escaped}\s*===?\s*(?:true|false)', template_section):
        return 'boolean'

    # Check for number operations
    if re.search(rf'{prop_escaped}\s*[+\-*/]', template_section):
        return 'number'

    # Check for string interpolation
    if re.search(rf'\{{\{{\s*{prop_escaped}\s*\}}\}}', template_section):
        return 'string | number'

    return 'unknown'


def generate_props_interface(bindings: Dict[str, List[str]], template_section: str, use_css_modules: bool) -> str:
    """Generate TypeScript props interface."""
    props = []

    if use_css_modules:
        props.append("  styles: Record<string, string>")

    seen = set()
    for prop in sorted(bindings['props'] + bindings['mustache']):
        # Clean up prop name
        prop_clean = prop.split('.')[0].split('[')[0].strip()
        if not prop_clean or prop_clean in seen:
            continue
        seen.add(prop_clean)

        prop_type = infer_prop_type(prop_clean, template_section)
        props.append(f"  {prop_clean}: {prop_type}")

    if not props:
        return "defineProps<{}>()"

    return "defineProps<{\n" + "\n".join(props) + "\n}>()"


def generate_emits_interface(bindings: Dict[str, List[str]]) -> str:
    """Generate TypeScript emits interface."""
    if not bindings['emits']:
        return ""

    emits = []
    for emit in sorted(bindings['emits']):
        # Guess param type based on emit name
        if emit.startswith('update:'):
            emits.append(f"  '{emit}': [value: unknown]")
        else:
            emits.append(f"  '{emit}': []")

    return "const emit = defineEmits<{\n" + "\n".join(emits) + "\n}>()"


def generate_child_component(
    name: str,
    template_section: str,
    use_css_modules: bool = False,
) -> str:
    """Generate complete child component code."""

    bindings = find_bindings(template_section)
    props_code = generate_props_interface(bindings, template_section, use_css_modules)
    emits_code = generate_emits_interface(bindings)

    # Build script section
    script_parts = [props_code]
    if emits_code:
        script_parts.append(emits_code)

    script_content = "\n\n".join(script_parts)

    component = f'''<template>
{template_section}
</template>

<script setup lang="ts">
{script_content}
</script>
'''

    return component


def main():
    parser = argparse.ArgumentParser(
        description='Generate Vue child component boilerplate from parent extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --parent src/MyComponent.vue --name ToolSetup --lines 50-120
  %(prog)s --parent src/MyComponent.vue --name ToolSetup --lines 50-120 --css-modules
  %(prog)s --parent src/MyComponent.vue --name ToolSetup --lines 50-120 --output-dir src/my_component/

The generated component includes:
  - Template section from specified lines
  - Inferred props from bindings
  - Inferred emits from event handlers
  - CSS Modules support (optional)
        """
    )

    parser.add_argument('--parent', '-p', required=True, type=Path,
                        help='Path to parent Vue component')
    parser.add_argument('--name', '-n', required=True,
                        help='Name for the child component (PascalCase)')
    parser.add_argument('--lines', '-l', required=True,
                        help='Line range to extract (e.g., 50-120)')
    parser.add_argument('--css-modules', action='store_true',
                        help='Add styles prop for CSS Modules')
    parser.add_argument('--output-dir', '-o', type=Path,
                        help='Output directory (default: same as parent)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print generated code without writing')

    args = parser.parse_args()

    # Validate parent exists
    if not args.parent.exists():
        print(f"Error: Parent file not found: {args.parent}", file=sys.stderr)
        sys.exit(1)

    # Parse line range
    try:
        start_line, end_line = parse_line_range(args.lines)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Read parent content
    content = args.parent.read_text(encoding='utf-8')

    # Extract template section
    template_section = extract_section(content, start_line, end_line)

    # Generate child component
    child_code = generate_child_component(
        name=args.name,
        template_section=template_section,
        use_css_modules=args.css_modules,
    )

    # Determine output path
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = args.parent.parent

    output_path = output_dir / f"{args.name}.vue"

    if args.dry_run:
        print(f"# Would write to: {output_path}")
        print(f"# Lines {start_line}-{end_line} from {args.parent}")
        print()
        print(child_code)
    else:
        # Create directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path.write_text(child_code, encoding='utf-8')
        print(f"Generated: {output_path}")
        print(f"  Lines: {start_line}-{end_line} ({end_line - start_line + 1} lines)")
        print()
        print("Next steps:")
        print(f"  1. Review and fix types in {output_path}")
        print(f"  2. Import in parent: import {args.name} from './{output_dir.name}/{args.name}.vue'")
        print(f"  3. Replace extracted section with <{args.name} ... />")
        print(f"  4. Run: npm run type-check")


if __name__ == '__main__':
    main()
