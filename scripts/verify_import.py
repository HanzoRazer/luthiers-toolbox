import json

with open('services/api/app/data/machines.json') as f:
    data = json.load(f)

for machine in data['machines']:
    if machine['id'] == 'IDC_WOODCRAFT':
        print(f"✓ Machine: {machine['name']}")
        print(f"✓ Total tools: {len(machine['tools'])}")
        print("\nFirst 5 tools:")
        for i, tool in enumerate(machine['tools'][:5], 1):
            rpm = tool.get('spindle_rpm', 0)
            feed = tool.get('feed_mm_min', 0)
            print(f"  {i}. T{tool['t']}: {tool['name']}")
            print(f"      Type: {tool['type']}, Ø{tool['dia_mm']}mm × {tool['len_mm']}mm")
            print(f"      {rpm}RPM, {feed}mm/min")
        
        print(f"\n✓ SUCCESS: {len(machine['tools'])} tools ready for CNC operations!")
        print(f"\nTo use these tools:")
        print(f"  1. Start API server (if not running): uvicorn app.main:app --reload")
        print(f"  2. Access via: GET /api/machines/tools/IDC_WOODCRAFT")
        print(f"  3. In CAM software, reference tools by T number (T1, T2, T3...)")
