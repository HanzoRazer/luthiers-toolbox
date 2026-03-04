# Instrument Designs Showcase Plan

**Date:** March 3, 2026
**Purpose:** Bring hidden instrument designs out of the codebase and onto the marketing website
**Status:** Planning Phase

---

## 🎸 What We Found

### Instrument Model Registry Location
```
services/api/app/instrument_geometry/instrument_model_registry.json
```

### Summary of Hidden Treasure

**Total Instruments:** 20+ guitar/instrument models
**Status Breakdown:**
- ✅ **COMPLETE** (2): Smart Guitar, Benedetto 17" Archtop
- ⚙️ **ASSETS_ONLY** (4): Flying V, J-200 Jumbo, Gibson L-00, Ukulele
- 📝 **STUB** (15+): Most classic designs (metadata only)

---

## 📊 Complete Instrument Inventory

### Electric Guitars (11 models)

| Model | Manufacturer | Status | Scale | Assets |
|-------|-------------|--------|-------|--------|
| **Smart Guitar** | Luthier's ToolBox | ✅ COMPLETE | 25.5" | 4 DXF files + full IoT spec |
| Stratocaster | Fender | STUB | 25.5" | None |
| Telecaster | Fender | STUB | 25.5" | None |
| Les Paul | Gibson | STUB | 24.75" | None |
| SG | Gibson | STUB | 24.75" | None |
| ES-335 | Gibson | STUB | 24.75" | None |
| **Flying V** | Gibson | ASSETS_ONLY | 24.75" | 3 DWG files (58/59/83 models) |
| Explorer | Gibson | STUB | 24.75" | None |
| Firebird | Gibson | STUB | 24.75" | None |
| Moderne | Gibson | STUB | 24.75" | None |
| PRS Custom 24 | PRS | STUB | 25" | None |

### Acoustic Guitars (6 models)

| Model | Category | Status | Scale | Assets |
|-------|----------|--------|-------|--------|
| Dreadnought | Martin D-28 style | STUB | 25.4" | None |
| OM/000 | Orchestra Model | STUB | 25.4" | None |
| J-45 | Round-shoulder dread | STUB | 24.75" | None |
| **J-200 Jumbo** | Super Jumbo | ASSETS_ONLY | 25.4" | 1 PDF plan |
| **Gibson L-00** | Small-body | ASSETS_ONLY | 24.75" | 1 PDF plan |
| Classical | Nylon-string | STUB | 25.6" | None |

### Archtop Jazz Guitars (3 variants)

| Model | Status | Size | Assets |
|-------|--------|------|--------|
| **Benedetto 17"** | ✅ COMPLETE | 17" | 3 files (body, f-holes, graduation map) |
| Gibson L-5 | STUB | 16" | None |
| Gibson Super 400 | STUB | 18" | None |

### Bass & Other (2 models)

| Model | Category | Status | Scale | Assets |
|-------|----------|--------|-------|--------|
| Jazz Bass | Fender 4-string | STUB | 34" | None |
| **Soprano Ukulele** | Hawaiian | ASSETS_ONLY | 13" | 3 DXF files |

---

## 🌟 Showcase Priority: The Smart Guitar

### Why Lead with Smart Guitar?

**Status:** ✅ **COMPLETE** - Only fully-implemented instrument design
**Unique Selling Point:** IoT-enabled electric guitar with embedded computing

### Smart Guitar Specifications

#### Hardware
- **Processor:** Raspberry Pi 5 (8GB RAM, 64GB storage)
- **OS:** Linux (custom Buildroot)
- **Connectivity:** BLE 5.0, Wi-Fi 6, USB-C 3.1, MIDI (USB/BLE/DIN)
- **Audio:** 24-bit/96kHz ADC, 3ms latency, real-time DSP
- **Sensors:** 6 piezo pickups, accelerometer, gyroscope, capacitive touch frets
- **Power:** Li-ion 18650 (6000mAh), 8hr runtime, USB-C PD charging

