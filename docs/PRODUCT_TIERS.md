# The Production Shop — Product Tiers

**Version:** 1.0-draft  
**Status:** Living document — expand as products mature  
**Last updated:** 2026-04-06

---

## Strategic Positioning

The Production Shop competes on three axes where existing tools fail:

```
Luthier Lab     → free, capable, hard to use, Android only
VCarve          → powerful CAM, not luthiery-specific, expensive
Fusion 360      → full parametric, steep learning curve, subscription
Custom scripts  → exist in forums, undocumented, not maintained
```

The Production Shop wins by being:

```
Free tier   → accessible to any maker, anywhere, any skill level
Easy to use → designed around the workflow, not the feature list  
DXF output  → verified R12 that opens in every CAM tool
Physics     → acoustic science built in, not bolted on
Connected   → tools share data, outputs feed inputs
```

---

## Tier Structure

### FREE — Establish Trust

**Who:** Any maker, hobbyist, student, first-time builder  
**Goal:** Demonstrate capability, build trust, generate word of mouth  
**Conversion:** Free users become subscribers when they need more

| Tool | Description | Standalone Repo |
|---|---|---|
| Blueprint Reader | Upload a photo or scan → get a DXF that opens | ltb-blueprint-reader |
| Rosette Designer | Design rosette patterns, BOM, DXF export | ltb-rosette-designer |
| Soundhole Calculator | Helmholtz resonance → recommended soundhole size | ltb-acoustic-design-studio |
| Body Outline Editor | Trace any instrument outline → DXF export | ltb-body-outline-editor |
| Fret Calculator | Scale length → fret positions, saddle compensation | ltb-fingerboard-designer |
| String Tension Calculator | String gauge → tension per string | ltb-express |

**Free tier principles:**
- No account required for basic use
- No ads — ever
- DXF output always R12 verified
- One instrument at a time
- No job history or save state between sessions

---

### PRO — $X/month (TBD)

**Who:** Serious hobbyist, semi-professional builder, small shop  
**Goal:** Recurring revenue from active builders  
**Value:** Tools they use every build, not just occasionally

| Package | Contents | Notes |
|---|---|---|
| Art Studio | Rosette Designer (full) + Headstock Inlay + Fretboard Inlay + Binding Designer + Marquetry Engine | All decorative CAM tools |
| Acoustic Design Studio | Soundhole Calculator + Plate Stiffness + Bracing Calculator + Flexural Rigidity (E×I) + Body Volume Estimator | Physics-first acoustic design |
| CAM Workstation | Toolpath Visualizer + Adaptive pocketing + G-code post processor + Machine profiles | Full CNC workflow |
| RMOS | Risk assessment + Safety gates + Audit trail + Run tracking | Safety-critical CAM |
| Job History | Save sessions, recall previous designs, version history | Persistence across sessions |
| Parametric Guitar | Define body by parameters → mathematically correct outline | Not tracing — pure parametric |

**Pro tier principles:**
- Account required
- Unlimited instruments
- Save and recall all designs
- Job history and audit trail
- Priority email support
- All free tier tools included

---

### ENTERPRISE — Custom Quote

**Who:** Production shop, school, lutherie program, OEM  
**Goal:** High-value contracts, institutional relationships  
**Value:** Multi-user, integration, custom specs, SLA

| Feature | Description |
|---|---|
| Multi-user | Team accounts, role-based permissions |
| Custom instrument specs | Add proprietary instrument families to spec_name catalog |
| API access | Integrate Production Shop tools into existing workflows |
| Shop OS | Inventory, job scheduling, client management, billing |
| Priority support | SLA-guaranteed response times |
| On-premise option | Deploy within shop network (no cloud dependency) |
| Training | Onboarding for shop staff |

---

## Product Packages

### Art Studio
*All decorative and artistic CAM tools under one roof*

```
Rosette Designer          ← exists, live (ltb-rosette-designer)
Headstock Inlay Designer  ← exists in code
Fretboard Inlay Designer  ← exists in code  
Binding Designer          ← exists in code
Marquetry Engine          ← exists in code (5 pattern generators)
Amsterdam/Spiro Engine    ← exists (rope weave rosettes)
```

Free preview: Rosette Designer (ltb-rosette-designer)  
Full package: Pro tier

