# SVG Viewer for Luthier's ToolBox

A minimal, elegant SVG viewer with zoom and pan controls - perfect for GitHub Pages deployment.

## 🎯 Features

- **Zoom & Pan**: Smooth mouse/touch controls
- **Drag & Drop**: Drop SVG files directly into the viewer
- **File Upload**: Load SVG files from your computer
- **Responsive**: Works on desktop, tablet, and mobile
- **Keyboard Shortcuts**: Quick access to common functions
- **URL Parameters**: Direct link to specific SVG files
- **Touch Support**: Pinch-to-zoom on mobile devices

## 🚀 Quick Start

### Option 1: Local Usage
1. Open `svg-viewer.html` in any modern browser
2. Click "Load SVG" or drag & drop an SVG file
3. Use mouse wheel to zoom, click & drag to pan

### Option 2: GitHub Pages
1. Push `svg-viewer.html` and your SVG files to your repository
2. Enable GitHub Pages in repository settings
3. Access via URL: `https://yourusername.github.io/repo/svg-viewer.html`

### Option 3: Direct SVG Link
Load a specific SVG automatically using URL parameters:
```
https://yourusername.github.io/repo/svg-viewer.html?svg=Radius_Arc_15ft.svg
```

## 🎮 Controls

| Action | Method |
|--------|--------|
| **Pan** | Click & drag mouse |
| **Zoom In** | Scroll up / Click "🔍 Zoom In" button |
| **Zoom Out** | Scroll down / Click "🔍 Zoom Out" button |
| **Reset View** | Double-click canvas / Click "⟲ Reset" button |
| **Fit to Screen** | Click "⛶ Fit to Screen" button |
| **Load File** | Click "📂 Load SVG" / Drag & drop |

### Touch Controls (Mobile/Tablet)
- **Pan**: Single finger drag
- **Zoom**: Pinch gesture (two fingers)
- **Reset**: Tap "Reset" button

## 📁 Example Files

### Radius_Arc_15ft.svg
**15-Foot Radius Arc Template** for guitar top/back arching reference.

**Specifications**:
- Radius: 15 feet (4572mm / 180 inches)
- Span: 500mm (19.69 inches)
- Sagitta (Rise): 6.84mm (0.269 inches)

**Usage**: Use this template to check radius dish accuracy during guitar top/back carving. The arc represents the ideal curvature for a 15-foot radius across a 500mm wide guitar body.

## 🔧 Technical Details

### Browser Compatibility
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

### Features
- **No Dependencies**: Pure HTML/CSS/JavaScript
- **Responsive Design**: Adapts to any screen size
- **Performance**: Hardware-accelerated transforms
- **Accessibility**: Keyboard and screen reader support

### SVG Support
Works with any valid SVG file:
- Guitar body templates
- Bracing patterns
- Rosette designs
- Graduation maps
- Radius arc templates
- Fretboard layouts

## 📦 GitHub Pages Deployment

### Step 1: Prepare Files
```bash
# Add viewer and SVG files
git add svg-viewer.html
git add Radius_Arc_15ft.svg
git add SVG_VIEWER_README.md
git commit -m "Add SVG viewer with radius arc template"
git push origin main
```

### Step 2: Enable GitHub Pages
1. Go to repository **Settings**
2. Navigate to **Pages** section
3. Select **Source**: `main` branch, `/ (root)` folder
4. Click **Save**
5. Wait 1-2 minutes for deployment

### Step 3: Access Your Viewer
```
https://yourusername.github.io/Luthiers-ToolBox/svg-viewer.html
https://yourusername.github.io/Luthiers-ToolBox/svg-viewer.html?svg=Radius_Arc_15ft.svg
```

## 🎨 Customization

### Change Color Scheme
Edit the `<style>` section in `svg-viewer.html`:
```css
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
button {
  background: #667eea; /* Change button color */
}
```

### Add Default SVG
Modify the URL parameter check at the end of the script:
```javascript
// Load default SVG if no parameter provided
if (!svgPath) {
  loadSvg(defaultSvgContent, 'default.svg');
}
```

## 📝 Use Cases

### 1. Design Portfolio
Showcase your guitar designs on GitHub Pages with interactive zoom/pan.

### 2. CAD File Sharing
Share DXF-to-SVG conversions with clients or collaborators.

### 3. Documentation
Embed SVG technical drawings in project documentation.

### 4. CNC Reference
Quick-view radius templates and toolpath previews before machining.

### 5. Mobile Workshop Reference
Access design files on tablet/phone in the workshop.

## 🛠 Advanced Features

### URL Parameter Options
```
?svg=path/to/file.svg          # Load specific SVG
?svg=file.svg&zoom=2           # Load with initial zoom (future)
?svg=file.svg&fit=true         # Auto-fit to screen (future)
```

### Multiple File Support
The viewer can be extended to support galleries:
```html
<a href="svg-viewer.html?svg=design1.svg">Design 1</a>
<a href="svg-viewer.html?svg=design2.svg">Design 2</a>
```

## 🐛 Troubleshooting

### SVG Not Loading
- Check file path is correct
- Ensure SVG file is valid XML
- Verify file is in same directory or accessible path

### Pan/Zoom Not Working
- Ensure JavaScript is enabled
- Try a different browser
- Clear browser cache

### GitHub Pages 404 Error
- Wait 2-3 minutes after enabling Pages
- Check repository is public
- Verify file is committed to main branch

## 📄 License

This viewer is part of the Luthier's ToolBox project.

## 🤝 Contributing

To add features or fix bugs:
1. Fork the repository
2. Create a feature branch
3. Make your changes to `svg-viewer.html`
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Refer to project documentation

---

**Created for**: Luthier's ToolBox CNC Lutherie Project  
**Last Updated**: November 3, 2025  
**Version**: 1.0.0
