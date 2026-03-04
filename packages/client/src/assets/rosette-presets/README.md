# Rosette Preset SVG Files

This directory contains SVG artwork for rosette pattern previews.

## File Naming Convention

SVG files should be named to match the pattern IDs defined in `/src/lib/rosettePresets.ts`:

### Repeating Single Ring Family
- `herringbone-24.svg` - Herringbone (24 segments)
- `spanish-rope-16.svg` - Spanish Rope (16 segments)
- `wave-12.svg` - Wave Pattern (12 segments)
- `german-rope-8.svg` - German Rope (8 segments)
- `fine-herringbone-32.svg` - Fine Herringbone (32 segments)
- `wide-rope-6.svg` - Wide Rope (6 segments)

### Multi-Ring Alternating Family
- `triple-ring-classic.svg` - Triple Ring Classic
- `five-ring-delicate.svg` - Five Ring Delicate
- `seven-ring-complex.svg` - Seven Ring Complex

### Radial Star Family
- `star-8-point.svg` - 8-Point Star
- `star-12-point.svg` - 12-Point Star
- `star-16-point.svg` - 16-Point Star

### Bordered Field Family
- `simple-border.svg` - Simple Border
- `double-border.svg` - Double Border
- `triple-border-complex.svg` - Triple Border Complex

### Concentric Rings Only Family
- `two-tone-rings.svg` - Two-Tone Rings
- `rainbow-gradient.svg` - Rainbow Gradient
- `wide-band-minimalist.svg` - Wide Band Minimalist

### Hybrid Family
- `segmented-core.svg` - Segmented Core

## SVG Requirements

- **Viewbox:** `0 0 100 100` (recommended for consistency)
- **Format:** Standard SVG, optimized for web
- **Colors:** Actual wood tones or representative colors
- **Size:** Keep file size under 50KB per SVG if possible

## Fallback Behavior

If an SVG file doesn't exist, the component will display a programmatically-generated preview as a fallback.
