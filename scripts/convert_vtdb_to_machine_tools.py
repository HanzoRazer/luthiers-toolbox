"""
Convert Vectric .vtdb export to Machine Tools CSV format

Transforms the full tool database export (IDC-Woodcraft-Vectric-Tools-FULL.csv)
into the format required by /api/machines/tools/{machine_id}/import

Input columns (from export_vtdb_full.py):
  tool_name, tool_type, diameter, flute_length, num_flutes, included_angle,
  flat_diameter, tip_radius, spindle_speed, feed_rate, plunge_rate,
  stepdown, stepover, tool_number, cutting_notes, material, machine,
  machine_make, machine_model

Output columns (for API import):
  t, name, type, dia_mm, len_mm, holder, offset_len_mm,
  spindle_rpm, feed_mm_min, plunge_mm_min

Usage:
  python scripts/convert_vtdb_to_machine_tools.py

Output:
  IDC-Woodcraft-Vectric-Tools-MACHINE.csv (ready for API import)
"""
import csv
import os

INPUT_FILE = "IDC-Woodcraft-Vectric-Tools-FULL.csv"
OUTPUT_FILE = "IDC-Woodcraft-Vectric-Tools-MACHINE.csv"


def convert_tool_type(vectric_type: str) -> str:
    """Map Vectric tool types to standard CAM types"""
    type_map = {
        # Common types
        "End Mill": "EM",
        "Ball Nose": "BALL",
        "V-Bit": "VBIT",
        "Chamfer": "CHAMFER",
        "Drill": "DRILL",
        "Taper": "TAPER",
        "Engraving": "ENGRAVE",
        "Tapered Ball Nose": "TAPERBALL",
        
        # Specialty types
        "Bowl": "BALL",
        "Core Box": "COREBOX",
        "Round Nose": "BALL",
        "Spot Drill": "DRILL",
        "Center Drill": "DRILL",
    }
    
    # Try exact match first
    if vectric_type in type_map:
        return type_map[vectric_type]
    
    # Try partial match (case-insensitive)
    vt_lower = vectric_type.lower()
    for key, value in type_map.items():
        if key.lower() in vt_lower:
            return value
    
    # Default fallback
    return "EM"


def safe_float(value, default=0.0):
    """Convert value to float, return default if empty/invalid"""
    if not value or value == "None" or value.strip() == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Convert value to int, return default if empty/invalid"""
    if not value or value == "None" or value.strip() == "":
        return default
    try:
        return int(float(value))  # Handle "1.0" → 1
    except (ValueError, TypeError):
        return default


def convert_csv():
    """Convert Vectric FULL export to Machine Tools import format"""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        print(f"   Run: python scripts/export_vtdb_full.py first")
        return
    
    # Read input CSV
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print(f"❌ No data found in {INPUT_FILE}")
        return
    
    print(f"✓ Loaded {len(rows)} tools from {INPUT_FILE}")
    
    # Convert each row
    converted = []
    for idx, row in enumerate(rows, start=1):
        # Extract and convert fields
        tool_name = row.get("tool_name", f"Tool {idx}")
        tool_type = row.get("tool_type", "End Mill")
        diameter = safe_float(row.get("diameter"), 6.0)
        flute_length = safe_float(row.get("flute_length"), 25.0)
        spindle_speed = safe_int(row.get("spindle_speed"), 12000)
        feed_rate = safe_float(row.get("feed_rate"), 1000.0)
        plunge_rate = safe_float(row.get("plunge_rate"), 500.0)
        tool_number = safe_int(row.get("tool_number"), idx)
        
        # Build output row
        converted.append({
            "t": tool_number or idx,  # Use tool_number if available, else sequential
            "name": tool_name,
            "type": convert_tool_type(tool_type),
            "dia_mm": diameter,
            "len_mm": flute_length,
            "holder": "",  # Not in Vectric export, leave blank
            "offset_len_mm": "",  # Not in Vectric export, leave blank
            "spindle_rpm": spindle_speed,
            "feed_mm_min": feed_rate,
            "plunge_mm_min": plunge_rate,
        })
    
    # Write output CSV
    fieldnames = [
        "t", "name", "type", "dia_mm", "len_mm", "holder",
        "offset_len_mm", "spindle_rpm", "feed_mm_min", "plunge_mm_min"
    ]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(converted)
    
    print(f"✓ Converted {len(converted)} tools to {OUTPUT_FILE}")
    print()
    print("Sample converted tools:")
    for i, tool in enumerate(converted[:5], start=1):
        print(f"  {i}: T{tool['t']} - {tool['name']} ({tool['type']}) - Ø{tool['dia_mm']}mm, {tool['spindle_rpm']}RPM")
    
    print()
    print("Next steps:")
    print("  1. Review the converted CSV to verify tool numbers and types")
    print("  2. Import to your machine using:")
    print(f"     POST /api/machines/tools/{{machine_id}}/import")
    print(f"     (Upload {OUTPUT_FILE})")
    print()
    print("  Or use curl:")
    print(f"     curl -X POST http://localhost:8000/api/machines/tools/YOUR_MACHINE_ID/import \\")
    print(f"          -F 'file=@{OUTPUT_FILE}'")


if __name__ == "__main__":
    convert_csv()