---

### Acoustic Design Studio
*Physics-first acoustic instrument design*

```
Soundhole Calculator      ← exists (Helmholtz resonance)
Plate Stiffness Tools     ← tap_tone_pi bridge (partial)
Bracing Pattern Calc      ← exists in code
Flexural Rigidity (E×I)   ← Liutalab-equivalent (planned)
Body Volume Estimator     ← planned
```

Free preview: Soundhole Calculator  
Full package: Pro tier  
Related: tap_tone_pi (hardware measurement platform)

---

### CAM Workstation
*From DXF to G-code to machine*

```
Toolpath Visualizer       ← exists in code
Adaptive pocketing        ← exists in code
G-code post processor     ← exists (multiple machine profiles)
RMOS safety system        ← exists (full implementation)
Machine profiles          ← exists (BCAMCNC 2030A validated)
```

Full package: Pro tier  
Note: RMOS is safety-critical infrastructure, not a standalone product

---

### Blueprint Reader
*Analog to digital for any maker*

```
Photo/scan → DXF pipeline ← exists, production-ready
AI render path            ← exists (500× faster)
14 instrument specs       ← exists
Body outline isolation    ← exists
```

Free: unlimited  
Hosted: Hostinger (pending deployment)  
Note: Free intake funnel → Pro conversion path

---

## Competitive Analysis

| Tool | Price | DXF Output | Luthiery-Specific | Physics | Ease of Use |
|---|---|---|---|---|---|
| Luthier Lab | Free | No | Yes | No | Hard |
| VCarve Desktop | $350 one-time | Yes | No | No | Medium |
| Fusion 360 | $545/year | Yes | No | No | Hard |
| **Production Shop Free** | **Free** | **Yes (R12)** | **Yes** | **Partial** | **Easy** |
| **Production Shop Pro** | **TBD** | **Yes (R12)** | **Yes** | **Yes** | **Easy** |

---

## Pricing Considerations (TBD)

Pricing not yet set. Factors to consider:

```
Luthier Lab benchmark    → free (no revenue model)
VCarve Desktop benchmark → $350 one-time
Fusion 360 benchmark     → $545/year hobbyist

Target customer:
  Serious hobbyist builds 2-4 instruments/year
  Small shop builds 10-20 instruments/year

Price sensitivity:
  Hobbyist → $10-20/month acceptable
  Small shop → $50-100/month acceptable
  Enterprise → custom quote, $500+/month

Revenue model options:
  A → Monthly subscription (recurring)
  B → Annual subscription (discounted)
  C → One-time purchase per tool (no recurring)
  D → Freemium with usage limits
  E → Hybrid (free tools + Pro subscription)

Recommendation: Option E
  Free tools drive discovery and trust
  Pro subscription captures recurring value
  Enterprise custom quote for institutional
```

---

## Free vs Paid Decision Framework

A tool belongs in the **free tier** if:

```
✓ It solves a single specific problem
✓ It demonstrates Production Shop quality
✓ It is a natural funnel to paid tools
✓ Competitors offer similar tools for free
✓ Withholding it would push users to competitors
```

A tool belongs in the **paid tier** if:

```
✓ It is used repeatedly across many builds
✓ It requires ongoing maintenance and improvement
✓ It saves significant time or prevents expensive mistakes
✓ It integrates with other paid tools
✓ No free equivalent exists at comparable quality
```

---

## Roadmap Integration

```
NOW (live):
  Blueprint Reader landing page
  ltb-rosette-designer (live)
  ltb-woodworking-studio (content committed)

NEXT (Sprint 2):
  Deploy blueprint-reader to Hostinger
  Populate ltb-acoustic-design-studio
  Define Pro tier pricing

FUTURE:
  Art Studio package page
  Pro tier subscription infrastructure
  Enterprise inquiry page
  Learning Vectorizer (Phase 2-4)
```

---

## Notes

- "Free" means genuinely free — no ads, no data harvesting, no dark patterns
- The Production Shop brand promise: files that actually work
- Every free tool is a proof of that promise
- Luthier Lab has proven the market exists — the opportunity is usability
- The dataset built by testing is a long-term strategic asset

---

*The Production Shop — Design. Build. Track. Deliver.*
