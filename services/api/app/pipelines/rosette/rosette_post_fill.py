"""
Rosette G-code Template Filler
Migrated from: server/pipelines/rosette/rosette_post_fill.py
Status: Medium Priority Pipeline

Fills G-code templates with rosette-specific parameters.
Replaces placeholder variables like {{TOOL_MM}}, {{FEED}}, etc.

Dependencies: None (pure Python)
"""
import re
from typing import Dict, Any


# Default parameter values
DEFAULT_PARAMS = {
    'TOOL_MM': 3.0,
    'FEED': 600,
    'RPM': 18000,
    'STEPDOWN': 0.5,
    'TOTAL_DEPTH': 1.5,
    'SAFE_Z': 5.0,
    'INNER_R': 40.0,
    'OUTER_R': 50.0,
    'SOUNDHOLE_R': 50.0,
    'CHANNEL_WIDTH': 10.0,
}


def fill_template(template: str, params: Dict[str, Any]) -> str:
    """
    Fill G-code template with parameter values.
    
    Args:
        template: G-code template string with {{PARAM}} placeholders
        params: Dictionary of parameter values
    
    Returns:
        Filled template string
    
    Supported placeholders:
        {{TOOL_MM}} - Tool diameter in mm
        {{FEED}} - Feed rate mm/min
        {{RPM}} - Spindle speed
        {{STEPDOWN}} - Depth per pass mm
        {{TOTAL_DEPTH}} - Final depth mm
        {{SAFE_Z}} - Safe retract height mm
        {{INNER_R}} - Inner channel radius mm
        {{OUTER_R}} - Outer channel radius mm
        {{SOUNDHOLE_R}} - Soundhole radius mm
        {{CHANNEL_WIDTH}} - Calculated channel width mm
    """
    # Merge with defaults
    merged = {**DEFAULT_PARAMS, **params}
    
    # Calculate derived values
    if 'INNER_R' in merged and 'OUTER_R' in merged:
        merged['CHANNEL_WIDTH'] = merged['OUTER_R'] - merged['INNER_R']
    
    # Replace all placeholders
    result = template
    for key, value in merged.items():
        placeholder = f"{{{{{key}}}}}"  # {{KEY}}
        if isinstance(value, float):
            replacement = f"{value:.3f}"
        else:
            replacement = str(value)
        result = result.replace(placeholder, replacement)
    
    # Warn about unfilled placeholders
    remaining = re.findall(r'\{\{(\w+)\}\}', result)
    if remaining:
        print(f"Warning: Unfilled placeholders: {remaining}")
    
    return result


def list_placeholders(template: str) -> list:
    """Extract list of placeholder names from template."""
    return re.findall(r'\{\{(\w+)\}\}', template)


# CLI entry point
if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python rosette_post_fill.py <template.nc> [params.json]")
        print("\nSupported placeholders:")
        for key, default in DEFAULT_PARAMS.items():
            print(f"  {{{{{key}}}}} - default: {default}")
        sys.exit(1)
    
    template_path = sys.argv[1]
    params_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load template
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Load params
    params = {}
    if params_path:
        with open(params_path, 'r') as f:
            params = json.load(f)
    
    # Fill and output
    result = fill_template(template, params)
    print(result)
