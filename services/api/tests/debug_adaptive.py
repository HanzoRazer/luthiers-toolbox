from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)
response = client.post('/cam/pocket/adaptive/plan', json={
    'loops': [{'pts': [[0,0], [100,0], [100,60], [0,60]]}],
    'units': 'mm',
    'tool_d': 6.0,
    'stepover': 0.45,
    'stepdown': 1.5,
    'margin': 0.5,
    'strategy': 'Spiral',
    'climb': True,
    'feed_xy': 1200,
    'safe_z': 5,
    'z_rough': -1.5
})
print(f'Status: {response.status_code}')
data = response.json()
print(f'Response keys: {list(data.keys())}')
if 'stats' in data:
    print(f'Stats keys: {list(data["stats"].keys())}')
print('\nFull response:')
print(json.dumps(data, indent=2)[:1000])
