# Knowledge Base

Central repository for technical theory, references, and formulas that underpin the Luthier's Tool Box calculations.

## Purpose

This knowledge base ensures that:
1. Critical formulas and algorithms are documented, not just in code
2. External references (papers, vendor specs, lutherie books) are tracked
3. New developers can understand the "why" behind calculations
4. Magic numbers have explanations

## Directory Structure

```
KnowledgeBase/
├── README.md                           # This file
├── Instrument_Geometry/
│   ├── Fret_Scale_Theory.md           # 12th root of 2, equal temperament
│   ├── Bridge_Compensation_Notes.md    # Intonation, saddle setback
│   ├── Radius_Theory_Compound.md       # Fretboard radius math
│   └── Fretboard_Geometry.md          # Outline, taper, widths
├── Saw_Physics/
│   ├── Saw_Blade_Geometry_Reference.md # Kerf, hook angle, tooth geometry
│   └── Vendor_Blade_Physics_Notes.md   # Manufacturer specifications
├── Materials/
│   ├── Wood_Properties_Tables.md       # Density, hardness, heat sensitivity
│   └── Tonewoods_Reference.md          # Species-specific properties
└── CAM/
    ├── Feeds_Speeds_Theory.md          # Chipload, SFM, MRR
    └── Toolpath_Strategies.md          # Climb vs conventional, etc.
```

## Code ↔ Knowledge Linking

Each calculator module should reference its knowledge base document:

```python
# scale_length.py
"""
Instrument Geometry: Scale Length & Fret Positions

See docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md
for derivations, references, and assumptions.
"""
```

And knowledge base documents should reference the implementing code:

```markdown
## Implementation

- `services/api/app/instrument_geometry/scale_length.py`
```

## Adding New Documents

When you discover valuable technical information:

1. **Save the source** (PDF, link, etc.) in the appropriate directory
2. **Create a summary markdown** with:
   - Key formulas and their meaning
   - References and citations
   - Assumptions and limitations
   - Implementation notes
3. **Link to the code** that uses these formulas
4. **Update the calculator module** with a reference comment

## References Format

Use consistent citation format:

```markdown
## References

1. Cumpiano, W. & Natelson, J. (1993). *Guitar Making: Tradition and Technology*. Chronicle Books.
2. Stewart-MacDonald. "Fret Scale Template Calculator." [online] Available at: https://www.stewmac.com/
3. Liutaio Mottola. "Fret Spacing Calculator." [online] Available at: https://www.liutaiomottola.com/formulae/fret.htm
```
