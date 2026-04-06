# The Production Shop — Product Tiers

Last updated: 2026-04-06
Maintained by: Ross Echols (HanzoRazer)

---

## Tier Overview

| Tier | Target User | Price | Access Model |
|------|-------------|-------|--------------|
| **Free** | Hobbyist, student, evaluator | $0 | Web-based, rate-limited |
| **Pro** | Professional luthier, small shop | TBD/month | Full access, local install option |
| **Enterprise** | Production facility, school, OEM | TBD/year | Volume licensing, SLA, custom integration |

---

## Competitive Analysis

### Current Market

| Competitor | Price | Strengths | Weaknesses |
|------------|-------|-----------|------------|
| LMI Templates | $15-50/plan | Industry standard, physical templates | No digital, no customization |
| StewMac Plans | $10-30/plan | Trusted brand | Static PDFs, no CAM |
| FretFind | Free | Scale length calculator | No body geometry, no CAM |
| Ekfrasis | €200+ | 3D modeling | Complex, not CNC-focused |
| Generic CAD | $500-2000/yr | Full CAD capability | No lutherie-specific tools |

### Our Position

**Differentiation:** Integrated lutherie-specific CAD/CAM pipeline.
- Blueprint → DXF → G-code in one workflow
- Validated instrument geometry (not generic CAD)
- Physics-based calculators (Helmholtz, P:A ratio, scale length)
- R12 DXF standard for CAM compatibility

---

## Free Tier

### Included Tools

**Calculators (unlimited use):**
- Scale length calculator (standard + multiscale)
- Fret position calculator
- String tension calculator
- Bridge compensation calculator
- Soundhole P:A ratio calculator
- Helmholtz resonance estimator

**Geometry Viewers (read-only):**
- Body outline viewer
- Neck profile viewer
- Headstock template gallery

**Blueprint Reader (limited):**
- 3 extractions per month
- Standard instruments only (Tier 1 catalog)
- Watermarked DXF output

### Rate Limits

| Resource | Free Limit |
|----------|-----------|
| Blueprint extractions | 3/month |
| AI image analysis | 5/month |
| DXF exports | 10/month |
| API calls | 100/day |

### Purpose

- Product discovery and evaluation
- Education and learning
- Hobbyist occasional use
- Funnel to Pro tier

---

## Pro Tier

### Included (everything in Free, plus)

**Blueprint Reader (unlimited):**
- Unlimited extractions
- Full instrument catalog (Tier 1 + Tier 2)
- Clean DXF output (no watermark)
- SVG + DXF + PDF export
- Batch processing (up to 10 files)

**Design Tools:**
- Soundhole designer (round, oval, spiral, f-hole)
- Bridge geometry calculator
- Neck profile designer
- Headstock designer
- Binding/purfling calculator

**CAM Integration:**
- G-code preview
- Machine profile library
- Post-processor selection
- Toolpath simulation (2D)

**Instrument Catalog Access:**
- Full Tier 1 validated catalog (27 instruments)
- Tier 2 community catalog (97+ instruments)
- Custom instrument spec creation

### Pricing Considerations

**Target:** $TBD/month or $TBD/year

**Comparable pricing:**
- Fusion 360 Hobbyist: Free (limited)
- Fusion 360 Commercial: $545/year
- VCarve Desktop: $349 one-time
- Aspire: $1995 one-time

**Value proposition:** Specialized lutherie tools that would require
$500+ in generic CAD software plus manual template purchases.

---

## Enterprise Tier

### Included (everything in Pro, plus)

**Volume Features:**
- Unlimited team seats
- Shared instrument library
- Project management dashboard
- Production tracking integration

**Integration:**
- API access (full rate)
- Webhook notifications
- Custom post-processor development
- ERP/MES integration support

**Support:**
- Dedicated account manager
- SLA guarantee (TBD uptime %)
- Priority bug fixes
- Custom feature development (paid)

### Pricing Considerations

**Target:** $TBD/year minimum contract

**Target customers:**
- Guitar factories (Eastman, Cordoba, Taylor overseas)
- Lutherie schools (Roberto-Venn, Chicago School)
- OEM component suppliers
- Large restoration shops

---

## Free vs Paid Framework

### Principle: Calculators are Free, Workflows are Paid

**Free forever:**
- Physics calculators (Helmholtz, tension, compensation)
- Reference data (scale lengths, standard dimensions)
- Educational content
- Community catalog viewing

**Paid:**
- Geometry generation (DXF output)
- Blueprint extraction (vectorizer)
- CAM integration (G-code)
- Batch operations
- API access beyond limits

### Rationale

Calculators establish authority and trust. They cost nothing to serve
(client-side computation). They bring traffic and backlinks. They
convert to paid when users need actual files for CNC.

---

## Standalone Products (Moat Strategy)

Free standalone tools that establish The Production Shop as the
authoritative source for lutherie calculations:

| Standalone | Description | Status |
|------------|-------------|--------|
| ltb-acoustic-design-studio | Helmholtz + soundhole geometry | Planned |
| ltb-bridge-designer | Bridge geometry + string spacing | Planned |
| ltb-fingerboard-designer | Scale length, radius, multiscale | Planned |
| ltb-headstock-designer | Tuner layout, templates | Planned |
| ltb-neck-designer | Neck profiles, tapers | Planned |
| ltb-parametric-guitar | Body shape generator | Planned |
| ltb-woodworking-studio | Joinery, wood movement | In progress |
| blueprint-reader | PDF → DXF pipeline | Active |

**Strategy:** Free tools with Pro upsell. Each standalone is also
embedded in the main platform for Pro/Enterprise users.

---

## Subscription Infrastructure

**TBD — Options under consideration:**

| Provider | Pros | Cons |
|----------|------|------|
| Stripe | Industry standard, good DX | 2.9% + $0.30 per transaction |
| Paddle | Handles VAT/tax | Higher fees |
| LemonSqueezy | Simple, good for SaaS | Newer, less mature |
| Self-hosted | Full control | Development overhead |

**Decision criteria:**
- International tax handling (VAT, etc.)
- Subscription management UX
- Developer experience
- Cost at scale

---

## Open Questions

1. **Pro tier price point:** $19/mo? $29/mo? $99/year?
2. **Annual discount:** 2 months free? 20% off?
3. **Student/educator discount:** 50% off Pro?
4. **Lifetime deal:** One-time purchase option?
5. **Enterprise minimum:** $1000/year? $5000/year?
6. **Free tier limits:** Too generous? Too restrictive?

---

## Metrics to Track

| Metric | Target |
|--------|--------|
| Free → Pro conversion | 5-10% |
| Pro monthly churn | <5% |
| Annual vs monthly ratio | 60% annual |
| Enterprise contract size | $5000+ avg |
| Time to first paid | <30 days |

---

*This is a living document. Update as pricing experiments complete
and market feedback arrives.*
