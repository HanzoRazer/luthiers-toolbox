# Fender Stratocaster CNC Machining Guide

**Generated:** December 12, 2025  
**Source Files:** Fender_Stratocaster_Project.zip

---

## Overview

This package contains G-code toolpaths for a complete Stratocaster build:

| Component | File | Lines | Operations |
|-----------|------|-------|------------|
| Body (Top) | `STRAT_BODY_TOP.nc` | 12,354 | Pickup cavities, control route, contours |
| Body (Bottom) | `STRAT_BODY_BOTTOM.nc` | 18,025 | Tremolo spring cavity, contours |
| Neck | `STRAT_NECK.nc` | 5,680 | Profile, headstock |
| Fretboard | `STRAT_FRETBOARD.nc` | 6,474 | Perimeter, radius prep |
| Pickguard | `STRAT_PICKGUARD.nc` | 4,674 | Perimeter, screw holes |
| Trem Cover | `STRAT_TREM_COVER.nc` | 219 | Perimeter cut |

---

## Material Requirements

### Body Blank
- **Size:** 355mm × 460mm × 45mm (14" × 18" × 1.75")
- **Species:** Alder (traditional) or Ash (70s style)
- **Grain:** Book-matched 2-piece or solid slab

### Neck Blank  
- **Size:** 700mm × 100mm × 25mm (27.5" × 4" × 1")
- **Species:** Maple (quartersawn preferred)
- **Note:** Add headstock wings for angled headstock

### Fretboard
- **Size:** 500mm × 65mm × 6.5mm (20" × 2.5" × 0.25")
- **Species:** Rosewood, Ebony, or Maple
- **Radius:** 9.5" (241mm) - sand to radius after CNC

### Pickguard
- **Size:** 300mm × 200mm × 2.8mm
- **Material:** 3-ply celluloid or PVC

### Tremolo Cover
- **Size:** 160mm × 100mm × 2.5mm
- **Material:** Matching pickguard material

---

## Tooling Required

### Endmills
| Tool | Diameter | Use |
|------|----------|-----|
| 1/4" Flat Endmill | 6.35mm | Body/Neck perimeter, pockets |
| 1/8" Flat Endmill | 3.175mm | Pickguard, fine details |
| 1/4" Ball Endmill | 6.35mm | Contour carving (optional) |

### Drill Bits
| Tool | Diameter | Use |
|------|----------|-----|
| #30 Drill | 3.0mm | Screw pilot holes |
| 1/8" Drill | 3.175mm | String ferrule holes |

### Specialty
| Tool | Size | Use |
|------|------|-----|
| Fret Slotting Saw | 0.023" (0.584mm) | Fret slots (separate operation) |

---

## Machining Parameters

### Body (Alder/Ash @ 18,000 RPM)
| Operation | Feed | Plunge | Depth/Pass |
|-----------|------|--------|------------|
| Perimeter | 2000 mm/min | 500 mm/min | 6.0mm |
| Pockets | 2500 mm/min | 600 mm/min | 4.0mm |
| Drilling | 1000 mm/min | 300 mm/min | 3.0mm peck |

### Neck (Maple @ 16,000 RPM)
| Operation | Feed | Plunge | Depth/Pass |
|-----------|------|--------|------------|
| Perimeter | 1800 mm/min | 400 mm/min | 4.0mm |

### Fretboard (Rosewood @ 18,000 RPM)
| Operation | Feed | Plunge | Depth/Pass |
|-----------|------|--------|------------|
| Perimeter | 1500 mm/min | 300 mm/min | 2.0mm |

### Pickguard (Plastic @ 12,000 RPM)
| Operation | Feed | Plunge | Depth/Pass |
|-----------|------|--------|------------|
| Perimeter | 2000 mm/min | 500 mm/min | 1.5mm |

---

## Operation Sequence

### 1. Body - Top Side
1. Secure blank to spoilboard (double-sided tape + screws in waste)
2. Zero X/Y to body centerline
3. Zero Z to material surface
4. Run `STRAT_BODY_TOP.nc`
   - Pickup cavities (3 single-coil routes)
   - Control cavity
   - Neck pocket
   - Bridge mounting holes
   - Pickguard screw holes

### 2. Body - Bottom Side  
1. **CRITICAL:** Flip body using registration pins
2. Re-zero Z to new surface
3. Run `STRAT_BODY_BOTTOM.nc`
   - Tremolo spring cavity
   - Wiring channel
   - Contour cuts (belly/arm)

### 3. Neck
1. Secure maple blank
2. Run `STRAT_NECK.nc`
3. **Manual follow-up required:**
   - Truss rod channel (router/chisel)
   - Headstock angle (if using tilt-back)
   - Profile carving (templates + spokeshave)

### 4. Fretboard
1. Secure fretboard blank
2. Run `STRAT_FRETBOARD.nc`
3. **Manual follow-up:**
   - Sand radius (9.5" radius block)
   - Cut fret slots (table saw with slitting blade or manual)
   - Inlay work (if applicable)

### 5. Pickguard
1. Secure plastic with sacrificial backing
2. Run `STRAT_PICKGUARD.nc`
3. Deburr edges with scraper

### 6. Tremolo Cover
1. Run `STRAT_TREM_COVER.nc`
2. Match-drill mounting holes to body

---

## Critical Notes

### Workholding
- **Body:** Use vacuum table or strategic screws in waste areas
- **Add tabs:** The G-code marks where tabs should go for cutouts
- **Flip alignment:** Use dowel pins for precise 2-sided registration

### Depth Verification
Before running, verify these critical depths match your hardware:

| Feature | Generated Depth | Verify Against |
|---------|-----------------|----------------|
| Pickup cavity | 19.0mm | Your pickup height |
| Control cavity | 38.0mm | Pot shaft length |
| Neck pocket | 16.0mm | Neck heel thickness |
| Trem spring cavity | 40.0mm | Spring claw depth |

### Feed Rate Adjustment
These feeds are conservative for hardwood. Adjust based on:
- Your machine rigidity
- Actual material hardness
- Tool sharpness
- Chip load preferences

---

## Post-Processing Checklist

- [ ] Sand all CNC'd surfaces (120 → 220 → 320 grit)
- [ ] Round over edges where appropriate
- [ ] Route binding channels (if using binding)
- [ ] Drill string-through holes (if hardtail)
- [ ] Final fit neck to pocket
- [ ] Test-fit all hardware before finishing

---

## Files Included

```
gcode/
├── STRAT_BODY_TOP.nc      # Body front operations
├── STRAT_BODY_BOTTOM.nc   # Body back operations  
├── STRAT_NECK.nc          # Neck profile
├── STRAT_FRETBOARD.nc     # Fretboard perimeter
├── STRAT_PICKGUARD.nc     # Pickguard + holes
└── STRAT_TREM_COVER.nc    # Back plate
```

---

*Generated for Luthier's ToolBox project*