#### Software Features
- Real-time pitch detection
- 19+ alternative temperament systems
- RGB LED fret markers
- Onboard effects processing
- DAW integration (Giglad, Band-in-a-Box)
- Chord recognition
- 60s stereo looper
- Metronome with tap tempo
- Chromatic + temperament-aware tuner
- Wireless audio streaming (A2DP)
- MIDI controller mode
- OTA firmware updates

#### CAM/Manufacturing Features
- Custom electronics cavity for Pi 5 + battery
- 3D printed or CNC aluminum control panel
- PCB mounting with M2.5 standoffs, vibration dampened
- **Design Files:** 4 DXF files available
  - `smart_guitar/body_outline.dxf`
  - `smart_guitar/electronics_cavity.dxf`
  - `smart_guitar/control_panel.dxf`
  - `smart_guitar/pcb_mounting.dxf`

#### Commercial Partnerships
- **Giglad:** OEM partnership for live backing tracks + AI accompaniment
- **PG Music:** OEM partnership for Band-in-a-Box integration + chord recognition

---

## 🎯 Website Integration Strategy

### Phase 1: Quick Win - Add Instruments Page (1-2 days)

**Create new page:** `instruments.html`

**Content Structure:**
```
┌─────────────────────────────────────────────────┐
│  HEADER: "Instrument Designs"                   │
│  Tagline: "From classic shapes to cutting-edge  │
│           innovation"                            │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  HERO SECTION: Smart Guitar                     │
│  - Large hero image/render                      │
│  - "IoT-Enabled Electric Guitar"                │
│  - Key specs in callout boxes                   │
│  - "View Design Files" CTA                      │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  SECTION: Instrument Library                    │
│  - Tabs: Electric | Acoustic | Archtop | Other  │
│  - Grid of instrument cards                     │
│  - Badge: COMPLETE | ASSETS | COMING SOON       │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  SECTION: Parametric Templates                  │
│  - Customizable guitar designs                  │
│  - Stratocaster, Telecaster, Les Paul, etc.     │
│  - "Try the Designer" CTAs                      │
└─────────────────────────────────────────────────┘
```

**Update navigation:**
```html
Home | Features | Instruments | Pricing | About | Contact
                      ^
                    NEW!
```

---

### Phase 2: Individual Instrument Pages (1 week)

**Create detailed pages for COMPLETE instruments:**

#### `/instruments/smart-guitar.html`
**Sections:**
1. **Hero** - Glamour shot of guitar
2. **Overview** - What makes it unique
3. **Hardware Specs** - Table of components
4. **Software Features** - Feature grid with icons
5. **CAM Integration** - How to manufacture it
6. **Design Files** - Download DXF files
7. **Build Gallery** - Community builds (if available)
8. **Partnerships** - Giglad, PG Music logos
9. **Get Started** - "Build Your Own" CTA

#### `/instruments/benedetto-archtop.html`
**Sections:**
1. **Heritage** - Robert Benedetto history
2. **Specifications** - 17" body, dimensions
3. **Carved Top Details** - Graduation map
4. **F-Hole Design** - Precision templates
5. **Design Files** - DXF downloads
6. **Build Guide** - Link to tutorials

---

### Phase 3: Instrument Gallery Component (2-3 days)

**Reusable component for all pages**

**Instrument Card Design:**
```
┌─────────────────────────────┐
│  [Image/Icon]               │
│                             │
│  Fender Stratocaster        │
│  25.5" Scale | 22 Frets     │
│                             │
│  [COMING SOON badge]        │
│                             │
│  [ Learn More ]             │
└─────────────────────────────┘
```

**Status Badges:**
- 🟢 **READY** (COMPLETE) - Green badge, "Download Design Files"
- 🟡 **AVAILABLE** (ASSETS_ONLY) - Yellow badge, "View Plans"
- 🔵 **COMING SOON** (STUB) - Blue badge, "Notify Me"

---

### Phase 4: Interactive Features (Future)

**Design File Viewer:**
- Inline DXF preview using libraries like `dxf-viewer.js`
- Pan/zoom/measure tools
- Layer visibility toggles
- Export to PNG/PDF

