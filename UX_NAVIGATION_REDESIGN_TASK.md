# UX Navigation Redesign Task: Guitar-Centric Information Architecture

**Status:** 📋 Proposed  
**Priority:** High (UX/IA Foundation)  
**Effort:** Medium-Large (3-5 days)  
**Impact:** Reduces learning curve, improves discoverability, aligns UI with real lutherie workflow

---

## 🎯 Problem Statement

The current navigation structure does not reflect the **actual priority and sequence** of guitar construction. Minor decorative features (e.g., rosette design) are given equal or greater prominence than structural fundamentals (e.g., neck joint, bracing), creating cognitive friction for luthiers.

**Current Issues:**
1. **Flat hierarchy** - All features have equal visual weight regardless of importance
2. **No build sequence logic** - Tools are grouped by technical category (Design/Analysis/Utility) rather than construction phase
3. **Feature-first ordering** - Navigation evolved chronologically (features added as built) rather than workflow-optimized
4. **Rosette over-emphasis** - A minor decorative detail appears first in the menu (🌹 Rosette) ahead of body shape, neck, bracing
5. **Steep learning curve** - Users must understand the entire toolset before finding the right tool for their build stage

**User Impact:**
- Luthiers waste time hunting for core tools
- Beginners don't understand the build sequence
- The UI feels "software-centric" rather than "craft-centric"

---

## 🎸 Guitar Build Sequence (Real-World Priority)

### **Phase 1: Body Foundation** (Structure)
1. **Body Outline & Templates** - Shape design, binding channels, neck pocket
2. **Bracing Design** - Top bracing (X-brace, ladder, fan), back bracing
3. **Radius Dish** - Top/back carving radii (archtop, classical)

### **Phase 2: Neck & Fretboard** (Playability)
4. **Neck Profile** - C-shape, V-shape, soft-V, thickness taper
5. **Neck Joint** - Dovetail, mortise-tenon, bolt-on geometry
6. **Fretboard Radius** - Compound radius transitions (12"→16")
7. **Scale Length** - String tension, intonation, multi-scale
8. **Fret Layout** - Slot positions, tang depth, compensation

### **Phase 3: Bridge & Intonation** (Setup)
9. **Bridge Placement** - Scale length reference, body position
10. **Saddle Compensation** - Intonation correction per string
11. **Nut Design** - String spacing, slot depth, break angle

### **Phase 4: Hardware & Electronics** (Function)
12. **Pickup Cavities** - Routing depth, mounting rings, pole spacing
13. **Control Cavities** - Volume/tone pot placement, wiring channels
14. **Jack & Switch** - Output jack location, pickup selector routing
15. **Tuner Holes** - Headstock drilling, bushing fit

### **Phase 5: Decorative Details** (Aesthetics) ⚠️ **Rosette belongs here**
16. **Soundhole Rosette** - Ring patterns, inlay (acoustic only)
17. **Fretboard Inlays** - Position markers, custom designs
18. **Binding & Purfling** - Body edge decoration
19. **Headstock Logo** - V-carve engraving, inlay

### **Phase 6: Finishing** (Protection)
20. **Wood Prep** - Grain filling, sanding schedule
21. **Staining & Burst** - Color design, sunburst patterns
22. **Sealer & Topcoat** - Shellac, nitro, poly, oil finish
23. **Buffing & Polish** - Final surface preparation

---

## 💡 Proposed Solution: Multi-Mode Navigation

### **Option A: Build Workflow Mode** (Beginner-Friendly)
Collapsible accordion navigation showing construction phases:

```
🏗️ Body Foundation
  └─ Body Outline & Templates
  └─ Bracing Calculator
  └─ Radius Dish Designer

🎸 Neck & Fretboard
  └─ Neck Profile Generator
  └─ Fretboard Radius
  └─ Scale Length Designer
  └─ Compound Radius

🌉 Bridge & Setup
  └─ Bridge Calculator
  └─ Nut Design

🔌 Hardware & Electronics
  └─ Hardware Layout
  └─ Wiring Workbench

🎨 Decorative Details      ← Rosette moves here
  └─ Rosette Designer
  └─ Headstock Logo
  └─ Art Studio (relief carving, inlays)

🖌️ Finishing
  └─ Finish Planner
  └─ Finishing Designer

🔧 CAM Operations          ← Advanced users
  └─ CAM Dashboard
  └─ G-code Tools

⚙️ Utilities              ← Power user tools
  └─ DXF Cleaner
  └─ Scientific Calculator
  └─ Export Queue
```

### **Option B: Smart Context Mode** (Adaptive)
Navigation adapts based on:
- **Current project type** - Acoustic (shows rosette), Electric (hides rosette)
- **Build stage** - Body phase shows body tools, Neck phase shows neck tools
- **User experience level** - Beginner (linear), Intermediate (phase-grouped), Expert (all tools)

