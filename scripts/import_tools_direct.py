"""
Import tool library directly into machines.json

Bypasses the API and directly merges tools into the machine profile.
Faster for bulk imports and doesn't require API restart.

Usage:
  python scripts/import_tools_direct.py
"""
import csv
import json
import os

MACHINES_FILE = "services/api/app/data/machines.json"
TOOLS_CSV = "IDC-Woodcraft-Vectric-Tools-MACHINE.csv"
MACHINE_ID = "IDC_WOODCRAFT"


def import_tools():
    """Import tools from CSV directly into machines.json"""
    
    # Load machines.json
    if not os.path.exists(MACHINES_FILE):
        print(f"❌ Machines file not found: {MACHINES_FILE}")
        print("   Run: python scripts/setup_machine_with_tools.py first")
        return
    
    with open(MACHINES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Find target machine
    machine = None
    for m in data.get("machines", []):
        if m.get("id") == MACHINE_ID:
            machine = m
            break
    
    if not machine:
        print(f"❌ Machine not found: {MACHINE_ID}")
        print(f"   Available machines: {[m.get('id') for m in data.get('machines', [])]}")
        return
    
    # Load tools from CSV
    if not os.path.exists(TOOLS_CSV):
        print(f"❌ Tools CSV not found: {TOOLS_CSV}")
        print("   Run: python scripts/convert_vtdb_to_machine_tools.py first")
        return
    
    with open(TOOLS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tools = []
        skipped = 0
        
        for row in reader:
            try:
                # Convert and validate required fields
                tool = {
                    "t": int(row["t"]),
                    "name": row["name"],
                    "type": row.get("type", "EM"),
                    "dia_mm": float(row["dia_mm"]),
                    "len_mm": float(row["len_mm"]),
                }
                
                # Optional fields (only add if not empty)
                if row.get("holder") and row["holder"].strip():
                    tool["holder"] = row["holder"]
                if row.get("offset_len_mm") and row["offset_len_mm"].strip():
                    tool["offset_len_mm"] = float(row["offset_len_mm"])
                if row.get("spindle_rpm") and row["spindle_rpm"].strip():
                    tool["spindle_rpm"] = float(row["spindle_rpm"])
                if row.get("feed_mm_min") and row["feed_mm_min"].strip():
                    tool["feed_mm_min"] = float(row["feed_mm_min"])
                if row.get("plunge_mm_min") and row["plunge_mm_min"].strip():
                    tool["plunge_mm_min"] = float(row["plunge_mm_min"])
                
                tools.append(tool)
            except Exception as e:
                skipped += 1
                continue
    
    print(f"✓ Loaded {len(tools)} tools from CSV ({skipped} skipped)")
    
    # Merge tools (upsert by T number)
    existing = {int(t.get("t")): t for t in machine.get("tools", [])}
    for tool in tools:
        existing[int(tool["t"])] = tool
    
    # Sort by T number and save
    machine["tools"] = [existing[k] for k in sorted(existing.keys())]
    
    with open(MACHINES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Imported {len(tools)} tools into machine '{MACHINE_ID}'")
    print(f"✓ Total tools in machine: {len(machine['tools'])}")
    print()
    print("Sample tools:")
    for i, tool in enumerate(machine["tools"][:5], start=1):
        rpm = tool.get("spindle_rpm", 0)
        print(f"  {i}: T{tool['t']} - {tool['name']} ({tool['type']}) - Ø{tool['dia_mm']}mm, {rpm}RPM")
    
    print()
    print("✓ Import complete! Tools are now available via API:")
    print(f"   GET http://localhost:8000/api/machines/tools/{MACHINE_ID}")


if __name__ == "__main__":
    import_tools()