**Parametric Designer:**
- Live sliders for body dimensions
- Real-time preview updates
- Export customized DXF
- "Save to My Designs" (requires login)

**Build Gallery:**
- User-submitted photos of completed instruments
- Tag by model (e.g., #SmartGuitar, #Benedetto)
- Upvote/comment system
- "Featured Build of the Month"

---

## 📝 Content Strategy

### Home Page Updates

**Add new hero section:**
```
"Design, Build, and Innovate"
- 20+ Classic Guitar Designs
- IoT-Enabled Smart Guitar
- Parametric Templates
- Download Production-Ready CAD Files
```

**Add instrument showcase section:**
```
Featured Instrument: Smart Guitar
[Hero image] [Specs callout] [Learn More →]
```

---

### Features Page Updates

**Add to Design Tab:**
- ✅ Guitar Dimensions (already there)
- 🆕 **Instrument Library** - 20+ classic designs
- 🆕 **Parametric Templates** - Editable constraints
- 🆕 **Smart Guitar Designer** - IoT customization

**New feature card:**
```
┌─────────────────────────────────────┐
│  📐 Instrument Library              │
│                                     │
│  Access 20+ classic guitar designs  │
│  including Stratocaster, Les Paul,  │
│  Telecaster, and more. Download     │
│  production-ready DXF files or      │
│  customize with parametric          │
│  constraints.                       │
│                                     │
│  [ Try it → ]                       │
└─────────────────────────────────────┘
```

---

### Pricing Page Updates

**Add to Free Tier:**
- ✅ Access to 5 classic instrument designs
- ✅ Basic DXF export

**Add to Pro Tier ($49/mo):**
- ✅ Access to all 20+ instrument designs
- ✅ Parametric template editor
- ✅ Smart Guitar design files

**Add to Shop Tier ($149/mo):**
- ✅ Full instrument library
- ✅ Custom design consultation
- ✅ Priority support for builds

---

## 🎨 Visual Assets Needed

### Smart Guitar
**Priority: HIGH**
- [ ] Hero image (render or photo)
- [ ] Component diagram (exploded view)
- [ ] PCB layout visualization
- [ ] Electronics cavity 3D render
- [ ] LED fret marker demo
- [ ] Control panel mockup

### Classic Instruments
**Priority: MEDIUM**
- [ ] Silhouette icons for each model (20+)
- [ ] Body outline previews (DXF → SVG)
- [ ] Scale/dimension diagrams
- [ ] Manufacturer logos (Fender, Gibson, Martin, PRS)

### Archtop Series
**Priority: MEDIUM**
- [ ] Benedetto 17" render
- [ ] F-hole detail closeup
- [ ] Graduation map visualization
- [ ] Carved top cross-section

### UI Elements
**Priority: LOW**
- [ ] Status badge designs (Complete/Assets/Coming Soon)
- [ ] Download icons
- [ ] File type icons (DXF, DWG, PDF, SVG)

---

## 🚀 Implementation Roadmap

### Week 1: Foundation
**Days 1-2:**
- [ ] Create `instruments.html` page
- [ ] Design instrument card component
- [ ] Add Smart Guitar hero section
- [ ] Update navigation links

**Days 3-5:**
- [ ] Build instrument grid (4 tabs: Electric/Acoustic/Archtop/Other)
- [ ] Implement status badges
- [ ] Add filter/search functionality
- [ ] Write copy for each instrument

**Days 6-7:**
- [ ] Create Smart Guitar detail page
- [ ] Add DXF download links
- [ ] Write technical documentation
- [ ] QA and responsive testing

### Week 2: Enhancements
**Days 8-10:**
- [ ] Create Benedetto Archtop page
- [ ] Add parametric templates showcase
- [ ] Update Features page with new cards
- [ ] Update Pricing page with instrument access

**Days 11-12:**
- [ ] Gather/create visual assets
- [ ] Add instrument preview images
- [ ] Create component diagrams
- [ ] Design Smart Guitar renders

**Days 13-14:**
- [ ] SEO optimization (meta tags, structured data)
- [ ] Analytics tracking setup
- [ ] Final QA pass
- [ ] Deployment preparation

### Week 3+: Expansion
- [ ] Build individual pages for ASSETS_ONLY instruments
- [ ] Add DXF inline preview
- [ ] Implement parametric designer interface
- [ ] Create build gallery
- [ ] Add "Request a Design" form

---

## 📊 Success Metrics

### Website Analytics (30 days post-launch)
- **Page Views:** Track `/instruments.html` traffic
- **Engagement:** Time on page, scroll depth
- **Downloads:** Track DXF file downloads
- **Conversion:** Instrument page → Signup rate

### User Behavior
- **Most Viewed Instruments:** Which designs get most clicks?
- **Search Terms:** What are users looking for?
- **Status Badge Clicks:** Interest in STUB vs COMPLETE designs
- **External Links:** Clicks to design file downloads

### Business Impact
- **Lead Generation:** Contact form submissions mentioning instruments
- **Trial Signups:** Users signing up after visiting `/instruments`
- **Upgrade Conversions:** Free → Pro for instrument library access
- **Partnership Inquiries:** Interest in Smart Guitar (Giglad/PG Music style)

---

## 🎯 Quick Wins (Can Do Today)

### 1. Add Instruments Link to Navigation (15 min)
```html
<!-- All 5 pages -->
<li><a href="instruments.html">Instruments</a></li>
```

### 2. Create Simple Instruments Landing Page (2 hours)
```html
<!-- instruments.html -->
<h1>Instrument Designs</h1>
<p>Access 20+ classic guitar designs and our revolutionary Smart Guitar</p>
<div class="instrument-grid">
  <!-- 3-4 featured instruments with cards -->
</div>
```

### 3. Add Smart Guitar Callout to Home Page (1 hour)
```html
<!-- index.html - new section -->
<section class="smart-guitar-promo">
  <h2>Introducing the Smart Guitar</h2>
  <p>IoT-enabled electric guitar with embedded computing</p>
  <a href="instruments/smart-guitar.html">Learn More →</a>
</section>
```

### 4. Update Features Page (30 min)
Add "Instrument Library" feature card to Design tab

---

## 📋 Open Questions

1. **Design File Licensing:**
   - Can we legally share DXF files for Flying V (Gibson trademark)?
   - Need permission for Fender/Gibson/Martin shapes?
   - Smart Guitar is original - safe to publish

2. **Visual Assets:**
   - Do we have photos/renders of Smart Guitar?
   - Can we generate preview images from DXF files?
   - Need to source instrument photos (stock vs custom)

3. **Pricing Access:**
   - Should Free tier have ANY instrument access?
   - Which instruments in Pro vs Shop tier?
   - Smart Guitar files - Pro or Shop only?

4. **Build Gallery:**
   - Do we have user builds to showcase?
   - Legal considerations for user-submitted photos?
   - Moderation workflow?

---

## 🎁 Bonus Ideas

### Smart Guitar Marketing Campaign
- "Build the Future of Music" tagline
- Partnership announcement with Giglad/PG Music
- Developer documentation for IoT integration
- Maker/hacker community outreach (Hackster.io, Hackaday)

### Instrument-of-the-Month
- Featured instrument rotates monthly
- Deep dive blog post
- Video tutorial on manufacturing
- Community challenge: "Build this month's design"

### CAD File Marketplace
- User-submitted custom designs
- Revenue share model (70/30 split)
- Quality review process
- Featured designer program

---

## 📝 Next Actions

**Immediate (This Week):**
1. ✅ Document website review → DONE
2. ✅ Find instrument designs → DONE
3. ✅ Create showcase plan → DONE
4. ⏳ Create `instruments.html` skeleton
5. ⏳ Design instrument card component
6. ⏳ Add Smart Guitar hero section

**This Month:**
1. Complete Week 1 roadmap tasks
2. Source/create visual assets
3. Write technical documentation
4. Deploy instruments page

**Future:**
1. Build individual instrument pages
2. Add DXF preview functionality
3. Create parametric designer
4. Launch build gallery

---

**Document Version:** 1.0
**Last Updated:** March 3, 2026
**Next Review:** After Phase 1 completion
