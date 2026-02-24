# Business Startup Suite Specification

**Date:** 2026-02-23
**Status:** Implemented
**Location:** `services/api/app/business/`

---

## Purpose

Help luthiers answer the critical business questions:

| Question | Service |
|----------|---------|
| "What materials do I need?" | BOM Service |
| "What does it cost to build?" | COGS Service |
| "What should I charge?" | Pricing Service |
| "How many do I need to sell?" | Break-Even Service |
| "Can I afford to quit my day job?" | Cash Flow Service |

---

## Architectural Boundary

### ALLOWED Imports
```python
from app.core.*           # Shared types
from app.calculators.*    # Domain calculations
```

### FORBIDDEN Imports
```python
from app.cam.*            # Manufacturing, not business
from app.rmos.*           # Safety, not business
from app.saw_lab.*        # Production ops, not business
from app.analyzer.*       # Acoustic analysis, not business
```

---

## Module Structure

```
services/api/app/business/
├── __init__.py           # Exports and boundary docs
├── schemas.py            # All data types
├── bom_service.py        # Bill of Materials
├── cogs_service.py       # Cost of Goods Sold
├── pricing_service.py    # Pricing strategy
├── breakeven_service.py  # Break-even analysis
├── cashflow_service.py   # Cash flow projections
└── router.py             # API endpoints
```

---

## Services

### 1. BOM Service

**Purpose:** Track what materials go into each instrument.

**Features:**
- Default material library (tonewoods, hardware, finish, etc.)
- BOM templates by instrument type
- Custom BOM creation
- Shopping list generation
- Supplier tracking

**Key Types:**
```python
Material:
  id, name, category, unit, unit_cost, supplier, species, grade

BillOfMaterials:
  instrument_type, items[], total_materials_cost, cost_by_category
```

### 2. COGS Service

**Purpose:** Calculate true cost per instrument.

**Formula:**
```
COGS = Direct Materials + Direct Labor + Allocated Overhead
```

**Features:**
- Labor estimation by task category
- Configurable hourly rates
- Overhead allocation (per-unit)
- Margin analysis at various price points

**Default Labor Categories:**
- Design, Wood Prep, Joinery, Carving
- Fretting, Finishing, Assembly, Setup, QA

### 3. Pricing Service

**Purpose:** Determine optimal selling price.

**Pricing Models:**
1. **Cost-Plus:** COGS × (1 + markup%)
2. **Market-Based:** Aligned with competitors
3. **Value-Based:** What custom tier commands

**Features:**
- Competitor database
- Market position analysis (below/at/above)
- Margin protection (minimum margin warning)
- Tier-based recommendations

**Default Competitors:**
- Gibson, Martin, Taylor (premium)
- Collings, Santa Cruz, Bourgeois (custom)
- Yamaha, Epiphone (entry)

### 4. Break-Even Service

**Purpose:** Calculate units needed to cover fixed costs.

**Formula:**
```
Break-Even Units = Fixed Costs / Contribution Margin
Contribution Margin = Price - Variable Cost
```

**Features:**
- Volume scenarios (1-12 units/month)
- Target profit calculation
- Sensitivity analysis (±20% on price, costs)
- Profit at specific volume

### 5. Cash Flow Service

**Purpose:** Project cash over time.

**Features:**
- Monthly projections (up to 60 months)
- Revenue ramp-up modeling
- Cash shortfall warnings
- Runway calculation
- Required capital estimation

**Key Outputs:**
- Months to positive cash flow
- Minimum cash point
- Required starting capital
- Cash warnings

---

## API Endpoints

### BOM
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/business/materials` | GET | List materials |
| `/api/business/materials/{id}` | GET | Get material |
| `/api/business/materials` | POST | Add material |
| `/api/business/bom/from-template` | POST | Create BOM from template |
| `/api/business/bom/templates` | GET | List templates |

### COGS
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/business/cogs/calculate` | POST | Calculate COGS |
| `/api/business/cogs/labor-rates` | GET | Get labor rates |
| `/api/business/cogs/labor-rates/{cat}` | PUT | Update rate |
| `/api/business/cogs/overhead` | GET | Get overhead summary |

### Pricing
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/business/pricing/calculate` | POST | Get pricing strategy |
| `/api/business/pricing/competitors` | GET | Competitor summary |
| `/api/business/pricing/competitors` | POST | Add competitor |

### Break-Even
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/business/breakeven/calculate` | POST | Break-even analysis |
| `/api/business/breakeven/target-profit` | POST | Units for target profit |
| `/api/business/breakeven/sensitivity` | POST | Sensitivity analysis |

### Cash Flow
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/business/cashflow/project` | POST | Create projection |
| `/api/business/cashflow/startup` | POST | Startup projection |
| `/api/business/cashflow/required-capital` | POST | Calculate capital needed |

---

## Example Workflow

### "Can I start a guitar business?"

```python
# 1. Create BOM for your first guitar
bom = POST /api/business/bom/from-template
       ?instrument_type=acoustic_dreadnought
       &instrument_name=Dreadnought #1

# 2. Calculate COGS
cogs = POST /api/business/cogs/calculate
       body: bom

# 3. Get pricing recommendation
pricing = POST /api/business/pricing/calculate
          ?cogs=850
          &instrument_name=Custom Dreadnought
          &target_tier=custom

# 4. Calculate break-even
breakeven = POST /api/business/breakeven/calculate
            ?fixed_costs_monthly=1200
            &variable_cost_per_unit=850
            &selling_price_per_unit=3500

# 5. Project cash flow for first year
cashflow = POST /api/business/cashflow/startup
           ?starting_cash=10000
           &monthly_overhead=1200
           &target_monthly_revenue=7000
           &months_to_ramp=6
```

---

## Data Defaults

### Material Library
Pre-loaded with common lutherie materials:
- Sitka spruce, Indian rosewood, mahogany, ebony
- Gotoh tuners, bone nuts/saddles, truss rods
- Fret wire, binding, purfling
- Nitro lacquer, hide glue, Titebond

### Labor Rates (Default)
| Category | Rate |
|----------|------|
| Design | $50/hr |
| Wood Prep | $35/hr |
| Joinery | $45/hr |
| Carving | $50/hr |
| Fretting | $45/hr |
| Finishing | $40/hr |
| Assembly | $40/hr |
| Setup | $50/hr |
| QA | $45/hr |

### Overhead (Default Small Shop)
| Item | Monthly |
|------|---------|
| Rent | $800 |
| Utilities | $150 |
| Insurance | $100 |
| Tools | $100 |
| Marketing | $50 |
| Software | $30 |
| **Total** | **$1,230** |

---

## Future Enhancements

- [ ] Invoice generation
- [ ] Customer database
- [ ] Order tracking
- [ ] Tax calculations
- [ ] Multi-currency support
- [ ] Integration with accounting software
- [ ] Inventory management
- [ ] Supplier price tracking over time

---

*This module helps luthiers transition from hobbyist to business owner.*
