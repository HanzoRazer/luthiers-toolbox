# GitHub Pages Quick Deployment Guide

## 🚀 Deploy Your SVG Viewer to GitHub Pages in 5 Minutes

### Step 1: Prepare Your Files

The following files are ready for deployment:
```
Luthiers ToolBox/
├── index.html                    # Gallery landing page
├── svg-viewer.html               # Interactive SVG viewer
├── Radius_Arc_15ft.svg          # 15-foot radius template
├── Radius_Arc_Comparison.svg    # Comparison template
└── SVG_VIEWER_README.md         # Documentation
```

### Step 2: Commit Files to Git

```powershell
# Navigate to your repository
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"

# Add the new files
git add index.html
git add svg-viewer.html
git add Radius_Arc_15ft.svg
git add Radius_Arc_Comparison.svg
git add SVG_VIEWER_README.md
git add GITHUB_PAGES_DEPLOY.md

# Commit with descriptive message
git commit -m "Add SVG viewer with radius arc templates for GitHub Pages"

# Push to GitHub
git push origin main
```

### Step 3: Enable GitHub Pages

1. Go to your GitHub repository: `https://github.com/yourusername/Luthiers-ToolBox`
2. Click **Settings** (top right)
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select:
   - Branch: `main`
   - Folder: `/ (root)`
5. Click **Save**
6. Wait 1-2 minutes for deployment

### Step 4: Access Your Site

Your site will be live at:
```
https://yourusername.github.io/Luthiers-ToolBox/
```

#### Direct Links:
- **Gallery**: `https://yourusername.github.io/Luthiers-ToolBox/index.html`
- **Viewer**: `https://yourusername.github.io/Luthiers-ToolBox/svg-viewer.html`
- **15ft Arc**: `https://yourusername.github.io/Luthiers-ToolBox/svg-viewer.html?svg=Radius_Arc_15ft.svg`
- **Comparison**: `https://yourusername.github.io/Luthiers-ToolBox/svg-viewer.html?svg=Radius_Arc_Comparison.svg`

---

## 📱 Testing Your Deployment

### Local Testing (Before Pushing)
```powershell
# Start a simple HTTP server
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"
python -m http.server 8080

# Open browser to: http://localhost:8080
```

### Live Testing (After Deployment)
1. Open your GitHub Pages URL
2. Click on a template card
3. Test zoom (scroll wheel)
4. Test pan (click & drag)
5. Test on mobile device

---

## 🎨 Adding More SVG Files

### Add New Templates to Gallery

1. **Add your SVG file** to the repository root
2. **Edit `index.html`** and add a new card:

```html
<!-- Your New Template -->
<div class="card" onclick="window.location.href='svg-viewer.html?svg=YourFile.svg'">
  <h3>📐 Your Template Name</h3>
  <p>Description of your template and its use case.</p>
  <div class="specs">
    <div><strong>Dimension 1:</strong> Value</div>
    <div><strong>Dimension 2:</strong> Value</div>
    <div><strong>Application:</strong> Use case</div>
  </div>
  <a href="svg-viewer.html?svg=YourFile.svg" class="btn" onclick="event.stopPropagation()">View Interactive</a>
  <a href="YourFile.svg" class="btn btn-secondary" download onclick="event.stopPropagation()">Download SVG</a>
</div>
```

3. **Commit and push**:
```powershell
git add YourFile.svg index.html
git commit -m "Add new template: YourFile.svg"
git push origin main
```

---

## 🔧 Customization Options

### Change Gallery Theme Colors

Edit `index.html`, find this section:
```css
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

Change to your preferred gradient:
```css
/* Blue to green */
background: linear-gradient(135deg, #667eea 0%, #48bb78 100%);

/* Orange to red */
background: linear-gradient(135deg, #ed8936 0%, #e53e3e 100%);

/* Dark theme */
background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
```

### Add Custom Domain

1. Create file `CNAME` in repository root:
```
yourdomain.com
```

2. Update DNS settings:
```
Type: A
Host: @
Value: 185.199.108.153
       185.199.109.153
       185.199.110.153
       185.199.111.153
```

3. Push `CNAME` file:
```powershell
git add CNAME
git commit -m "Add custom domain"
git push origin main
```

---

## 📊 Usage Analytics (Optional)

### Add Google Analytics

1. Get tracking ID from Google Analytics
2. Add to `<head>` section of `index.html` and `svg-viewer.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 🔒 Security Best Practices

### Keep Repository Public
GitHub Pages requires public repositories for free hosting.

### Protect Sensitive Data
- **Don't commit** API keys, passwords, or private CAD files
- Use `.gitignore` for sensitive files:
```gitignore
*.secret
*.key
/private/
```

### Use HTTPS
GitHub Pages automatically serves over HTTPS. No configuration needed!

---

## 🐛 Troubleshooting

### Pages Not Loading
```powershell
# Check GitHub Pages status
git log --oneline -1
# Wait 2-3 minutes after push
# Clear browser cache (Ctrl+Shift+R)
```

### 404 Error
- Verify files are in repository root
- Check file names match exactly (case-sensitive)
- Ensure GitHub Pages is enabled in settings

### SVG Not Displaying
- Validate SVG at https://validator.w3.org/
- Check file encoding is UTF-8
- Ensure `<?xml` declaration is present

### Slow Loading
- Optimize SVG files (remove unnecessary metadata)
- Compress large files
- Use SVG optimization tools like SVGO

---

## 📈 Next Steps

### Add More Features
1. **Convert existing DXF files to SVG**
   - Use `ezdxf` Python library
   - Export as SVG with proper viewBox

2. **Create template library**
   - Fretboard layouts
   - Bracing patterns
   - Body templates
   - Rosette designs

3. **Add search/filter**
   - JavaScript-based filtering
   - Category tags
   - Dimension filters

4. **Enable file uploads**
   - Client-side SVG validation
   - Preview before viewing
   - Save to local storage

---

## 🤝 Sharing Your Site

### Social Media Links
```html
<!-- Add to index.html footer -->
<div class="social-links">
  <a href="https://twitter.com/intent/tweet?url=YOUR_URL&text=Check%20out%20my%20guitar%20design%20templates!">
    Share on Twitter
  </a>
  <a href="https://www.facebook.com/sharer/sharer.php?u=YOUR_URL">
    Share on Facebook
  </a>
</div>
```

### Embed in Documentation
```markdown
[![View Templates](https://img.shields.io/badge/View-Templates-blue)](https://yourusername.github.io/Luthiers-ToolBox/)
```

---

## 📞 Support

If you encounter issues:
1. Check [GitHub Pages documentation](https://docs.github.com/en/pages)
2. Review `SVG_VIEWER_README.md` for detailed viewer instructions
3. Open an issue in your repository
4. Check browser console for JavaScript errors (F12)

---

**Last Updated**: November 3, 2025  
**Version**: 1.0.0  
**Deployment Time**: ~5 minutes
