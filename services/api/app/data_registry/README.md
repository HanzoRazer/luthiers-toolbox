# Hybrid Data Registry - Complete Implementation

**Date:** December 13, 2025  
**Purpose:** Three-tier data architecture for multi-product SaaS delivery

---

## The 9 Products

| # | Product | Price | Data Tier |
|---|---------|-------|-----------|
| 1 | **ltb-express** | $49 | System only (honeypot) |
| 2 | **ltb-pro** | $299-399 | System + Pro edition |
| 3 | **ltb-enterprise** | $899-1299 | System + Pro + Enterprise |
| 4 | **ltb-parametric** | $39-59 | System + Parametric templates |
| 5 | **ltb-neck-designer** | $29-79 | System + Neck templates |
| 6 | **ltb-headstock-designer** | $14-29 | System + Headstock templates |
| 7 | **ltb-bridge-designer** | $14-19 | System + Bridge templates |
| 8 | **ltb-fingerboard-designer** | $19-29 | System + Fretboard templates |
| 9 | **ltb-cnc-blueprints** | $29-49 | Housing industry blueprints |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM DATA (Read-Only)                      │
│  Shipped with product, same for all users, version-locked       │
│  ─────────────────────────────────────────────────────────────  │
│  • Scale lengths (Fender 25.5", Gibson 24.75", etc.)            │
│  • Fret math formulas (12-TET, compensation)                    │
│  • Standard neck profiles (C, D, V, asymmetric)                 │
│  • Wood species reference (Janka, density, grain)               │
│  • Standard body templates (Strat, LP, J45 outlines)            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐
│  PRO EDITION  │   │  PARAMETRIC   │   │   CNC BLUEPRINTS      │
│───────────────│   │   PRODUCTS    │   │   (Housing Industry)  │
│ • Router bits │   │───────────────│   │───────────────────────│
│ • Machines    │   │ • Guitar CAD  │   │ • Framing standards   │
│ • Empirical   │   │ • Neck design │   │ • Cabinet specs       │
│ • CAM presets │   │ • Headstock   │   │ • Door/window dims    │
│ • Post procs  │   │ • Bridge      │   │ • Construction codes  │
└───────────────┘   │ • Fretboard   │   └───────────────────────┘
                    └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER DATA (Tenant-Isolated)                  │
│  Owned by user, never shared, CRUD with quotas                  │
│  ─────────────────────────────────────────────────────────────  │
│  • Custom profiles, templates, tools, machines, projects        │
│  • Local SQLite with optional PostgreSQL cloud sync             │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
data_registry/
├── __init__.py                     # Package exports
├── registry.py                     # Core registry class (750+ lines)
├── README.md                       # This file
├── schemas/
│   └── all_schemas.json            # Validation rules
│
├── system/                         # Universal, read-only (ALL products)
│   ├── instruments/
│   │   ├── body_templates.json     # 7 body templates
│   │   └── neck_profiles.json      # 7 neck profiles
│   ├── materials/
│   │   ├── wood_species.json       # 472 wood species (v4.0.0)
│   │   └── SOURCES.md              # Data sources & methodology
│   └── references/
│       ├── fret_formulas.json      # 12-TET, compensation
│       └── scale_lengths.json      # 8 standard scales
│
├── edition/
│   ├── express/                    # (empty - Express = honeypot)
│   │
│   ├── pro/                        # PRO/ENTERPRISE CAM features
│   │   ├── tools/router_bits.json      # 11 router bits
│   │   ├── machines/profiles.json      # 3 machines (BCAMCNC 2030CA)
│   │   ├── empirical/wood_limits.json  # 11 species limits
│   │   ├── cam_presets/presets.json    # 8 CAM recipes
│   │   └── posts/processors.json       # 4 post processors
│   │
│   ├── parametric/                 # ltb-parametric
│   │   └── guitar_templates.json       # 4 parametric guitar templates
│   │
│   ├── neck_designer/              # ltb-neck-designer
│   │   └── neck_templates.json         # 5 neck profiles + 4 truss specs
│   │
│   ├── headstock_designer/         # ltb-headstock-designer
│   │   └── headstock_templates.json    # 6 headstocks + 5 tuner layouts
│   │
│   ├── bridge_designer/            # ltb-bridge-designer
│   │   └── bridge_templates.json       # 6 bridges + saddle specs
│   │
│   ├── fingerboard_designer/       # ltb-fingerboard-designer
│   │   └── fretboard_templates.json    # 6 fretboards + 6 inlays + 4 fret wires
│   │
│   └── cnc_blueprints/             # ltb-cnc-blueprints (HOUSING industry)
│       └── blueprint_standards.json    # Framing, cabinets, doors, codes
│
└── user/                           # Per-tenant, SQLite, cloud-synced
    └── {user_id}.sqlite            # Created on demand
