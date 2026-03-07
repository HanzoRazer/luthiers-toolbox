# Phase 2/3 Implementation Plan

**Date:** 2026-03-06
**Status:** Ready for Execution
**Target:** 3-tier SaaS deployment (Free/Pro/Shop)

---

## Executive Summary

This plan bridges the gap between the current state (experienced luthier focus, 7.6/10 score) and the full vision (3-tier SaaS for hobbyists, beginners, and shops, 9.0/10 target).

**Key Metrics:**
- Current feature coverage: ~60%
- Target feature coverage: 95%
- Blueprint Vectorizer rating: 8.0/10 (production-ready)
- Missing routes from website: 33+

---

## Phase 2: Feature Parity & UX Polish

**Duration:** 4-6 weeks
**Goal:** Make the website's feature promises match reality

### 2.1 Missing Route Implementation (Week 1-2)

| Priority | Route | Component | Backend Status |
|----------|-------|-----------|----------------|
| P0 | `/design/stratocaster` | InstrumentDesignView | API exists |
| P0 | `/design/telecaster` | InstrumentDesignView | API exists |
| P0 | `/design/les-paul` | InstrumentDesignView | API exists |
| P0 | `/art-studio/binding` | BindingDesignerView | Needs API |
| P0 | `/art-studio/headstock` | HeadstockDesignerView | Needs API |
| P0 | `/art-studio/purfling` | PurflingDesignerView | Needs API |
| P0 | `/art-studio/soundhole` | SoundholeDesignerView | Needs API |
| P0 | `/art-studio/fret-markers` | FretMarkersView | Needs API |
| P1 | `/cam/pocket` | PocketClearingView | API exists |
| P1 | `/cam/contour` | ContourCuttingView | API exists |
| P1 | `/cam/surfacing` | SurfacingView | API exists |
| P1 | `/cam/drilling` | DrillingView | API exists |
| P1 | `/cam/fret-slots` | FretSlottingView | API exists |
| P1 | `/cam/inlay` | InlayPocketsView | API exists |
| P1 | `/cam/simulator` | ToolpathSimulatorView | API exists |
| P2 | `/rmos/inventory` | InventoryView | Needs API |
| P2 | `/rmos/quality` | QualityControlView | Needs API |
| P2 | `/rmos/time` | TimeTrackingView | Needs API |
| P2 | `/rmos/orders` | OrderManagementView | Needs API |
| P2 | `/rmos/variants` | VariantAnalysisView | Partial API |
| P3 | `/ai/wood-grading` | WoodGradingView | Needs AI |
| P3 | `/ai/recommendations` | DesignRecsView | Needs AI |
| P3 | `/ai/assistant` | BuildAssistantView | Needs AI |
| P3 | `/ai/defect-detection` | DefectDetectionView | Needs AI |

### 2.2 Beginner UX Improvements (Week 2-3)

#### 2.2.1 Guided Mode

```typescript
// New store: useGuidedModeStore.ts
interface GuidedModeState {
  enabled: boolean
  currentStep: number
  workflow: 'design' | 'cam' | 'production'
  completedSteps: string[]
}
```

**Workflow Steps:**
1. Welcome → Choose instrument type
2. Select preset or upload blueprint
3. Adjust dimensions (with validation)
4. Generate toolpaths (with simulation preview)
5. Export G-code (with safety check)

#### 2.2.2 Plain-English Error Messages

| Rule ID | Current | Improved |
|---------|---------|----------|
| F001 | Feed rate exceeds limit | "Your feed rate (800 mm/min) is too fast for this material. Try 400 mm/min or less." |
| F021 | Tool breakage risk | "The cutting depth (8mm) is 5x the tool diameter. This will break your bit. Reduce to 3mm max." |
| F024 | Missing material | "Please select a material type so we can calculate safe cutting parameters." |

**Implementation:**
```python
# rules.py - add human_explanation field
class FeasibilityRule:
    rule_id: str
    level: RiskLevel
    message: str
    human_explanation: str  # NEW
    fix_hint: str  # NEW
```

#### 2.2.3 Contextual Help

- Add `HelpTooltip.vue` component
- Wire to existing `/docs/*.md` content
- Show on hover/focus for all CAM parameters

