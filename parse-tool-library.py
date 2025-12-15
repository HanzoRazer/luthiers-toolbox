#!/usr/bin/env python3
"""
Parser for CarveCo/Vectric Tool Library Files
Extracts readable tool information from binary .tdb and .tool files
"""

import re
import struct
import csv
import sys
from pathlib import Path


def extract_strings(data, min_length=3):
    """Extract printable ASCII strings from binary data"""
    # Look for sequences of printable ASCII characters
    pattern = b'[\x20-\x7e]{' + str(min_length).encode() + b',}'
    strings = re.findall(pattern, data)
    return [s.decode('ascii', errors='ignore') for s in strings]


def parse_tool_markers(data):
    """Find tool type markers in the binary data"""
    tool_types = [
        b'tpmDB_VBitTool',
        b'tpmDB_BallnoseTool',
        b'tpmDB_SlotDrillTool',
        b'tpmDB_FlatConicalTool',
        b'tpmDB_RadiusedConicalTool',
        b'tpmDB_RadiusedSlotDrillTool',
        b'tpmDB_RadiusedEngravingTool',
        b'mcToolGroupMarker',
        b'mcRadiusedEngravingTool',
        b'ToolGroup',
    ]
    
    tool_entries = []
    
    for tool_type in tool_types:
        pos = 0
        while True:
            pos = data.find(tool_type, pos)
            if pos == -1:
                break
            tool_entries.append({
                'position': pos,
                'type': tool_type.decode('ascii')
            })
            pos += 1
    
    return sorted(tool_entries, key=lambda x: x['position'])


def extract_tool_info(data, start_pos, end_pos):
    """Extract tool information from a section of binary data"""
    section = data[start_pos:end_pos]
    
    # Extract all readable strings from this section
    strings = extract_strings(section, min_length=5)
    
    # Filter out common non-tool strings
    ignore_patterns = ['tpmDB_', 'mcTool', 'utParameter']
    strings = [s for s in strings if not any(p in s for p in ignore_patterns)]
    
    # Try to find tool name (usually the longest string or contains specific keywords)
    tool_name = ""
    tool_notes = ""
    url = ""
    
    for s in strings:
        if 'http' in s.lower():
            url = s
        elif len(s) > len(tool_name) and any(c.isalnum() for c in s):
            if 'Shank' in s or 'Bit' in s or 'Tool' in s or 'Router' in s or '#' in s or 'mm' in s or 'Deg' in s:
                tool_name = s
        elif 'note' in s.lower() or 'comment' in s.lower():
            tool_notes = s
    
    # Try to extract numeric values (dimensions, speeds, feeds)
    # Look for floating point numbers in the binary data
    numbers = []
    try:
        for i in range(0, len(section) - 8, 1):
            try:
                # Try to unpack as double (8 bytes)
                val = struct.unpack('<d', section[i:i+8])[0]
                if 0.01 < abs(val) < 10000 and not (val > 1e10 or val < -1e10):
                    numbers.append(round(val, 4))
            except:
                pass
    except:
        pass
    
    return {
        'name': tool_name,
        'notes': tool_notes,
        'url': url,
        'strings': strings[:5],  # Keep first 5 strings for reference
        'numbers': numbers[:10] if numbers else []  # Keep first 10 numbers
    }


def parse_tool_file(filepath):
    """Parse a tool library file and extract all tools"""
    print(f"\nParsing: {filepath}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find all tool markers
    tool_markers = parse_tool_markers(data)
    
    if not tool_markers:
        print("  No tool markers found!")
        return []
    
    print(f"  Found {len(tool_markers)} tool markers")
    
    tools = []
    
    # Process each tool section
    for i, marker in enumerate(tool_markers):
        # Determine section end (next marker or end of file)
        start_pos = marker['position']
        end_pos = tool_markers[i + 1]['position'] if i + 1 < len(tool_markers) else len(data)
        
        # Skip if section is too small
        if end_pos - start_pos < 20:
            continue
        
        tool_info = extract_tool_info(data, start_pos, end_pos)
        tool_info['type'] = marker['type']
        
        # Only add if we found a name
        if tool_info['name']:
            tools.append(tool_info)
    
    print(f"  Extracted {len(tools)} tools")
    return tools


def write_csv(tools, output_file):
    """Write extracted tools to CSV"""
    if not tools:
        print(f"No tools to write to {output_file}")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'Tool Type',
            'Tool Name',
            'Notes',
            'URL',
            'Additional Info',
            'Numeric Values'
        ])
        
        # Write tool data
        for tool in tools:
            writer.writerow([
                tool.get('type', ''),
                tool.get('name', ''),
                tool.get('notes', ''),
                tool.get('url', ''),
                ' | '.join(tool.get('strings', [])[:3]),
                ', '.join(str(n) for n in tool.get('numbers', [])[:5])
            ])
    
    print(f"  ✓ Created: {output_file}")


def main():
    script_dir = Path(__file__).parent
    
    # Define input/output file mappings
    conversions = [
        {
            "input": script_dir / "Two-Moose-Set-CarveCo-V1.2" / "Two Moose Set-CarveCo-V1.2.txt",
            "output": script_dir / "Two-Moose-Set-CarveCo-V1.2" / "Two Moose Set-CarveCo-V1.2-parsed.csv"
        },
        {
            "input": script_dir / "Bits-Bits-CarveCo-Complete-V1.2" / "Bits Bits CarveCo Complete-V1.2.txt",
            "output": script_dir / "Bits-Bits-CarveCo-Complete-V1.2" / "Bits Bits CarveCo Complete-V1.2-parsed.csv"
        },
        {
            "input": script_dir / "Myers-Woodshop-Set-CarveCo-V1.2" / "Myers Woodshop Set-CarveCo-V1.2.txt",
            "output": script_dir / "Myers-Woodshop-Set-CarveCo-V1.2" / "Myers Woodshop Set-CarveCo-V1.2-parsed.csv"
        },
        {
            "input": script_dir / "Amana-Tool-Vectric.tool.txt",
            "output": script_dir / "Amana-Tool-Vectric.tool-parsed.csv"
        }
    ]
    
    print("=" * 70)
    print("CarveCo/Vectric Tool Library Parser")
    print("=" * 70)
    
    for conversion in conversions:
        input_file = conversion["input"]
        output_file = conversion["output"]
        
        if not input_file.exists():
            print(f"\n✗ File not found: {input_file}")
            continue
        
        # Parse the tool file
        tools = parse_tool_file(input_file)
        
        # Write to CSV
        if tools:
            write_csv(tools, output_file)
        else:
            print(f"  ✗ No tools extracted")
    
    print("\n" + "=" * 70)
    print("Conversion complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
