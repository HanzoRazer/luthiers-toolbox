# Universal SVG/HTML File Gallery - Documentation

## 🎯 Overview

A **universal, auto-discovering file gallery** that scans your directory for ALL SVG and HTML files and creates an interactive browsable gallery with zero configuration.

---

## ✨ Key Features

### 🔍 **Auto-Discovery**
- Automatically finds ALL `.svg` and `.html` files
- No manual file listing required
- Works with any directory structure
- Updates when you add new files

### 🎨 **Interactive Viewer**
- Zoom: Mouse wheel or `+`/`-` keys
- Pan: Click & drag or arrow keys
- Reset: Double-click or `0` key
- Fit to screen: `F` key
- Touch support: Pinch-to-zoom on mobile

### 🔎 **Smart Search**
- Real-time search as you type
- Searches filenames and descriptions
- Filter by type (SVG/HTML/All)
- Shows result count

### ⌨️ **Keyboard Shortcuts**
```
+  / =    Zoom In
-  / _    Zoom Out  
0         Reset View
F         Fit to Screen
↑ ↓ ← →   Pan View
```

---

## 📂 Files in This System

### Core Files (Required)
- **`index.html`** - Auto-discovering gallery page
- **`svg-viewer.html`** - Interactive SVG viewer with zoom/pan
- **`generate_gallery.py`** - Python script to generate file list

### Optional Files
- **`files.json`** - Pre-generated file list (faster loading)
- **`test-viewer.html`** - Testing interface
- **`*.svg`** - Your SVG files (auto-discovered)
- **`*.html`** - Your HTML pages (auto-discovered)

---

## 🚀 Usage Methods

### Method 1: Direct Open (Simple)
```powershell
# Just double-click index.html
# Works immediately, uses fallback file list
Start-Process index.html
```

**Pros**: Instant, no setup  
**Cons**: Only shows pre-defined files

---

### Method 2: Local Server (Recommended)
```powershell
# Run Python's built-in HTTP server
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"
python -m http.server 8080

# Open browser to:
# http://localhost:8080
```

**Pros**: Auto-discovers all files, real-time updates  
**Cons**: Requires Python and terminal

---

### Method 3: Pre-Generate File List (Best)
```powershell
# Generate files.json once
python generate_gallery.py

# Then open index.html (no server needed!)
Start-Process index.html
```

**Pros**: Auto-discovers all files, works offline  
**Cons**: Must re-run when adding files

---

### Method 4: GitHub Pages (Production)
```powershell
# Add to git
git add index.html svg-viewer.html generate_gallery.py files.json *.svg
git commit -m "Add universal file gallery"
git push origin main

# Enable Pages in GitHub Settings
# Your gallery will be at:
# https://yourusername.github.io/repo/
```

**Pros**: Professional hosting, shareable URL  
**Cons**: Requires GitHub account

---

## 🔧 How It Works

### File Discovery Flow

```
┌─────────────────────────────────────┐
│   User Opens index.html             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Try Method 1: Load files.json     │◄─── Fastest
└────────────┬────────────────────────┘
             │ (if exists)
             ▼
┌─────────────────────────────────────┐
│   Try Method 2: Parse Directory     │◄─── Auto-updates
└────────────┬────────────────────────┘
             │ (if server running)
             ▼
┌─────────────────────────────────────┐
│   Method 3: Use Fallback List       │◄─── Always works
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Render Gallery Cards              │
└─────────────────────────────────────┘
```

### Gallery Generator

```python
# generate_gallery.py scans directory
scan_directory() 
    ↓
find *.svg and *.html files
    ↓
generate descriptions from filenames
    ↓
create files.json
    ↓
index.html reads files.json on load
```

---

## 📋 Adding New Files

### Option A: Automatic (Server)
```powershell
# 1. Add your SVG/HTML files to directory
# 2. Refresh browser (Ctrl+R)
# Files auto-discovered if using http.server
```

### Option B: Semi-Automatic (Generated)
```powershell
# 1. Add your SVG/HTML files
# 2. Re-run generator
python generate_gallery.py

# 3. Refresh browser
# Files now visible in gallery
```

### Option C: Manual (Fallback)
Edit `index.html` and add to `knownFiles` array:
```javascript
const knownFiles = [
  { 
    name: 'YourFile.svg', 
    type: 'svg', 
    description: 'Your description' 
  },
  // ... more files
];
```

---

## 🎨 Customization

