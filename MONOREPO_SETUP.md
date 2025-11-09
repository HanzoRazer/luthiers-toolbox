# Luthier's Tool Box - Monorepo Setup

## 🎉 What's New

This repository now includes a **monorepo architecture** with:

- **`services/api/`** - FastAPI backend with G-code simulation, tool library, and feeds/speeds
- **`packages/client/`** - Vue 3 client (placeholder for future integration)
- **`packages/shared/`** - Shared TypeScript types (OpenAPI SDK target)
- **CI/CD workflows** - Automated testing and SDK generation

## 📁 Structure

```
Luthiers ToolBox/
├── .env.example                    # Environment variables template
├── pnpm-workspace.yaml             # Monorepo workspace configuration
├── services/
│   └── api/                        # FastAPI backend service
│       ├── requirements.txt        # Python dependencies
│       ├── app/
│       │   ├── main.py             # FastAPI app entry point
│       │   ├── routers/
│       │   │   ├── sim_validate.py # G-code simulator with arc support
│       │   │   ├── cam_sim_router.py # /cam endpoints
│       │   │   └── feeds_router.py # /tooling endpoints
│       │   └── models/
│       │       └── tool_db.py      # SQLAlchemy models for tools/materials
│       └── data/
│           ├── posts/              # Post-processor configs (GRBL, Mach4, etc.)
│           └── tool_library.sqlite # Auto-generated database
├── packages/
│   ├── client/                     # Vue 3 client (future)
│   │   └── README.md
│   └── shared/                     # Shared types
│       └── README.md
├── tools/
│   └── codegen/
│       └── generate_ts_sdk.sh      # OpenAPI → TypeScript SDK generator
├── scripts/
│   ├── wire_in_monorepo.sh         # Bash setup script
│   └── wire_in_monorepo.ps1        # PowerShell setup script
└── .github/
    └── workflows/
        ├── api_tests.yml           # API smoke tests
        ├── sdk_codegen.yml         # Auto-generate SDK on API changes
        └── client_lint_build.yml   # Client CI (placeholder)
```

## 🚀 Quick Start

### 1. Install API Dependencies

```powershell
cd services\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start the API Server

```powershell
cd services\api
uvicorn app.main:app --reload --port 8000
```

Server will start at: **http://localhost:8000**

- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### 3. Test the API

#### Health Check
```powershell
curl http://localhost:8000/health
# {"ok": true}
```

#### Simulate G-code with Arcs
```powershell
$gcode = "G21 G90 G17 F1200`nG0 Z5`nG0 X0 Y0`nG1 Z-1 F300`nG2 X60 Y40 I0 J20`nG0 Z5"
$body = @{gcode = $gcode} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/cam/simulate_gcode" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body | Select-Object -ExpandProperty Content
```

#### List Post-Processors
```powershell
curl http://localhost:8000/tooling/posts | ConvertFrom-Json
# Returns: grbl, mach4, pathpilot, linuxcnc, masso
```

## 📡 API Endpoints

### CAM Simulation (`/cam`)

#### `POST /cam/simulate_gcode`
Simulate G-code with arc support (G2/G3), time estimation, and safety checks.

**Request:**
```json
{
  "gcode": "G21 G90 G17 F1200\nG0 X0 Y0\nG2 X60 Y40 I30 J20",
  "as_csv": false,
  "accel": 2000.0,
  "clearance_z": 5.0
}
```

**Response Headers:**
- `X-CAM-Summary`: `{"units":"mm", "total_xy":123.45, "total_z":10.0, "est_seconds":5.67}`
- `X-CAM-Modal`: `{"units":"mm", "abs":true, "plane":"G17", "feed_mode":"G94", "F":1200, "S":0}`

**Response Body:**
```json
{
  "moves": [
    {"line":1, "code":"G0", "x":0, "y":0, "z":5, "feed":3000, "t":0.1},
    {"line":2, "code":"G2", "x":60, "y":40, "z":5, "i":30, "j":20, "cx":30, "cy":20, "feed":1200, "t":2.45}
  ],
  "issues": []
}
```

### Tooling (`/tooling`)

#### `GET /tooling/tools`
List all tools in the database.

#### `POST /tooling/tools`
Add a new tool.

```json
{
  "name": "Endmill 6mm",
  "type": "flat",
  "diameter_mm": 6.0,
  "flute_count": 2,
  "helix_deg": 30.0
}
```

#### `GET /tooling/materials`
List all materials.

#### `POST /tooling/materials`
Add a new material.

```json
{
  "name": "Hardwood",
  "chipload_mm": 0.15,
  "max_rpm": 18000
}
```

#### `POST /tooling/feedspeeds`
Calculate feeds and speeds.

```json
{
  "tool_name": "Endmill 6mm",
  "material_name": "Hardwood",
  "rpm": 15000,
  "width_mm": 3.0,
  "depth_mm": 2.0
}
```

**Response:**
```json
{
  "rpm": 15000,
  "feed_mm_min": 4500.0
}
```

#### `GET /tooling/posts`
List all post-processor configurations.

**Response:**
```json
{
  "grbl": {"header": ["G90","G21","G94","F1000"], "footer": ["M5","M30"]},
  "mach4": {"header": ["G90","G21","G64 P0.01"], "footer": ["M5","M30"]},
  ...
}
```

## 🔧 Features

### G-code Simulator (Patch I1.2 Enhanced)

- **Arc Support**: G2/G3 with IJK format (center offset) and R format (radius)
- **Arc Math**: 
  - `arc_center_from_ijk()` - Calculate center from I/J/K offsets
  - `arc_center_from_r()` - Calculate center from radius (selects correct solution for CW/CCW)
  - `arc_length()` - Calculate arc length from sweep angle
- **Time Estimation**: Trapezoidal motion profile with acceleration
- **Modal State**: Tracks units (G20/G21), abs/inc (G90/G91), plane (G17/G18/G19), feed mode (G93/G94)
- **Safety Checks**: 
  - Envelope violation detection
  - Unsafe rapid detection (XY motion below Z=0)
  - Auto-split rapids with Z clearance
- **CSV Export**: Export simulation results with `as_csv: true`

### Tool Library

- SQLite database (`services/api/data/tool_library.sqlite`)
- Auto-created on first request
- Stores tools (name, type, diameter, flutes, helix)
- Stores materials (name, chipload, max RPM)
- Calculates feeds/speeds with engagement compensation

### Post-Processors

- Pre-configured for 5 platforms: GRBL, Mach4, PathPilot, LinuxCNC, MASSO
- JSON format for easy editing
- Header/footer G-code templates

## 🧪 Testing

### Manual Testing

```powershell
# Terminal 1: Start API
cd services\api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run tests
curl http://localhost:8000/health
curl http://localhost:8000/tooling/posts
```

### CI/CD

Three GitHub Actions workflows:

1. **`api_tests.yml`** - Boots API, tests /cam/simulate_gcode and /tooling endpoints
2. **`sdk_codegen.yml`** - Generates TypeScript SDK from OpenAPI on API changes
3. **`client_lint_build.yml`** - Placeholder for client build (wire up later)

## 📦 SDK Generation

Generate TypeScript types from OpenAPI:

```bash
# Start API first
cd services/api
uvicorn app.main:app --port 8000 &

