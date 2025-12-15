# MASTER SEGMENTATION STRATEGY  
### Luthier's ToolBox — Multi-Product Ecosystem Blueprint  
Version 1.0 — 2025–2026

---

## 1. PURPOSE OF THIS DOCUMENT
This document unifies:

1. Business motivations for segmentation  
2. Market reasoning and risk mitigation  
3. Pricing and product tier architecture  
4. Technical segmentation plan  
5. Repo strategy and developer handoff  

It represents a complete, top-to-bottom strategy for turning the Luthier's ToolBox into a family of coordinated products, including:

- Express Edition  
- Pro Edition  
- Enterprise Edition  
- Parametric Guitar Designer  
- Neck Designer  
- Headstock Designer  
- Fingerboard Designer  
- Bridge Designer  
- Blueprint Reader / Construction Designer  
- Etsy/Gumroad digital asset packs  

---

## 2. WHY SEGMENTATION IS NEEDED

### 2.1. Market Cloning Threat
The ToolBox contains visually appealing components (rosette designer, curve lab, fretboard tools) that are **the first features unscrupulous competitors or large platforms will clone**.

Your prior experience with Amazon spoofing your 2003–2004 software proves a painful truth:

> **If you don't pre-empt the clones, they will pre-empt you.**

Segmentation protects the brand and creates intentional product "decoys" that soak up clone energy.

---

## 3. THREE CORE EDITIONS

### 3.1. Express Edition (Entry Tier)
- Lightweight  
- Design-focused  
- No CAM, no risk model, no overrides  
- Ideal for players, hobbyists, Etsy buyers  
- Price: **$49** one-time  

### 3.2. Pro Edition (Flagship)
- Full CAM pipeline  
- Post configurator  
- Overrides learning system  
- Jig integration  
- Risk/thermal models  
- Price: **$299–$399**  

### 3.3. Enterprise Edition (Business Suite)
- BOM/COGS  
- Orders, customers  
- Production scheduling  
- E-commerce integrations  
- Multi-machine support  
- Price: **$899–$1299**  

---

## 4. BREAKOUT PRODUCT FAMILY

### 4.1. Parametric Guitar Designer
- Body shape generator  
- Scale-based geometry  
- PDF/DXF/SVG export  
- Price: **$39–$59**  

### 4.2. Neck Designer / Neck 3D Generator
- Fender/Gibson neck profile presets  
- Depth-map based lofting  
- PDF/DXF/SVG/STL output  
- Price: **$29–$49** (templates)  
- Price: **$59–$79** (3D version)  

### 4.3. Headstock Designer
- Tuners layout  
- Angle, thickness, contour  
- Custom outlines  
- Price: **$14–$29**  

### 4.4. Bridge Designer
- Mounting geometry  
- String spacing  
- Footprint templates  
- Price: **$14–$19**  

### 4.5. Fingerboard Designer
- Radius, taper, scale, multiscale  
- Slot positions  
- Price: **$19–$29**  

### 4.6. Blueprint Reader / Construction Designer
- Reads DXF  
- Room/wall/fixture layers  
- For house designs  
- Price: **$29–$49**  

---

## 5. REPO ARCHITECTURE STRATEGY

### 5.1. Golden Repo (Original ToolBox)
- Acts as master source  
- Never used for experiments  
- No AI agents  

### 5.2. Product Repos (Children)
- `ltb-express`  
- `ltb-pro`  
- `ltb-enterprise`  
- `ltb-parametric`  
- `ltb-neck-designer`  
- `ltb-headstock-designer`  
- `ltb-bridge-designer`  
- `ltb-fingerboard-designer`  
- `blueprint-reader`  

### 5.3. Shared Core Layer
- Geometry engine  
- Viewer  
- Import/Export utilities  
- Optional `ltb-core` repo  

---

## 6. FEATURE FLAG SYSTEM

```env
APP_EDITION=EXPRESS | PRO | ENTERPRISE
FEATURE_CAM=true/false
FEATURE_RISK_MODEL=true/false
FEATURE_FINANCIAL=true/false
FEATURE_BLUEPRINT=true/false
FEATURE_CUSTOMER_PORTAL=true/false
```