### **Option C: Dual-Mode Toggle** (Hybrid)
Toggle between:
- **📚 Build Workflow** - Sequential phases (matches real construction)
- **🔧 All Tools** - Alphabetical/categorical (power users who know what they want)

---

## 🎯 Success Metrics

### **Quantitative:**
- **Time-to-tool** - Reduce average clicks from 3.2 → 1.8 (user testing)
- **Navigation depth** - Flatten from 4 levels → 2 levels max
- **Task completion rate** - Increase from 68% → 90% for "find tool for [build task]"

### **Qualitative:**
- **Cognitive load** - "The menu makes sense for how I actually build guitars"
- **Discoverability** - "I found tools I didn't know existed"
- **Confidence** - "I understand where I am in the build process"

---

## 📐 Design Principles

### **1. Craft-First, Not Software-First**
- Use **lutherie terminology** (e.g., "Setup" not "Analysis Tools")
- Show **build context** (e.g., "You're working on the neck phase")
- Provide **workflow hints** (e.g., "Next: Install frets")

### **2. Progressive Disclosure**
- **Beginners** - Show only current phase tools
- **Intermediate** - Show current + adjacent phases
- **Expert** - Show all tools with quick search

### **3. Context-Aware Defaults**
- **Acoustic project** - Rosette, bracing, soundhole visible
- **Electric project** - Electronics, pickups, neck joint prominent
- **Archtop project** - Carving, f-holes, floating bridge highlighted

### **4. Flexible Access Patterns**
- **Sequential** - Step-by-step wizard for complete builds
- **Random access** - Jump to any tool (expert mode)
- **Search-first** - Fuzzy search for "I need to route pickup cavities"

---

## 🛠️ Implementation Plan

### **Phase 1: Research & Validation** (1 day)
- [x] Document current navigation issues (this doc)
- [ ] User interview with 3-5 luthiers (build sequence, tool usage patterns)
- [ ] Analyze usage telemetry (if available) - most/least used tools
- [ ] Competitive analysis (StewMac, Crimson Guitars, Luthiers Mercantile site navigation)

### **Phase 2: IA Redesign** (1 day)
- [ ] Create sitemap showing new hierarchy
- [ ] Wireframe 3 navigation concepts (Option A/B/C above)
- [ ] User preference survey - which mode resonates?
- [ ] Define metadata schema (tool → phase, project_type, experience_level)

### **Phase 3: UI Prototyping** (1 day)
- [ ] Build clickable prototype in Figma/Penpot
- [ ] Test with 2-3 luthiers (think-aloud protocol)
- [ ] Iterate based on feedback
- [ ] Finalize chosen navigation pattern

### **Phase 4: Frontend Implementation** (2-3 days)
- [ ] Refactor `App.vue` navigation structure
- [ ] Create `BuildPhaseNav.vue` component
- [ ] Add phase metadata to all tool components
- [ ] Implement mode toggle (if hybrid approach chosen)
- [ ] Add search/filter functionality
- [ ] Mobile responsive breakpoints

### **Phase 5: Testing & Refinement** (1 day)
- [ ] Usability testing with 5 users (mixed experience levels)
- [ ] A/B test old vs. new navigation (if possible)
- [ ] Gather feedback and iterate
- [ ] Document navigation patterns for future tools

---

## 📊 Tool Categorization Matrix

| Tool Name | Current Category | Build Phase | Priority | Project Type | Experience Level |
|-----------|------------------|-------------|----------|--------------|------------------|
| Body Outline | (missing) | Body Foundation | Critical | All | Beginner |
| Bracing Calculator | Design | Body Foundation | Critical | Acoustic/Archtop | Intermediate |
| Neck Generator | Design | Neck & Fretboard | Critical | All | Beginner |
| Bridge Calculator | Design | Bridge & Setup | Critical | All | Beginner |
| Scale Length Designer | Planning | Neck & Fretboard | Critical | All | Beginner |
| Fretboard Radius | Design | Neck & Fretboard | High | All | Beginner |
| Compound Radius | Design | Neck & Fretboard | Medium | All | Intermediate |
| Hardware Layout | Design | Hardware & Electronics | High | Electric | Beginner |
| Wiring Workbench | Design | Hardware & Electronics | High | Electric | Intermediate |
| **Rosette Designer** | **Design (1st)** | **Decorative Details** | **Low** | **Acoustic only** | **Intermediate** |
| Archtop Calculator | Design | Body Foundation | Medium | Archtop only | Advanced |
| Radius Dish | Design | Body Foundation | Medium | Acoustic/Archtop | Intermediate |
| Finish Planner | Analysis | Finishing | Medium | All | Beginner |
| Finishing Designer | Planning | Finishing | Medium | All | Intermediate |
| DXF Cleaner | Utility | (cross-phase) | Low | All | Advanced |
| G-code Explainer | Analysis | (cross-phase) | Low | All | Advanced |
| CAM Dashboard | CAM | (cross-phase) | High | All | Advanced |
| Art Studio | CAM | Decorative Details | Medium | All | Intermediate |

