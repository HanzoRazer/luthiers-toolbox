# Data Registry Integration - Quick Reference

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Module:** Data Registry + Edition Middleware

---

## Overview

The Data Registry provides **edition-based data access** for the Luthier's ToolBox multi-product SaaS architecture. It implements a three-tier data model:

| Tier | Access | Examples |
|------|--------|----------|
| **System** | All editions | Scale lengths, fret formulas, wood species |
| **Edition** | Pro/Enterprise | Empirical limits, machines, tools, CAM presets |
| **User** | Per-user | Custom profiles, projects (future) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
├─────────────────────────────────────────────────────────────────┤
│  useEdition()          │  useRegistryStore()  │  api/registry   │
│  - canAccess(feature)  │  - scaleLengths      │  - getScales()  │
│  - showUpgradePrompt() │  - empiricalLimits   │  - getLimits()  │
└────────────────────────┴──────────────────────┴─────────────────┘
                                    │
                                    ▼ X-Edition header
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────────┤
│  registry_router.py    │  edition_middleware  │  data_registry  │
│  - /api/registry/*     │  - get_edition()     │  - Registry()   │
│  - 7 endpoints         │  - require_feature() │  - JSON loaders │
└────────────────────────┴──────────────────────┴─────────────────┘
```

---

## Edition Tiers

### Core Editions (Tiered)

| Edition | Price | Features |
|---------|-------|----------|
| **Express** | $49 | Geometry, templates, DXF export |
| **Pro** | $299-399 | + Tools, machines, empirical limits, G-code |
| **Enterprise** | $899-1299 | + Fleet, scheduling, analytics |

### Standalone Tools (Etsy/Gumroad)

| Tool | Price | Scope |
|------|-------|-------|
| Parametric Guitar | $39-59 | Full guitar CAD |
| Neck Designer | $29-79 | Neck profiles |
| Headstock Designer | $14-29 | Headstock layouts |
| Bridge Designer | $14-19 | Bridge geometry |
| Fingerboard Designer | $19-29 | Fretboard calculator |

---

## API Endpoints

### Base URL: `/api/registry`

| Endpoint | Method | Tier | Description |
|----------|--------|------|-------------|
| `/info` | GET | All | Registry metadata |
| `/scale_lengths` | GET | System | Standard scale lengths |
| `/wood_species` | GET | System | Wood reference data |
| `/fret_formulas` | GET | System | Fret calculation constants |
| `/empirical_limits` | GET | Edition | Feed/speed limits (Pro+) |
| `/empirical_limits/{wood_id}` | GET | Edition | Per-wood limits (Pro+) |
| `/health` | GET | All | Health check |

### Edition Detection

Priority order:
1. `X-Edition` header (testing/admin)
2. `?edition=` query param (testing)
3. `LTB_DEFAULT_EDITION` env var
4. Default: `pro` (development)

### Example Requests

```bash
# System tier (all editions)
curl http://localhost:8000/api/registry/scale_lengths

# Edition tier (Pro required)
curl -H "X-Edition: pro" http://localhost:8000/api/registry/empirical_limits

# Express user (403 Forbidden)
curl -H "X-Edition: express" http://localhost:8000/api/registry/empirical_limits
```

---

## Backend Usage

### Registry Class

```python
from app.data_registry import Registry, Edition, EntitlementError

# Initialize for edition
reg = Registry(edition="pro")

# System tier (all editions)
scales = reg.get_scale_lengths()      # {"scales": {...}, "count": 8}
woods = reg.get_wood_species()        # {"species": {...}, "count": 13}
formulas = reg.get_fret_formulas()    # {"formulas": {...}}

# Edition tier (Pro/Enterprise only)
try:
    limits = reg.get_empirical_limits()  # {"limits": {...}, "count": 13}
except EntitlementError:
    print("Upgrade required")
```

### Edition Middleware

```python
from fastapi import Depends
from app.middleware import get_edition, require_feature, EditionContext

# Any edition can access
@router.get("/public")
def public_endpoint(ctx: EditionContext = Depends(get_edition)):
    return {"edition": ctx.edition.value}

# Pro or higher required
@router.get("/pro-only")
def pro_endpoint(ctx: EditionContext = Depends(require_feature("empirical_limits"))):
    return {"data": load_empirical_data()}
```

### EditionContext Methods

```python
ctx.can_access("empirical_limits")  # bool - check without raising
ctx.require_feature("tools")         # raises HTTPException(403) if denied
ctx.is_express                       # bool
ctx.is_pro                           # bool (True for Pro or Enterprise)
ctx.is_enterprise                    # bool
ctx.is_standalone                    # bool (parametric tools)
```

---

## Frontend Usage

### Pinia Store

```typescript
import { useRegistryStore } from '@/stores/useRegistryStore'

const registry = useRegistryStore()

// Initialize on app load
await registry.initialize()

// Access cached data
const scales = registry.scaleLengths   // ScaleLengthResponse | null
const woods = registry.woodSpecies     // WoodSpeciesResponse | null
const limits = registry.empiricalLimits // EmpiricalLimitsResponse | null

// Check entitlements
if (registry.canAccessEmpiricalLimits) {
  await registry.loadEmpiricalLimits()
}

// Handle entitlement errors
if (registry.hasEntitlementError) {
  showUpgradeModal(registry.entitlementError)
}
```

### useEdition Composable

```typescript
import { useEdition } from '@/composables/useEdition'

const { canAccess, showUpgradePrompt, edition } = useEdition()

// Feature gating in templates
<div v-if="canAccess('empirical_limits')">
  <EmpiricalLimitsTable />
</div>
<UpgradeButton v-else @click="showUpgradePrompt('empirical_limits')" />

// Convenience computed
canAccessEmpiricalLimits  // computed<boolean>
canAccessTools            // computed<boolean>
canAccessGcode            // computed<boolean>
canAccessFleet            // computed<boolean>
```

### API Client

```typescript
import { 
  getScaleLengths, 
  getEmpiricalLimits,
  isEntitlementError 
} from '@/api/registry'

// System tier (always succeeds)
const scales = await getScaleLengths()

// Edition tier (may throw)
try {
  const limits = await getEmpiricalLimits()
} catch (err) {
  if (isEntitlementError(err)) {
    console.log(`Upgrade to ${err.required_edition}`)
  }
}
```

---

## Testing

### Run Pytest (Backend)

```powershell
cd services/api
python -m pytest app/tests/test_data_registry.py -v --override-ini="addopts="
```

**22 tests covering:**
- Registry initialization
- System tier data access
- Edition tier entitlement enforcement
- API endpoint responses
- Edition middleware detection

### Run Smoke Tests (PowerShell)

```powershell
# Start API server first
cd services/api
uvicorn app.main:app --reload --port 8000

# In another terminal
.\test_data_registry.ps1
```

**10 tests covering:**
- Registry info Express/Pro
- Scale lengths, wood species, fret formulas
- Empirical limits 403/200 by edition
- Health check

---

## File Reference

### Backend

| File | Purpose |
|------|---------|
| `services/api/app/data_registry/__init__.py` | Package exports |
| `services/api/app/data_registry/registry.py` | Registry class, Edition enum |
| `services/api/app/data_registry/loaders.py` | JSON data loaders |
| `services/api/app/middleware/__init__.py` | Middleware exports |
| `services/api/app/middleware/edition_middleware.py` | Edition context, guards |
| `services/api/app/routers/registry_router.py` | API endpoints |
| `services/api/app/data/registry/` | JSON data files |

### Frontend

| File | Purpose |
|------|---------|
| `packages/client/src/api/registry.ts` | Typed API client |
| `packages/client/src/stores/useRegistryStore.ts` | Pinia store |
| `packages/client/src/composables/useEdition.ts` | Feature gating |

### Tests

| File | Type | Tests |
|------|------|-------|
| `services/api/app/tests/test_data_registry.py` | pytest | 22 |
| `test_data_registry.ps1` | PowerShell | 10 |

---

## Feature Requirements

| Feature | Minimum Edition |
|---------|-----------------|
| `geometry` | Express |
| `scale_lengths` | Express |
| `fret_formulas` | Express |
| `wood_species` | Express |
| `dxf_export` | Express |
| `empirical_limits` | Pro |
| `tools` | Pro |
| `machines` | Pro |
| `gcode_export` | Pro |
| `simulation` | Pro |
| `fleet` | Enterprise |
| `scheduling` | Enterprise |
| `analytics` | Enterprise |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LTB_DEFAULT_EDITION` | `pro` | Default edition for API |
| `LTB_EDITION_OVERRIDE` | `true` | Allow header/param override |

---

## Commit History

| Phase | Commit | Description |
|-------|--------|-------------|
| 1 | `0a37355` | Data registry package |
| 2 | `1b5831c` | Calculator rehabilitation |
| 3 | `d5df4a1` | Instrument geometry consolidation |
| 4 | `3fcf2b1` | Main.py integration |
| 5 | `2ca1a08` | Edition middleware |
| 6 | `5020a6f` | Frontend integration |
| 7 | `9e20c6f` | Testing |
| 8 | — | Documentation |

---

## See Also

- [AGENTS.md](./AGENTS.md) - Repository guidance
- [copilot-instructions.md](.github/copilot-instructions.md) - Project overview
- [MACHINE_PROFILES_MODULE_M.md](./MACHINE_PROFILES_MODULE_M.md) - Machine profiles
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - CAM pocketing