# Generate SDK
bash tools/codegen/generate_ts_sdk.sh
# Creates: packages/shared/index.d.ts
```

Usage in TypeScript:

```typescript
import type { SimInput, ToolIn, MaterialIn } from '@toolbox/shared';

const request: SimInput = {
  gcode: "G21 G90\nG2 X60 Y40 I30 J20",
  as_csv: false
};
```

## 🐳 Docker (Future)

Planned:

```yaml
# docker-compose.yml
services:
  api:
    build: ./services/api
    ports:
      - "8000:8000"
    env_file: .env
  client:
    build: ./packages/client
    ports:
      - "8080:8080"
    depends_on:
      - api
```

## 🔗 Integration with Existing Code

### Server Integration

The new `services/api/` structure **coexists** with your existing `server/` directory:

- **Old**: `server/app.py`, `server/sim_validate.py` (Patch I1 versions)
- **New**: `services/api/app/main.py`, `services/api/app/routers/sim_validate.py` (Patch I1.2 enhanced)

**Migration Path**:
1. Test new API endpoints alongside existing server
2. Update client to use new endpoints: `/cam/*` → `http://localhost:8000/cam/*`
3. Deprecate old `server/` once validated

### Client Integration

Your existing `client/` directory remains unchanged. To integrate:

1. Update Vite proxy config:
   ```typescript
   // vite.config.ts
   export default {
     server: {
       proxy: {
         '/cam': 'http://localhost:8000',
         '/tooling': 'http://localhost:8000'
       }
     }
   }
   ```

2. Import new SDK types:
   ```typescript
   import type { SimInput } from '@toolbox/shared';
   ```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Arc Math**: See `services/api/app/routers/sim_validate.py` docstrings
- **Patch History**: `PATCHES_I1_2_3_INTEGRATION.md` (existing docs)

## 🛠️ Development

### Adding New Endpoints

1. Create router in `services/api/app/routers/`
2. Register in `services/api/app/main.py`:
   ```python
   from .routers.my_router import router as my_router
   app.include_router(my_router)
   ```
3. Add tests to `.github/workflows/api_tests.yml`

### Adding New Post-Processors

Create JSON file in `services/api/app/data/posts/`:

```json
{
  "header": ["G90", "G21", "(Custom Post)"],
  "footer": ["M5", "M30"]
}
```

## 🚧 Roadmap

- [ ] Docker Compose setup
- [ ] Client package integration (move existing `client/` to `packages/client/`)
- [ ] WebSocket support for real-time simulation
- [ ] 3D visualization endpoint (Three.js scene data)
- [ ] Tool library importers (vendor CSVs)
- [ ] Advanced feeds/speeds (material hardness, tool wear)

## 🐛 Known Issues

- Tool database is empty by default (add tools via POST)
- SDK generation requires running server
- Client CI workflow is placeholder only

## 📝 License

Same as parent project.

## 🤝 Contributing

1. Create feature branch
2. Add tests to `api_tests.yml`
3. Run locally: `uvicorn app.main:app --reload`
4. Submit PR

---

**Questions?** Check existing docs:
- `PATCHES_I1_2_3_INTEGRATION.md` - Simulation features
- `WORKSPACE_ANALYSIS.md` - Architecture decisions
- `.github/copilot-instructions.md` - Project overview