### 2.3 Blueprint Vectorizer Polish (Week 3-4)

#### Current: 8.0/10 → Target: 9.0/10

| Issue | Fix | Impact |
|-------|-----|--------|
| Body outline accuracy 92% | Dual-pass with aggressive+light modes | +3% |
| OCR dimension extraction 70% | Add EasyOCR fallback patterns | +15% |
| Feature classification 78% | Retrain RandomForest with more samples | +10% |
| False positive rate 8% | Add confidence thresholding | -5% |

#### Processing Tier UI

```vue
<!-- TierSelector.vue -->
<template>
  <div class="tier-selector">
    <TierCard
      tier="EXPRESS"
      time="<30 sec"
      features="Basic contours"
      :available="true"
    />
    <TierCard
      tier="STANDARD"
      time="1-2 min"
      features="ML classification"
      :available="tier >= 'pro'"
    />
    <TierCard
      tier="PREMIUM"
      time="3-5 min"
      features="Full pipeline"
      :available="tier >= 'pro'"
    />
    <TierCard
      tier="BATCH"
      time="10-20 min"
      features="Maximum quality"
      :available="tier === 'shop'"
    />
  </div>
</template>
```

### 2.4 Instrument Library Completion (Week 4-5)

**33 instrument models advertised, ~16 implemented**

| Category | Count | Missing |
|----------|-------|---------|
| Electric | 16 | Explorer, Flying V, Firebird, JS1000, Harmony H44 |
| Acoustic | 9 | Martin D-28, J-45, L-00, Carlos Jumbo |
| Archtop | 3 | Benedetto 17", L-5 |
| Bass/Specialty | 4 | Octave Mandolin |
| Smart | 1 | Complete |

**Implementation Pattern:**
1. Add DXF to `instrument_geometry/body/dxf/{category}/`
2. Add entry to `catalog.json`
3. Add preset to `presets/instruments/`
4. Wire route in router

---

## Phase 3: SaaS Infrastructure

**Duration:** 8-12 weeks
**Goal:** Enable monetization through tiered access

### 3.1 Authentication (Week 1-2)

**Recommended:** Clerk (fastest) or Supabase (self-hosted option)

```typescript
// authStore.ts
interface AuthState {
  user: User | null
  tier: 'free' | 'pro' | 'shop'
  projectCount: number
  projectLimit: number
  features: FeatureFlags
}

interface FeatureFlags {
  gcodeExport: boolean
  camSimulation: boolean
  rmosScheduling: boolean
  multiUser: boolean
  customPostProcessors: boolean
  inventoryManagement: boolean
  erp: boolean
}
```

**Tier Limits:**
| Feature | Free | Pro | Shop |
|---------|------|-----|------|
| Projects | 5 | ∞ | ∞ |
| G-code exports/day | 0 | ∞ | ∞ |
| Processing tier | EXPRESS | PREMIUM | BATCH |
| Seats | 1 | 1 | 10 |

### 3.2 Payment Integration (Week 2-3)

**Stripe Integration:**
- Checkout Session for new subscriptions
- Customer Portal for management
- Webhooks for tier changes

```typescript
// payments/stripe.ts
async function createCheckoutSession(
  tier: 'pro' | 'shop',
  billing: 'monthly' | 'annual'
): Promise<string> {
  const priceId = PRICE_IDS[tier][billing]
  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${BASE_URL}/success`,
    cancel_url: `${BASE_URL}/pricing`,
  })
  return session.url
}
```

**Prices:**
| Tier | Monthly | Annual (20% off) |
|------|---------|------------------|
| Pro | $49 | $39/mo ($468/yr) |
| Shop | $149 | $119/mo ($1,428/yr) |

### 3.3 Project Persistence (Week 3-4)

**Cloud Storage:**
- Free: 5 projects max, local storage
- Pro: Unlimited, cloud sync (S3/Cloudflare R2)
- Shop: Unlimited, shared workspace

```typescript
// projectStore.ts
interface Project {
  id: string
  userId: string
  workspaceId?: string  // Shop tier only
  name: string
  type: 'instrument' | 'rosette' | 'inlay' | 'custom'
  data: ProjectData
  artifacts: Artifact[]
  createdAt: Date
  updatedAt: Date
}
```

### 3.4 Multi-Tenancy (Week 4-6)

**Shop Tier Features:**
- Workspace with up to 10 seats
- Role-based access (Admin, Builder, Operator)
- Shared project library
- Team analytics dashboard

```typescript
// workspaceStore.ts
interface Workspace {
  id: string
  name: string
  ownerId: string
  members: WorkspaceMember[]
  settings: WorkspaceSettings
  subscription: Subscription
}

