# Shields.io Badge Quick Reference

## 🎯 What It Does
Generates color-coded Shields.io badges showing G-code output sizes for each post-processor preset, published to GitHub Pages.

## 🚀 Quick Start

### 1. Enable GitHub Pages
```
Settings → Pages → Source: "GitHub Actions" → Save
```

### 2. Run Workflow
```
Actions → API Health + Smoke → Run workflow
```

### 3. Add Badges to README
```markdown
![GRBL](https://img.shields.io/endpoint?url=https://<OWNER>.github.io/<REPO>/grbl.json)
![Mach3](https://img.shields.io/endpoint?url=https://<OWNER>.github.io/<REPO>/mach3.json)
![Haas](https://img.shields.io/endpoint?url=https://<OWNER>.github.io/<REPO>/haas.json)
![Marlin](https://img.shields.io/endpoint?url=https://<OWNER>.github.io/<REPO>/marlin.json)
```

## 📊 Badge Colors

| Color | Meaning |
|-------|---------|
| 🟩 Green | Normal (within threshold) |
| 🟨 Yellow | No baseline yet (first run) |
| 🟧 Orange | Size regression (>35% growth) |
| 🟥 Red | Empty output (0 bytes) |

## 🔗 URLs

**Per-preset badges:**
- `https://<OWNER>.github.io/<REPO>/grbl.json`
- `https://<OWNER>.github.io/<REPO>/mach3.json`
- `https://<OWNER>.github.io/<REPO>/haas.json`
- `https://<OWNER>.github.io/<REPO>/marlin.json`

**Aggregate index:**
- `https://<OWNER>.github.io/<REPO>/badges.json`

## 📋 badges.json Structure

```json
{
  "schema": "toolbox-art-studio/badges-v1",
  "smoke_ok": true,
  "size_gate_ok": true,
  "growth_threshold": 0.35,
  "shrink_threshold": 0.0,
  "presets": {
    "GRBL": {
      "bytes": 1012,
      "baseline_bytes": 980,
      "delta_bytes": 32,
      "delta_pct": 0.0327,
      "badge_color": "green"
    }
  }
}
```

## 🔧 Workflow Changes

### Added Permissions
```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### Added Steps (3)
1. **Build badge JSONs** - Generates per-preset + index
2. **Configure Pages** - Sets up GitHub Pages
3. **Upload/Deploy Pages** - Publishes to GitHub Pages

## 🎨 Usage Examples

### Basic Badge
```markdown
![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)
```

### Clickable Badge
```markdown
[![GRBL](https://img.shields.io/endpoint?url=https://HanzoRazer.github.io/guitar_tap/grbl.json)](https://github.com/HanzoRazer/guitar_tap/actions)
```

### Dashboard Link
```markdown
**All presets:** `https://HanzoRazer.github.io/guitar_tap/badges.json`
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 on badge URL | Enable Pages in Settings → Pages |
| Badges not updating | Wait 5 min (Shields.io cache) |
| Wrong colors | Check `SIZE_GROWTH_THRESH` variable |
| Missing presets | Verify `smoke_posts.json` has all presets |

## 📚 See Also

- [SHIELDS_BADGE_SYSTEM.md](./SHIELDS_BADGE_SYSTEM.md) - Complete documentation
- [API_HEALTH_SMOKE_COMPLETE.md](./API_HEALTH_SMOKE_COMPLETE.md) - Workflow docs

---

**Status:** ✅ Implemented  
**Date:** November 6, 2025
