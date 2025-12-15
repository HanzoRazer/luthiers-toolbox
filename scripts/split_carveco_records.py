"""
Carveco CSV Record Splitter
Splits single-line Carveco CSV files into proper rows by record markers
"""
import sys
import re
from pathlib import Path

def split_carveco_records(input_file: str, output_file: str = None):
    """
    Split Carveco CSV records into separate lines
    
    Args:
        input_file: Path to single-line cleaned CSV
        output_file: Path to save split CSV (optional)
    """
    input_path = Path(input_file)
    
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_split{input_path.suffix}"
    
    print(f"Reading: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✓ Read {len(content):,} characters")
    
    # Find record markers
    markers = ['tpmDBGroupStart', 'tpmDBGroupEnd', 'tpmDBSlotDrillTool', 
               'tpmDBBallnoseTool', 'tpmDBFlatConicalTool', 'tpmDBRadiusedConicalTool',
               'tpmDBVBitTool', 'mcToolGroupMarker', 'mcToolGroup']
    
    # Split by any marker
    pattern = '(' + '|'.join(markers) + ')'
    parts = re.split(pattern, content)
    
    # Recombine marker with its data
    lines = []
    i = 0
    while i < len(parts):
        if parts[i] in markers and i + 1 < len(parts):
            line = parts[i] + parts[i + 1]
            lines.append(line.strip())
            i += 2
        elif parts[i].strip():
            lines.append(parts[i].strip())
            i += 1
        else:
            i += 1
    
    # Remove empty lines
    lines = [line for line in lines if line and len(line) > 10]
    
    print(f"✓ Split into {len(lines)} records")
    
    # Write split file
    print(f"Writing: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        for line in lines:
            f.write(line + '\n')
    
    print(f"✓ Split CSV saved to: {output_file}")
    print(f"\nFirst 5 records:")
    for i, line in enumerate(lines[:5]):
        preview = line[:80] + '...' if len(line) > 80 else line
        print(f"  {i+1}: {preview}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_carveco_records.py <input_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    split_carveco_records(input_file, output_file)
