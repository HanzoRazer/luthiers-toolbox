# test_badge_generator.py
# Quick test for badge generator (no API required)

import json
import pathlib
import sys

# Create sample test data
reports_dir = pathlib.Path("reports")
reports_dir.mkdir(exist_ok=True)

sample_data = {
    "GRBL": {"bytes": 1247, "segments": 8, "arc_mode": "IJ"},
    "Mach3": {"bytes": 1248, "segments": 8, "arc_mode": "IJ"},
    "Haas": {"bytes": 1203, "segments": 8, "arc_mode": "R"},
    "Marlin": {"bytes": 1249, "segments": 8, "arc_mode": "IJ"}
}

# Save sample data
data_file = reports_dir / "helical_smoke_posts.json"
with open(data_file, "w") as f:
    json.dump(sample_data, f, indent=2)

print(f"✅ Created {data_file}")

# Run badge generator
sys.path.insert(0, "services/api/tools")

try:
    import gen_helical_badge
    print("\n" + "="*50)
    print("Badge generator output:")
    print("="*50)
except ImportError as e:
    print(f"❌ Failed to import badge generator: {e}")
    sys.exit(1)

# Verify badges were created
badges_dir = reports_dir / "badges"
expected_files = [
    "badges.json",
    "GRBL.svg",
    "Mach3.svg",
    "Haas.svg",
    "Marlin.svg"
]

print("\n" + "="*50)
print("Verification:")
print("="*50)

all_exist = True
for filename in expected_files:
    filepath = badges_dir / filename
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"✅ {filename} ({size} bytes)")
    else:
        print(f"❌ {filename} NOT FOUND")
        all_exist = False

if all_exist:
    print("\n🎉 All badges generated successfully!")
    
    # Show badges.json content
    badges_json = badges_dir / "badges.json"
    print(f"\n{badges_json}:")
    print(badges_json.read_text())
    
    sys.exit(0)
else:
    print("\n❌ Some files missing")
    sys.exit(1)