**Key Insights:**
- Rosette is **Low Priority, Acoustic-Only, Decorative Phase** - should not be first
- Neck/Bridge/Bracing are **Critical Priority, All Projects, Foundation Phase** - should be prominent
- Most tools are **Beginner-friendly** except CAM/DXF tools (Advanced)

---

## 🚀 Quick Win: Immediate Improvements (< 1 hour)

While full redesign is in progress, these can be done now:

1. **Reorder existing flat menu** to match build sequence:
```javascript
const views = [
  // Body Foundation
  { id: 'bracing', label: '🏗️ Bracing', category: 'body' },
  { id: 'radius', label: '📏 Radius Dish', category: 'body' },
  { id: 'archtop', label: '🎻 Archtop', category: 'body' },
  
  // Neck & Fretboard
  { id: 'neck', label: '🎸 Neck Gen', category: 'neck' },
  { id: 'scale-length', label: '📏 Scale Length', category: 'neck' },
  { id: 'compound-radius', label: '📐 Compound Radius', category: 'neck' },
  
  // Bridge & Setup
  { id: 'bridge', label: '🌉 Bridge', category: 'setup' },
  
  // Hardware & Electronics
  { id: 'hardware', label: '🔌 Hardware', category: 'electronics' },
  { id: 'wiring', label: '⚡ Wiring', category: 'electronics' },
  
  // Decorative Details (Rosette moves here ↓)
  { id: 'rosette', label: '🌹 Rosette', category: 'decorative' },
  
  // ... rest of tools
]
```

2. **Add visual separators** between phases (CSS border-top)

3. **Update welcome screen** to show build sequence, not feature categories

---

## 🎨 Visual Design Notes

### **Phase Indicator Colors** (optional visual aid)
- 🟦 **Body Foundation** - Blue (structural, foundational)
- 🟩 **Neck & Fretboard** - Green (playability, organic)
- 🟨 **Bridge & Setup** - Yellow (precision, tuning)
- 🟧 **Hardware & Electronics** - Orange (functional, technical)
- 🟪 **Decorative Details** - Purple (aesthetic, artistic) ← Rosette here
- 🟫 **Finishing** - Brown (wood, natural)
- ⚫ **CAM/Utilities** - Gray (tools, advanced)

### **Iconography**
- Use **phase icons** in addition to tool icons
- Example: 🏗️ (foundation) + 🌹 (rosette) = "Decorative rosette in body phase"

---

## 📚 References & Inspiration

### **Lutherie Workflow Sources:**
- *Guitarmaking: Tradition and Technology* by Cumpiano & Natelson (standard build sequence)
- StewMac YouTube series (order of operations)
- Crimson Guitars build along series (real-world progression)

### **IA Best Practices:**
- *Information Architecture for the Web and Beyond* (4th ed.) - Rosenfeld, Morville, Arango
- Nielsen Norman Group: "Category Organization" patterns
- Apple Human Interface Guidelines: Progressive Disclosure

### **Similar Tool Navigation:**
- **Fusion 360** - Workspace modes (Design/CAM/Simulation)
- **SketchUp** - Tool palettes by task
- **Blender** - Mode switching (Edit/Sculpt/Shading)

---

## ✅ Definition of Done

- [ ] New navigation structure implemented and tested
- [ ] All tools correctly categorized by build phase
- [ ] Rosette moved to "Decorative Details" section (not prominent)
- [ ] User testing shows improved time-to-tool metrics
- [ ] Documentation updated with navigation patterns
- [ ] Mobile responsive navigation tested on 3 screen sizes
- [ ] Accessibility audit passed (keyboard nav, screen readers)

---

## 💬 Discussion Notes

**2025-11-19**: Initial observation from user - "Rosette graphic showing up as placeholder in places it didn't belong. AI over-emphasized the rosette when it's actually a minor feature of guitar build. It's a source of customization and creativity but only a small afterthought as far as construction. Labels and functions need to be more guitaristic so the menu is not a steep learning curve."

**Key Insight**: This is not a bug in one component - it's a **systemic UX problem** where the navigation hierarchy doesn't reflect real-world lutherie priorities. The solution requires rethinking the entire IA from a craft-centric perspective.

---

**Next Steps:** Schedule user research sessions to validate build sequence assumptions and gather feedback on proposed navigation concepts.
