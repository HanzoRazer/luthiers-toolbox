# Luthier's ToolBox

**The complete toolkit for luthiers and guitar builders.**

Luthier's ToolBox provides everything you need to design, calculate, and manufacture stringed instruments with precision CNC workflows.

---

## What You Can Do

<div class="grid cards" markdown>

- :material-guitar-electric: **Design Instruments**

  Scale length, body dimensions, fret spacing, and more.

- :material-calculator: **Calculate Everything**

  String tension, board feet, unit conversions, miter angles.

- :material-file-cad: **Process CAD Files**

  Import DXF, validate geometry, prepare for CNC.

- :material-robot-industrial: **Generate Toolpaths**

  G-code for pockets, contours, drilling, and rosettes.

</div>

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/HanzoRazer/luthiers-toolbox.git

# Start the API
cd luthiers-toolbox/services/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start the UI
cd ../packages/client
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173)

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Scale Length Designer** | Calculate string tension using Mersenne's Law |
| **Unit Converter** | Convert between metric, imperial, and specialty units |
| **Woodwork Calculator** | Board feet, wood weight, miter angles |
| **DXF Import** | Validate and process CAD files |
| **Toolpath Generation** | Adaptive pockets, contours, drilling |
| **Rosette Designer** | Create intricate sound hole patterns |
| **Fret Calculator** | Equal temperament and custom intonation |
| **RMOS Safety** | Manufacturing decision intelligence |

---

## Architecture

```
luthiers-toolbox/
├── packages/client/     # Vue 3 frontend
├── services/api/        # FastAPI backend
├── contracts/           # JSON schemas
└── docs/               # This documentation
```

---

## Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/HanzoRazer/luthiers-toolbox/issues)
- **Discussions**: [Ask questions](https://github.com/HanzoRazer/luthiers-toolbox/discussions)

---

## License

Open source under the MIT License.
