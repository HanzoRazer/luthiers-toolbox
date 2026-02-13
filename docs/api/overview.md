# API Overview

Luthier's ToolBox provides a RESTful API for programmatic access to all features.

---

## Base URL

```
http://localhost:8000
```

Production deployments will have a different base URL.

---

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Quick Start

### Health Check

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "version": "0.33.0"
}
```

### Calculate String Tension

```bash
curl -X POST http://localhost:8000/api/calculators/string-tension \
  -H "Content-Type: application/json" \
  -d '{
    "scale_length_mm": 648,
    "strings": [
      {"gauge": 0.010, "pitch": "E4", "material": "plain_steel"}
    ]
  }'
```

---

## API Categories

### Calculators (`/api/calculators`)

Mathematical tools for instrument design.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/string-tension` | POST | Calculate string tension |
| `/fret-positions` | POST | Calculate fret positions |
| `/convert` | POST | Unit conversion |
| `/board-feet` | POST | Board feet calculation |
| `/wood-weight` | POST | Wood weight by species |

### CAM (`/api/cam`)

Toolpath generation and G-code.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pocket` | POST | Generate pocket toolpath |
| `/contour` | POST | Generate contour toolpath |
| `/drill` | POST | Generate drilling operations |
| `/preview/{id}` | GET | Preview toolpath |
| `/export/{id}` | GET | Export G-code |

### DXF (`/api/dxf`)

CAD file processing.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload DXF file |
| `/validate/{id}` | GET | Validate geometry |
| `/layers/{id}` | GET | Get layer info |
| `/heal/{id}` | POST | Auto-heal geometry |

### RMOS (`/api/rmos`)

Manufacturing safety and run management.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/runs_v2/runs` | GET | List runs |
| `/runs_v2/runs/{id}` | GET | Get run details |
| `/feasibility/check` | POST | Check feasibility |
| `/runs_v2/runs/{id}/override` | POST | Apply override |

### Art Studio (`/api/art-studio`)

Rosette design and decorative patterns.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rosette` | POST | Generate rosette |
| `/rosette/toolpath` | POST | Rosette toolpath |
| `/sessions` | GET | List design sessions |

### Machines (`/api/machines`)

CNC machine configuration.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profiles` | GET | List machine profiles |
| `/profiles` | POST | Create profile |
| `/profiles/{id}` | PUT | Update profile |
| `/profiles/{id}` | DELETE | Delete profile |

---

## Request Format

### Headers

```
Content-Type: application/json
Accept: application/json
```

### Body

All POST/PUT requests use JSON body:

```json
{
  "parameter1": "value1",
  "parameter2": 123
}
```

---

## Response Format

### Success Response

```json
{
  "status": "ok",
  "data": { ... }
}
```

Or for simple responses:

```json
{
  "result": 42.5
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

---

## Pagination

List endpoints support pagination:

```
GET /api/rmos/runs_v2/runs?limit=20&offset=40
```

Response includes pagination metadata:

```json
{
  "items": [...],
  "total": 100,
  "limit": 20,
  "offset": 40
}
```

---

## Filtering

Many endpoints support query parameters for filtering:

```
GET /api/rmos/runs_v2/runs?risk_level=YELLOW&created_after=2025-01-01
```

---

## Rate Limiting

The API does not currently enforce rate limits. For production deployments, consider implementing rate limiting at the infrastructure level.

---

## CORS

CORS is configured to allow requests from:

- `http://localhost:5173` (default Vue dev server)
- `http://localhost:3000`

Production deployments should configure appropriate origins.

---

## SDK Usage

### Python

```python
import requests

class ToolBoxAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def calculate_tension(self, scale_mm, strings):
        response = self.session.post(
            f"{self.base_url}/api/calculators/string-tension",
            json={"scale_length_mm": scale_mm, "strings": strings}
        )
        response.raise_for_status()
        return response.json()

# Usage
api = ToolBoxAPI()
result = api.calculate_tension(648, [
    {"gauge": 0.010, "pitch": "E4", "material": "plain_steel"}
])
```

### JavaScript/TypeScript

```typescript
const API_BASE = "http://localhost:8000";

async function calculateTension(scaleMm: number, strings: StringSpec[]) {
  const response = await fetch(`${API_BASE}/api/calculators/string-tension`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scale_length_mm: scaleMm, strings }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

---

## Next Steps

- [Authentication](authentication.md) - API authentication (optional)
- [Endpoints](endpoints.md) - Full endpoint reference