```

---

## Product Entitlements Matrix

| Data Category | Express | Pro | Enterprise | Parametric | Neck | Headstock | Bridge | Fretboard | Blueprints |
|---------------|---------|-----|------------|------------|------|-----------|--------|-----------|------------|
| **System** |
| Scale lengths | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fret formulas | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| Neck profiles | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| Body templates | ✓ | ✓ | ✓ | ✓ | - | - | - | - | - |
| Wood species | ✓ | ✓ | ✓ | ✓ | - | - | - | - | - |
| **Edition** |
| Tool library | ❌ | ✓ | ✓ | - | - | - | - | - | - |
| Machines | ❌ | ✓ | ✓ | - | - | - | - | - | - |
| Empirical limits | ❌ | ✓ | ✓ | - | - | - | - | - | - |
| CAM presets | ❌ | ✓ | ✓ | - | - | - | - | - | - |
| Post processors | ❌ | ✓ | ✓ | - | - | - | - | - | - |
| Guitar templates | - | - | - | ✓ | - | - | - | - | - |
| Neck templates | - | - | - | - | ✓ | - | - | - | - |
| Headstock templates | - | - | - | - | - | ✓ | - | - | - |
| Bridge templates | - | - | - | - | - | - | ✓ | - | - |
| Fretboard templates | - | - | - | - | - | - | - | ✓ | - |
| Blueprint standards | - | - | - | - | - | - | - | - | ✓ |

---

## Usage Examples

### Core Products (Express/Pro/Enterprise)

```python
from data_registry import Registry

# Pro edition
reg = Registry(edition="pro", user_id="user_123")

# System data (all editions)
scale = reg.get_scale_length("fender_25_5")
wood = reg.get_wood("mahogany_honduran")

# Pro features
tool = reg.get_tool("flat_6mm_2f")
machine = reg.get_machine("bcamcnc_2030ca")
limits = reg.get_empirical_limit("mahogany_honduran")
```

### Standalone Parametric Tools

```python
# ltb-neck-designer
reg = Registry(edition="neck_designer")
template = reg.get_neck_template("vintage_50s_v")
truss = reg.get_truss_specs()

# ltb-fingerboard-designer
reg = Registry(edition="fingerboard_designer")
fretboard = reg.get_fretboard_template("compound_radius_24")
inlays = reg.get_inlay_patterns()
frets = reg.get_fret_wire_specs()

# ltb-bridge-designer
reg = Registry(edition="bridge_designer")
bridge = reg.get_bridge_template("tune_o_matic")
saddles = reg.get_saddle_specs()
```

### Housing Industry (CNC Blueprints)

```python
# ltb-cnc-blueprints
reg = Registry(edition="cnc_blueprints")
standards = reg.get_blueprint_standards()
dims = reg.get_dimension_tables()
codes = reg.get_construction_codes()
```

### Edition Enforcement

```python
# Express edition - blocked from Pro features
express = Registry(edition="express")
try:
    tools = express.get_tools()
except EntitlementError as e:
    print("Upgrade to Pro for tool library")

# Neck Designer - blocked from Pro features
neck = Registry(edition="neck_designer")
try:
    machines = neck.get_machines()
except EntitlementError as e:
    print("Machines only in Pro/Enterprise")
```

---

## Data Counts Summary

| Edition | Templates | Tools | Machines | Species | Other |
|---------|-----------|-------|----------|---------|-------|
| System | 7 bodies, 7 necks | - | - | 472 | 8 scales, formulas |
| Pro | - | 11 | 3 | 11 limits | 8 presets, 4 posts |
| Parametric | 4 guitars | - | - | - | constraints |
| Neck | 5 necks | - | - | - | 4 truss specs |
| Headstock | 6 headstocks | - | - | - | 5 tuner layouts |
| Bridge | 6 bridges | - | - | - | saddle specs |
| Fretboard | 6 fretboards | - | - | - | 6 inlays, 4 frets |
| Blueprints | - | - | - | - | 4 standards, 4 dims, 3 codes |

---

## Next Steps

1. **Calculator Rehabilitation** - Wire calculators to read from this registry
2. **Geometry Sandbox** - Claude leads consultation (separate location)
3. **Cloud Sync** - PostgreSQL backend for SaaS products
4. **Product Cloning** - Use Create-ProductRepos.ps1 scripts (Q2 2026)
