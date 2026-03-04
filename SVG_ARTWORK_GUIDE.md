# Rosette Preset SVG Artwork Guide

## Overview

The rosette preset browser is now configured to load actual SVG artwork files. When you add SVG files, they will automatically replace the programmatic previews.

## Where to Place SVG Files

All SVG files should be placed in:
```
packages/client/src/assets/rosette-presets/
```

## File Naming Convention

Each pattern variation has a specific filename. Use these exact names:

### Repeating Single Ring (Segmented Patterns)
- `herringbone-24.svg` ✅ (Example included)
- `spanish-rope-16.svg`
- `wave-12.svg`
- `german-rope-8.svg`
- `fine-herringbone-32.svg`
- `wide-rope-6.svg`

### Multi-Ring Alternating
- `triple-ring-classic.svg`
- `five-ring-delicate.svg`
- `seven-ring-complex.svg`

### Radial Star (Geometric)
- `star-8-point.svg`
- `star-12-point.svg`
- `star-16-point.svg`

### Bordered Field
- `simple-border.svg`
- `double-border.svg`
- `triple-border-complex.svg`

### Concentric Rings Only
- `two-tone-rings.svg`
- `rainbow-gradient.svg`
- `wide-band-minimalist.svg`

### Hybrid
- `segmented-core.svg`

## SVG Requirements

### Viewbox
Use `viewBox="0 0 100 100"` for consistency (recommended, not required)

### Colors
- Use actual wood tone colors (#f5deb3 for maple, #3e2723 for walnut, etc.)
- Or use realistic wood grain textures
- Should match the colorScheme defined in the preset data

### File Size
- Keep files under 50KB if possible
- Optimize SVGs before adding (remove unnecessary metadata)

### Format
- Standard SVG format
- Can include gradients, patterns, textures
- Avoid external dependencies (embed all assets)

## How It Works

1. **If SVG exists**: The browser loads and displays your artwork
2. **If SVG doesn't exist**: Falls back to programmatic preview (current colorful pie slices)
3. **No code changes needed**: Just drop SVG files in the folder with correct names

## Testing

After adding an SVG file:
1. The dev server will auto-reload (HMR)
2. Open the preset browser
3. Your artwork should appear immediately
4. If it doesn't, check browser console for errors

## Example

Check `herringbone-24.svg` in the assets folder to see the structure. Replace it with your actual artwork when ready.

## Current Status

- ✅ Structure set up
- ✅ Component configured to load SVG files
- ✅ Fallback rendering working
- ✅ Example file created (`herringbone-24.svg`)
- ⏳ Need 19 more SVG files from you

## Where to Find Preset Data

Pattern definitions (colors, segments, ring counts) are in:
```
packages/client/src/lib/rosettePresets.ts
```

Each variation has a `svgFile` property that specifies which file to load.
