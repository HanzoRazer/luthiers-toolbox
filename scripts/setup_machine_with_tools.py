"""
Setup machine and import tool library in one step

Creates a machine profile in machines.json and imports the converted
Vectric tool library.

Usage:
  python scripts/setup_machine_with_tools.py
"""
import json
import os

MACHINES_FILE = "services/api/app/data/machines.json"
TOOLS_CSV = "IDC-Woodcraft-Vectric-Tools-MACHINE.csv"


def setup_machine():
    """Create a machine profile and prepare for tool import"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(MACHINES_FILE), exist_ok=True)
    
    # Create machine profile
    machine = {
        "id": "IDC_WOODCRAFT",
        "name": "IDC Woodcraft CNC Router",
        "max_feed_xy": 2000.0,
        "rapid": 4000.0,
        "accel": 600.0,
        "jerk": 1800.0,
        "safe_z_default": 5.0,
        "tools": []  # Will be populated via CSV import
    }
    
    # Load existing machines or create new structure
    try:
        with open(MACHINES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"machines": []}
    
    # Add machine if not exists
    existing_ids = [m.get("id") for m in data.get("machines", [])]
    if machine["id"] not in existing_ids:
        data["machines"].append(machine)
        print(f"✓ Created machine: {machine['id']} - {machine['name']}")
    else:
        print(f"✓ Machine already exists: {machine['id']}")
    
    # Save machines.json
    with open(MACHINES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to {MACHINES_FILE}")
    print()
    print("Next steps:")
    print("  1. Restart the API server to load the new machine")
    print("  2. Import tools using:")
    print(f"     curl -X POST http://localhost:8000/api/machines/tools/{machine['id']}/import_csv \\")
    print(f"          -F 'file=@{TOOLS_CSV}'")
    print()
    print("  3. Or via Python:")
    print(f"     import requests")
    print(f"     with open('{TOOLS_CSV}', 'rb') as f:")
    print(f"         r = requests.post('http://localhost:8000/api/machines/tools/{machine['id']}/import_csv',")
    print(f"                           files={{'file': f}})")
    print(f"         print(r.json())")


if __name__ == "__main__":
    setup_machine()