interface WorkspaceMember {
  userId: string
  role: 'admin' | 'builder' | 'operator'
  invitedAt: Date
  acceptedAt?: Date
}
```

### 3.5 Business Features (Week 6-10)

#### 3.5.1 Quote Generator

```python
# business/quotes/service.py
class QuoteService:
    async def generate_quote(
        self,
        customer_id: str,
        items: List[QuoteItem],
        markup: float = 0.30,
    ) -> Quote:
        # Calculate material costs
        # Calculate labor estimate
        # Apply markup
        # Generate PDF
```

#### 3.5.2 Invoice Manager

```python
# business/invoices/service.py
class InvoiceService:
    async def create_invoice(
        self,
        quote_id: str,
        payment_terms: PaymentTerms = PaymentTerms.NET_30,
    ) -> Invoice:
        # Convert quote to invoice
        # Generate invoice number
        # Send email notification
```

#### 3.5.3 Customer CRM

```python
# business/customers/models.py
class Customer(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    addresses: List[Address]
    orders: List[Order]
    notes: List[Note]
    tags: List[str]
    lifetime_value: float
```

### 3.6 Offline Mode (Week 10-12)

**Service Worker Strategy:**
- Cache core app shell
- Cache user's recent projects
- Queue operations when offline
- Sync when online

```typescript
// sw.ts
const CACHE_NAME = 'production-shop-v1'
const OFFLINE_QUEUE = 'offline-queue'

self.addEventListener('fetch', (event) => {
  if (isApiRequest(event.request)) {
    event.respondWith(networkFirstWithQueue(event.request))
  } else {
    event.respondWith(cacheFirst(event.request))
  }
})
```

---

## Timeline Summary

```
Week 1-2:  Missing routes + Begin guided mode
Week 2-3:  Plain-English errors + Help tooltips
Week 3-4:  Vectorizer polish + Processing tier UI
Week 4-5:  Instrument library completion
Week 5-6:  Authentication integration
Week 6-7:  Payment integration (Stripe)
Week 7-8:  Project persistence (cloud storage)
Week 8-10: Multi-tenancy + Role-based access
Week 10-12: Business features + Offline mode
Week 12+:  Polish, testing, launch
```

---

## Success Metrics

| Metric | Current | Phase 2 Target | Phase 3 Target |
|--------|---------|----------------|----------------|
| Feature coverage | 60% | 90% | 100% |
| Route match (website→app) | 67% | 95% | 100% |
| Beginner task completion | Unknown | 70% | 85% |
| Blueprint accuracy | 92% | 96% | 98% |
| Test coverage | 31% | 50% | 70% |
| Design review score | 7.6/10 | 8.2/10 | 9.0/10 |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Auth integration delays | Medium | High | Use managed service (Clerk) |
| Payment compliance | Low | High | Use Stripe's hosted checkout |
| Offline mode complexity | High | Medium | Start with read-only offline |
| AI costs at scale | Medium | Medium | Cache AI responses, tier limits |
| Feature creep | High | Medium | Strict scope gates per week |

---

## Dependencies

- **External:** Stripe account, Clerk/Auth0 account, S3/R2 bucket
- **Internal:** Blueprint Vectorizer Phase 4 complete (✓), RMOS stability (✓)
- **Team:** Frontend developer, Backend developer, DevOps

---

## Next Actions

1. [ ] Review and approve this plan
2. [ ] Set up Stripe test account
3. [ ] Evaluate Clerk vs Supabase for auth
4. [ ] Begin Week 1: Missing routes implementation
5. [ ] Create sprint board with all tasks

---

*Generated by Claude Code analysis of luthiers-toolbox codebase and website structure.*
