# 🎸 Luthier's Toolbox

**Parametric CAD/CAM Suite for Modern Guitar Makers**

Bridge the gap between traditional luthiery and digital fabrication with an integrated toolset for designing, costing, and manufacturing guitars and stringed instruments.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Features

### 🎨 **CAD Module** - Parametric Design Tools
- Guitar body design with classic shapes (Stratocaster, Telecaster, Les Paul, SG)
- Precision neck design with configurable profiles (C, D, V, U)
- Fretboard layout with accurate fret positioning
- Export to DXF for CNC machining

### ⚙️ **CAM Module** - CNC Toolpath Generation
- Profile cutting, pocket milling, and drilling operations
- G-code export with customizable machine parameters
- Optimized cutting strategies for wood
- Machining time estimation

### 💰 **Costing Module** - Material & Labor Estimation
- Comprehensive tonewood pricing database
- Hardware and supplies cost tracking
- Labor time estimates for common luthiery tasks
- Complete project cost breakdowns

### 🪵 **Tonewood Module** - Wood Analytics & Recommendations
- Database of 8+ tonewood species with physical and acoustic properties
- Wood combination analysis for tonal prediction
- Style-based recommendations (blues, rock, jazz, metal)
- Alternative wood finder

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Command Line Usage

```bash
# Design a Stratocaster body
luthier cad body --shape stratocaster --output strat.dxf

# Calculate fret positions for 25.5" scale
luthier cad fretboard --scale 25.5 --frets 22

# Estimate project cost
luthier costing estimate --body-wood mahogany --neck-wood maple

# Analyze tonewood combination
luthier tonewood analyze --body mahogany --neck maple --fretboard rosewood

# Get recommendations for rock style
luthier tonewood recommend --style rock

# Generate CNC toolpaths
luthier cam generate --operation profile --depth 0.5 --output body.gcode
```

### Python API

```python
from luthiers_toolbox.cad import GuitarBody, GuitarNeck, Fretboard
from luthiers_toolbox.cam import ToolpathGenerator, GCodeGenerator, GCodeExporter
from luthiers_toolbox.costing import CostEstimator
from luthiers_toolbox.tonewood import TonewoodAnalyzer

# Design a Stratocaster body
body = GuitarBody(shape="stratocaster", scale_length=25.5)
body.export_dxf("my_strat.dxf")

# Analyze tonewood combination
analyzer = TonewoodAnalyzer()
profile = analyzer.analyze_wood_combination("mahogany", "maple", "rosewood")
print(profile.get_summary())

# Estimate project cost
estimator = CostEstimator()
project = estimator.estimate_guitar(
    body_wood="mahogany",
    neck_wood="maple",
    fretboard_wood="rosewood",
    include_electronics=True
)
print(f"Total cost: ${project.get_total_cost():.2f}")

# Generate CNC toolpaths
generator = ToolpathGenerator()
outline = [(p.x, p.y) for p in body.get_outline()]
toolpath = generator.generate_profile_toolpath(outline, depth=0.5)

gcode_gen = GCodeGenerator(units="inches", spindle_speed=18000)
gcode = gcode_gen.generate([toolpath])
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:
- [Full Documentation](docs/README.md)
- [Complete Workflow Example](examples/basic_workflow.py)

## 🎯 Use Cases

**For Hobbyist Luthiers:**
- Design your first guitar with proven dimensions
- Understand tonewood choices and their impact
- Estimate material costs before purchasing
- Generate CNC files for local fabrication

**For Professional Builders:**
- Rapid prototyping of new designs
- Cost estimation for client quotes
- Standardized toolpath generation
- Material alternatives analysis

**For CNC Operators:**
- Ready-to-use toolpaths for guitar parts
- Optimized cutting strategies
- G-code generation with machine-specific parameters

**For Digital Craftsmen:**
- Bridge between CAD and physical builds
- Integrate traditional techniques with modern tools
- Comprehensive workflow from design to manufacturing

## 🛠️ Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest

# Run specific test file
pytest tests/test_cad.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## 🎸 Technical Details

### Supported Guitar Types
- Electric solid body (Stratocaster, Telecaster, Les Paul, SG, custom)
- Acoustic (coming soon)
- Bass (coming soon)

### Scale Lengths
- Standard: 25.5" (Fender style)
- Gibson: 24.75"
- Short scale: 22.5" - 24"
- Custom: Any value

### Export Formats
- **DXF**: AutoCAD format for 2D designs
- **G-code**: CNC machine programs
- **JSON**: Project data and configurations

### Tonewood Database
Includes physical and acoustic properties for:
- Mahogany, Maple, Rosewood, Ebony
- Spruce, Cedar, Alder, Ash, Walnut

## 🤝 Contributing

Contributions are welcome! This project aims to bridge traditional luthiery with digital fabrication.

Areas for contribution:
- Additional body shapes and templates
- More tonewood species
- Advanced CAM strategies
- Acoustic guitar support
- Inlay design tools
- Assembly instructions generator

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🎯 Project Goals

**Mission:** To empower guitar makers of all skill levels by providing professional-grade digital tools that complement traditional luthiery skills.

**Vision:** A complete digital workflow where builders can:
1. Design custom instruments parametrically
2. Analyze and optimize tonewood choices
3. Generate CNC-ready manufacturing files
4. Estimate costs accurately
5. Share and iterate on designs

## 🙏 Acknowledgments

Built for the luthier community with respect for both traditional craftsmanship and modern technology.

---

**Made with ❤️ for guitar makers, by guitar makers**