---

## 7. PRICING STRUCTURE

| Product | Price | Purpose |
|---------|-------|---------|
| Express | $49 | Funnel / anti-clone |
| Pro | $299–$399 | Core revenue |
| Enterprise | $899+ | High-end B2B |
| Parametric Designer | $39–$59 | Etsy/Gumroad |
| Neck Template Pack | $14 | High-volume digital |
| Neck 3D Generator | $59–$79 | Premium digital |
| Headstock Pack | $14–$19 | Add-on |
| Bridge Creator | $14–$19 | Niche digital |
| Fingerboard Creator | $19–$29 | Mid-tier |
| Blueprint Reader | $29–$49 | Cross-market |

---

## 8. EXECUTION TIMELINE (24-WEEK PLAN)

### Q4 2025 (Weeks 1–4)
- Repo segmentation
- Express build
- Parametric Designer MVP

### Q1 2026 (Weeks 5–12)
- Neck / Headstock / Fingerboard / Bridge creators
- Etsy product launch

### Q2 2026 (Weeks 13–24)
- Pro + Enterprise polish
- Installers
- Full launch

---

## 9. INTELLECTUAL PROPERTY FIREWALL

Only Pro/Enterprise retain:
- Overrides learning engine
- CAM pipeline
- Risk/thermal models
- Jig integrations
- Multi-machine scheduler
- Manufacturing presets

---

## 10. STRATEGIC OUTCOME

1. Clones attack Express, not your core.
2. Etsy/Gumroad generate passive revenue.
3. Pro Edition becomes industry standard.
4. Enterprise becomes the "shop OS" for luthiers.

---

## 11. VISUAL DIAGRAMS

### Product Ladder Diagram

```
          ┌──────────────────────────────┐
          │      ENTERPRISE EDITION      │
          │  Orders • COGS • Scheduling  │
          │  E-Commerce • Shop Mgmt      │
          └──────────────┬───────────────┘
                         │
          ┌──────────────┴───────────────┐
          │         PRO EDITION           │
          │  CAM • Overrides • Jigs       │
          │  Risk Model • Pipelines       │
          └──────────────┬───────────────┘
                         │
          ┌──────────────┴───────────────┐
          │        EXPRESS EDITION        │
          │ Design Tools • Viewer • Export│
          └──────────────┬───────────────┘
                         │
     ┌───────────────────┴────────────────────┐
     │   Etsy/Gumroad Spinoffs (Parametric)    │
     │  Neck • Headstock • Bridge • Blueprint  │
     └─────────────────────────────────────────┘
```

### Repo Segmentation Diagram

```
           [ GOLDEN MASTER ]
                    │
     ┌──────────────┼─────────────┬─────────────┐
     │              │             │             │
[ltb-express] [ltb-pro] [ltb-enterprise] [parametric-suite]
     │              │             │             │
Rosette/Curve  CAM/Posts/    Orders/        Neck/Body/
Fretboard      Overrides      COGS       Headstock etc.
```

### IP Protection Wall

```
 EXPRESS     PRO           ENTERPRISE
   │          │                │
   │       ┌──┴────────────────┴──┐
   │       │  PROTECTED CORE IP    │
   │       │ Overrides • CAM • Jigs│
   │       │ Risk Model • Scheduler│
   │       └───────────────────────┘
```

---

## 12. RELATED DOCUMENTS

- [Marketing & Positioning Addendum](./MARKETING_POSITIONING_ADDENDUM.md) - Target audiences, messaging, competitive advantage
- [Founder's Preface](./FOUNDERS_PREFACE.md) - Strategic vision and motivation
- [Product Repo Setup Guide](../../PRODUCT_REPO_SETUP.md) - Technical implementation
- [Canonical Server Stub](../../templates/server/main.py) - FastAPI boilerplate
- [Canonical Client Stub](../../templates/client/App.vue) - Vue 3 boilerplate

---

**Status:** ✅ Strategy Complete  
**Version:** 1.0  
**Last Updated:** December 3, 2025  
**Next Steps:** Phase 1 execution (repo segmentation + Express build)
