# CANONICAL vs CURRENT STATE ANALYSIS

## WHAT IS CANONICAL (Production-Ready, Stable)

### ✅ Core API Backend (services/api/app/)
- **93 Production Routers** (Waves 1-13, 16-19)
- **Main Application**: main.py (777 lines, all imports working)
- **Database Layer**: db/ (migrations, startup)
- **Core Domains**:
  - cam/ - CAM operations (Wave 18 consolidated)
  - compare/ - Comparison tools (Wave 19 consolidated)
  - rmos/ - Rosette Manufacturing Orchestration (v2 default)
  - art_studio/ - Art/design tools
  - routers/ - 93 working routers

### ✅ AI Infrastructure (NEW - Just Committed)
**Location**: services/api/app/ai/
- cost/ - AI cost estimation
- observability/ - Audit logging, request tracking
- prompts/ - Template system
- providers/ - Base provider interface
- safety/ - Policy enforcement
- transport/ - LLM & image clients

**Status**: Production-ready structure, DUPLICATE of _experimental/ai_core

### ✅ Governance Contracts (10 contracts)
**Location**: docs/governance/
All v1 contracts defining system behavior:
- SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md
- RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md
- AI_SANDBOX_EXECUTION_AUTHORITY_CONTRACT_v1.md
- SECURITY_TRUST_BOUNDARY_CONTRACT_v1.md
- (+ 6 more)

---

## ⚠️ WHAT IS NOT CANONICAL (But Should Be)

### 1. AI Graphics Module (Wave 14) - HIGH VALUE
**Current Location**: _experimental/ai_graphics/
**Size**: ~40 Python files
**Routers**: 3 (vision, advisory, teaching)
**Status**: Functional, wrapped in try/except

**Components**:
- Vision Engine (image analysis)
- Advisory System (AI guidance)
- Teaching Loop (training data generation)
- Image providers & transport
- Rosette generator (AI-powered)

**WHY NOT CANONICAL**: Never promoted after Wave 14
**SHOULD BE**: services/api/app/ai_graphics/ (production)

---

### 2. AI-CAM Router (Wave 9) - MEDIUM VALUE
**Current Location**: _experimental/ai_cam/
**Size**: ~5 files
**Routers**: 1 (ai_cam_router)

**Components**:
- AI CAM advisor
- G-code explainer
- Optimization suggestions

**WHY NOT CANONICAL**: No clear adoption metrics
**DECISION NEEDED**: Promote vs Sunset

---

### 3. CNC Production Analytics (Waves 9-11) - HIGH VALUE
**Current Location**: _experimental/cnc_production/
**Size**: ~25 files
**Routers**: 3 (learn, joblog, dashboard - referenced but not loading)

**Components**:
- feeds_speeds/ - Chipload calc, learned overrides
- joblog/ - Job telemetry storage
- learn/ - Live learning ingestor, risk buckets

**WHY NOT CANONICAL**: Missing from main.py imports (broken references)
**SHOULD BE**: services/api/app/cnc_production/ (production)

---

### 4. Analytics Module (Wave 11) - MEDIUM VALUE
**Current Location**: _experimental/analytics/
**Size**: ~4 files
**Routers**: 2 (analytics, advanced_analytics - try/except wrapped)

**Components**:
- Job analytics
- Material analytics
- Pattern analytics

**WHY NOT CANONICAL**: Optional feature, wrapped for graceful failure
**SHOULD BE**: services/api/app/analytics/ (production)

---

### 5. Infrastructure (Wave 13) - OPERATIONAL SUPPORT
**Current Location**: _experimental/infra/
**Size**: 1 file
**Component**: live_monitor.py

**WHY NOT CANONICAL**: Monitoring is typically experimental until proven
**DECISION NEEDED**: Promote or integrate into observability/

---

## 🔴 DUPLICATE CODE - CRITICAL ISSUE

### services/api/app/ai/ vs _experimental/ai_core/
**Problem**: Both exist, serving similar purposes

**ai/ (NEW - canonical structure)**:
- cost/, observability/, prompts/, providers/, safety/, transport/
- 16 files total
- Clean architecture

**_experimental/ai_core/ (OLD - monolithic)**:
- clients.py, generators.py, safety.py, structured_generator.py
- 6 files total
- Less organized

**RESOLUTION NEEDED**: 
- Option A: Delete _experimental/ai_core/, migrate to ai/
- Option B: Merge functionality, keep ai/ as canonical

---

## 📊 SUMMARY STATS

| Category | Current Location | Files | Status | Should Be |
|----------|-----------------|-------|--------|-----------|
| **CANONICAL** | services/api/app/ | ~300+ | ✅ Production | (keep as-is) |
| **AI Infrastructure** | ai/ | 16 | ✅ NEW | (verify no conflicts) |
| **AI Graphics** | _experimental/ai_graphics/ | ~40 | ⚠️ Limbo | ai_graphics/ |
| **AI-CAM** | _experimental/ai_cam/ | ~5 | ⚠️ Limbo | ai_cam/ OR sunset |
| **CNC Production** | _experimental/cnc_production/ | ~25 | ⚠️ Broken | cnc_production/ |
| **Analytics** | _experimental/analytics/ | ~4 | ⚠️ Optional | analytics/ |
| **AI Core (OLD)** | _experimental/ai_core/ | ~6 | 🔴 DUPLICATE | DELETE |
| **Infra** | _experimental/infra/ | 1 | ⚠️ Util | observability/ |

---

## 🎯 RECOMMENDED CANONICAL STATE

### Phase 1: Resolve Duplicates (URGENT)
1. **Audit ai/ vs ai_core/**
   - Identify overlapping functionality
   - Migrate unique features from ai_core/ → ai/
   - Delete _experimental/ai_core/

2. **Verify ai/ is used**
   - Check if any code imports from services/api/app/ai/
   - If unused, consider it dead code from merge conflict

### Phase 2: Promote High-Value Modules
1. **ai_graphics/** → Production (Wave 14 completion)
2. **cnc_production/** → Production (fix broken imports)
3. **analytics/** → Production (remove try/except wrappers)

### Phase 3: Decide on Marginal Modules
1. **ai_cam/** - Usage audit, then promote or sunset
2. **infra/live_monitor** - Merge into observability/

---

## 🚨 IMMEDIATE ACTIONS

1. ✅ **Check ai/ directory usage**
   - Is it imported anywhere?
   - Does it conflict with _experimental/ai_core/?

2. ✅ **Restore cnc_production imports**
   - Fix broken learn/dashboard router references in main.py

3. ✅ **Document promotion criteria**
   - What makes _experimental → production?
   - Who approves promotions?

