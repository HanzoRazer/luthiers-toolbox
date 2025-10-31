# Luthier's Toolbox Documentation

## Overview

The Luthier's Toolbox is a comprehensive parametric CAD/CAM suite designed specifically for guitar makers, CNC operators, and digital craftsmen. It bridges the gap between traditional luthiery and modern digital fabrication.

## Key Features

### 🎸 CAD Module
- Parametric guitar body design (Stratocaster, Telecaster, Les Paul, and custom shapes)
- Precision neck design with configurable profiles (C, D, V, U shapes)
- Fretboard layout with accurate fret positioning using the Rule of 18
- DXF export for CNC machining

### ⚙️ CAM Module
- CNC toolpath generation (profile cutting, pocket milling, drilling)
- G-code export with customizable machine parameters
- Optimized cutting strategies for wood
- Machining time estimation

### 💰 Costing Module
- Material cost database with common tonewoods
- Hardware and supplies pricing
- Labor time estimates for common tasks
- Project-level cost breakdowns with overhead

### 🪵 Tonewood Module
- Comprehensive database of tonewood species
- Physical and acoustic property tracking
- Wood combination analysis
- Style-based recommendations (blues, rock, jazz, metal)
- Alternative wood finder

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Command Line Interface

The `luthier` command provides access to all modules:

```bash
# Design a Stratocaster body
luthier cad body --shape stratocaster --output strat.dxf

# Calculate fret positions
luthier cad fretboard --scale 25.5 --frets 22

# Estimate project cost
luthier costing estimate --body-wood mahogany --neck-wood maple

# Analyze tonewood combination
luthier tonewood analyze --body mahogany --neck maple --fretboard rosewood

# Get wood recommendations for playing style
luthier tonewood recommend --style rock
```

### Python API

```python
from luthiers_toolbox.cad import GuitarBody, GuitarNeck
from luthiers_toolbox.costing import CostEstimator
from luthiers_toolbox.tonewood import TonewoodAnalyzer

# Design a guitar body
body = GuitarBody(shape="stratocaster", scale_length=25.5)
body.export_dxf("my_guitar_body.dxf")

# Estimate costs
estimator = CostEstimator()
project = estimator.estimate_guitar(
    body_wood="mahogany",
    neck_wood="maple",
    fretboard_wood="rosewood"
)
print(f"Total cost: ${project.get_total_cost():.2f}")

# Analyze tonewoods
analyzer = TonewoodAnalyzer()
profile = analyzer.analyze_wood_combination("mahogany", "maple", "rosewood")
print(profile.get_summary())
```

## Modules

### CAD Module

Design parametric guitar components:

- **GuitarBody**: Create body shapes with customizable dimensions
- **GuitarNeck**: Design necks with various profiles and scale lengths
- **Fretboard**: Calculate precise fret positions and slot dimensions
- **Geometry**: Basic 2D primitives (Point, Line, Arc, Circle)

### CAM Module

Generate CNC toolpaths:

- **ToolpathGenerator**: Create cutting paths from CAD designs
- **GCodeGenerator**: Convert toolpaths to G-code
- **Operations**: Pre-defined operations (profile, pocket, drill)

### Costing Module

Estimate project costs:

- **MaterialDatabase**: Prices for tonewoods, hardware, and supplies
- **LaborEstimator**: Time estimates for luthiery tasks
- **CostEstimator**: Complete project cost breakdowns

### Tonewood Module

Analyze wood properties:

- **TonewoodDatabase**: Comprehensive wood species database
- **TonewoodAnalyzer**: Wood combination analysis and recommendations
- **WoodProperties**: Physical properties (density, hardness, stiffness)
- **AcousticProperties**: Tonal characteristics and resonance

## Workflow Example

1. **Design Phase**
   - Choose body shape and dimensions
   - Design neck with desired profile
   - Calculate fretboard layout

2. **Analysis Phase**
   - Select tonewoods based on desired tone
   - Analyze wood combination
   - Estimate material costs

3. **Manufacturing Phase**
   - Generate CNC toolpaths
   - Export G-code for machining
   - Calculate machine time and labor costs

4. **Costing Phase**
   - Review complete cost breakdown
   - Adjust materials or methods as needed
   - Generate final project estimate

## Technical Details

### Scale Lengths
- Standard guitar: 25.5" (Fender style)
- Gibson style: 24.75"
- Short scale: 22.5" - 24"

### Fret Calculation
Uses the precise constant 17.817 for equal temperament:
```
position = scale_length - (scale_length / (2 ^ (fret_number / 12)))
```

### Material Units
- Wood: Board feet (length × width × thickness / 144)
- Hardware: Per piece
- Finishes: Per quart

### Coordinate System
- Origin (0,0) at neck pocket
- X-axis: length (neck to bridge)
- Y-axis: width (bass to treble side)
- Z-axis: depth (negative into material)

## Contributing

Contributions welcome! This is an open-source project aimed at bridging traditional luthiery with digital fabrication.

## License

MIT License - see LICENSE file for details