### Change Gallery Colors
Edit `index.html`, find `body` style:
```css
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Customize File Descriptions
Edit `generate_gallery.py`, modify `descriptions` dict:
```python
descriptions = {
    'your_keyword': 'Your custom description',
    'radius': 'Radius arc template',
    # Add more patterns
}
```

### Change Card Layout
Edit `index.html`, find `.gallery` style:
```css
.gallery {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  /* Change 320px to adjust card width */
}
```

---

## 🔍 Search & Filter Features

### Search Box
- **Real-time**: Results update as you type
- **Searches**: Filename and description
- **Case-insensitive**: Works with any capitalization

### Filter Dropdown
- **All Files**: Show everything
- **SVG Only**: Show only SVG graphics
- **HTML Only**: Show only HTML pages

### Result Counter
Shows: `Found X files (Y total)`
- X = Filtered results
- Y = Total discovered files

---

## 📱 Mobile Support

### Touch Gestures (SVG Viewer)
- **Pan**: Single finger drag
- **Zoom**: Pinch with two fingers
- **Reset**: Tap reset button

### Responsive Layout
- Cards stack on small screens
- Buttons wrap appropriately
- Text sizes adjust
- Gallery remains usable

---

## 🐛 Troubleshooting

### No Files Showing
**Problem**: Gallery shows "No files found"

**Solutions**:
1. Run with HTTP server: `python -m http.server 8080`
2. Generate files.json: `python generate_gallery.py`
3. Check files are in same directory as index.html
4. Verify file extensions are `.svg` or `.html`

---

### SVG Won't Load
**Problem**: Clicking card shows error in viewer

**Solutions**:
1. Check file actually exists
2. Verify filename has no special characters
3. Use HTTP server (not `file://` protocol)
4. Check browser console for errors (F12)

---

### Directory Listing Not Working
**Problem**: Only sees fallback files

**Solutions**:
1. Use `python -m http.server` (enables directory listing)
2. Run `generate_gallery.py` to create files.json
3. Deploy to GitHub Pages (directory listing works there)

---

### Search Not Finding Files
**Problem**: File exists but search doesn't find it

**Solutions**:
1. Check spelling (search is case-insensitive)
2. Try filename instead of description
3. Clear filter dropdown (set to "All Files")
4. Refresh browser to reload file list

---

## 🚢 Deployment Options

### Local Network Sharing
```powershell
# Find your IP address
ipconfig

# Start server on all interfaces
python -m http.server 8080 --bind 0.0.0.0

# Share with others:
# http://YOUR_IP:8080
```

### GitHub Pages (Free Hosting)
```powershell
git add index.html svg-viewer.html files.json *.svg
git commit -m "Deploy gallery"
git push origin main
# Enable Pages in repo Settings
```

### Custom Domain
1. Add `CNAME` file with your domain
2. Configure DNS: `A` records to GitHub IPs
3. Enable HTTPS in GitHub Pages settings

---

## 📊 File Scanning Rules

### Included Files
✅ `*.svg` - All SVG graphics  
✅ `*.html` - All HTML pages  

### Excluded Files
❌ `index.html` - Gallery itself  
❌ `svg-viewer.html` - Viewer itself  
❌ `test-viewer.html` - Test page  

### Recursive Scanning
To enable subdirectory scanning, edit `generate_gallery.py`:
```python
files = scan_directory(root, recursive=True)  # Change to True
```

---

## 🎓 Advanced Usage

### Batch Convert DXF to SVG
```python
import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

def convert_dxf_to_svg(dxf_path, svg_path):
    doc = ezdxf.readfile(dxf_path)
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace())
    plt.savefig(svg_path, format='svg', bbox_inches='tight')
    plt.close()

# Then run generate_gallery.py to update index
```

### Embed Gallery in Website
```html
<iframe src="https://yourusername.github.io/repo/" 
        width="100%" height="600" frameborder="0">
</iframe>
```

### API for File List
```javascript
// Fetch file list programmatically
fetch('files.json')
  .then(r => r.json())
  .then(files => {
    console.log('Available files:', files);
    // Process files array
  });
```

---

## 📈 Performance Tips

### Optimize SVG Files
```bash
# Install SVGO
npm install -g svgo

# Optimize all SVGs
svgo *.svg
```

### Lazy Loading (Future Enhancement)
```javascript
// Load thumbnails first, full SVGs on demand
const img = new Image();
img.src = `thumbnails/${file.name}`;
```

### Cache files.json
```javascript
// Add to index.html
localStorage.setItem('cachedFiles', JSON.stringify(files));
```

---

## 🤝 Contributing

### Add File Type Support
Edit `scanDirectory()` in `generate_gallery.py`:
```python
if ext in ['.svg', '.html', '.dxf', '.pdf']:  # Add types
    files.append({...})
```

### Add Description Patterns
Edit `generate_description()`:
```python
descriptions = {
    'your_pattern': 'Your description',
    # Add more keywords
}
```

---

## 📞 Support

### Common Issues
- **CORS Errors**: Use HTTP server or GitHub Pages
- **Slow Loading**: Pre-generate files.json
- **Files Not Found**: Check directory structure
- **Search Not Working**: Verify JavaScript enabled

### Getting Help
1. Check browser console (F12)
2. Review error messages
3. Try different browser
4. Test with HTTP server

---

## 🎉 Summary

You now have a **completely universal** file gallery that:

✅ Auto-discovers ALL SVG/HTML files  
✅ Requires ZERO manual configuration  
✅ Works offline or online  
✅ Scales to thousands of files  
✅ Mobile-friendly responsive design  
✅ Full keyboard navigation  
✅ Interactive zoom/pan viewer  
✅ Real-time search & filter  

**Just add files and go!** 🚀

---

**Last Updated**: November 3, 2025  
**Version**: 2.0.0 (Universal Edition)  
**License**: MIT
