# Vue Component Extraction Analyzer (Enhanced)

A sophisticated analysis tool that identifies template sections in Vue SFCs that could be extracted into child components. Features prop/emit inference, composable detection, and intelligent overlap filtering.

## Quick Start

```bash
# Basic analysis
python scripts/analyze_vue_extraction.py packages/client/src/components/MyComponent.vue

# Recursive directory analysis
python scripts/analyze_vue_extraction.py packages/client/src/components/ --recursive

# JSON output with detailed prop information
python scripts/analyze_vue_extraction.py packages/client/src/components/MyComponent.vue --json --show-details

# Custom thresholds
python scripts/analyze_vue_extraction.py src/components/ --recursive --min-block 20 --min-vif 30
```

## Features

| Feature | Description | CLI Flag |
|---------|-------------|----------|
| **Overlap Filtering** | Shows only leaf candidates (no children) | `--no-overlap-filter` to disable |
| **Prop Inference** | Analyzes template bindings to suggest props | `--no-prop-inference` to disable |
| **Emit Detection** | Finds @event handlers to suggest emits | (included with prop inference) |
| **Composable Detection** | Identifies which composables each section uses | `--no-composable-detection` to disable |
| **v-if Grouping** | Groups related v-if/v-else chains | `--no-vif-grouping` to disable |
| **Complexity Score** | Ranks candidates by extraction difficulty | Always on |

## CLI Options

```bash
# Thresholds
--min-lines 500      # Only analyze files over this LOC (default: 500)
--min-block 15       # Minimum lines for any block (default: 15)
--min-vif 20         # Minimum lines for v-if branch (default: 20)
--min-section 25     # Minimum lines for section div (default: 25)

# Feature toggles
--no-overlap-filter      # Show all candidates, including parents
--no-prop-inference      # Disable prop/emit inference
--no-composable-detection # Disable composable detection
--no-vif-grouping        # Disable v-if chain grouping

# Output
--json               # Output as JSON
--show-details       # Show props/emits/composables in text output
-o, --output-file    # Write to file instead of stdout
-r, --recursive      # Recursively analyze directories
```

## Understanding the Output

### Example Output

```
================================================================================
Vue Extraction Analysis: src/components/SawContourPanel.vue
================================================================================

Lines: 777 total (template: 574, script: 197, style: 0)

WARNINGS:
  [!] File exceeds 500 LOC (777 lines) - decomposition recommended
  [!] Template exceeds 300 lines (574) - extract child components

EXTRACTION CANDIDATES (5 found):

1. [HIGH] (leaf) Lines 95-156 (62 lines)
   Element: <div> | Trigger: v-if
   Condition/Class: contourType === 'arc'
   Suggested name: ArcPanel.vue
   Props: centerX, centerY, radius, startAngle, endAngle
   Emits: input
   Composables: useSawContourPath
   Complexity: 2.4

2. [HIGH] (leaf) Lines 159-196 (38 lines)
   Element: <div> | Trigger: v-if
   Condition/Class: contourType === 'circle'
   Suggested name: CirclePanel.vue
   Props: centerX, centerY, radius
   Emits: input
   Complexity: 1.8

SUMMARY:
  Candidates: 5 (3 high, 2 medium)
  Potential reduction: ~261 lines
  Inferred props: 12
  Inferred emits: 8
  Detected composables: 4
```

### Markers

| Marker | Meaning |
|--------|---------|
| `[HIGH]` | High confidence - large block (30+ lines) with clear boundary |
| `[MED]` | Medium confidence - meets thresholds but may need review |
| `(leaf)` | Leaf candidate - no sub-sections, ready to extract |

### Complexity Score

Calculated as: `1.0 + (props * 0.2) + (emits * 0.3) + (composables * 0.5)`

- Score 1.0-1.5: Simple extraction
- Score 1.5-2.5: Moderate complexity
- Score 2.5+: Complex - consider extracting composable first

## Programmatic Usage

```python
from analyze_vue_extraction import analyze_vue_file
from pathlib import Path

# Configure analysis
config = {
    'min_block_lines': 15,
    'infer_props': True,
    'detect_composables': True,
    'filter_overlapping': True,
}

# Analyze a file
result = analyze_vue_file(Path("MyComponent.vue"), config)

# Access inferred props
for candidate in result.candidates:
    print(f"Section at lines {candidate['start_line']}-{candidate['end_line']}")
    print(f"  Props: {[p['name'] for p in candidate['props']]}")
    print(f"  Emits: {[e['name'] for e in candidate['emits']]}")
    print(f"  Composables: {[c['name'] for c in candidate['composables']]}")
```

## CI Integration

```yaml
# .github/workflows/architecture.yml
- name: Check for extraction candidates
  run: |
    python scripts/analyze_vue_extraction.py src/components/ -r --json --show-details > candidates.json

    # Count high-confidence leaf candidates
    HIGH_LEAF_COUNT=$(jq '[.[].candidates[] | select(.confidence=="HIGH" and .child_candidates == [])] | length' candidates.json)

    if [ "$HIGH_LEAF_COUNT" -gt 5 ]; then
      echo "::warning::$HIGH_LEAF_COUNT high-confidence leaf candidates ready for extraction"
    fi

    # Check for components with high complexity
    HIGH_COMPLEXITY=$(jq '[.[].candidates[] | select(.complexity_score > 3)] | length' candidates.json)

    if [ "$HIGH_COMPLEXITY" -gt 0 ]; then
      echo "::error::$HIGH_COMPLEXITY high-complexity sections need immediate attention"
      exit 1
    fi
```

## Recommended Workflow

1. **Run analysis** on files over 500 LOC
2. **Review HIGH confidence leaf candidates** (marked with 🍃) first
3. **Check inferred props** - these become the component's interface
4. **Extract v-if branches as a group** (note shows chain info)
5. **Start with lowest complexity** candidates
6. **Re-run analysis** after each extraction to see remaining work

## Limitations

1. **Script parsing**: Uses Python AST which doesn't understand TypeScript - composable detection may miss some imports
2. **Prop inference**: Based on template bindings only - doesn't trace data flow
3. **No auto-refactoring**: Analysis only - human makes extraction decisions

## Files

- `scripts/analyze_vue_extraction.py` - Main analyzer script (1140 lines)
- `scripts/README_vue_extraction.md` - This documentation
