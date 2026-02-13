# Troubleshooting

Common issues and solutions.

---

## Installation Issues

### "Python not found"

**Problem:** Python command not recognized.

**Solutions:**

1. Verify Python is installed: `python --version` or `python3 --version`
2. Add Python to PATH
3. On Windows, try `py` instead of `python`

---

### "npm: command not found"

**Problem:** Node.js/npm not installed.

**Solutions:**

1. Install Node.js from [nodejs.org](https://nodejs.org)
2. Verify: `node --version` and `npm --version`
3. Restart terminal after installation

---

### "Module not found" errors

**Problem:** Python dependencies not installed.

**Solutions:**

```bash
cd services/api
pip install -r requirements.txt
```

If still failing:

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

### "ENOENT: no such file or directory"

**Problem:** npm dependencies not installed.

**Solutions:**

```bash
cd packages/client
rm -rf node_modules
npm install
```

---

## Runtime Issues

### API won't start

**Problem:** `uvicorn` fails to start.

**Common Causes:**

1. **Port in use:**
   ```bash
   # Check what's using port 8000
   # Windows
   netstat -ano | findstr 8000
   # Linux/Mac
   lsof -i :8000
   ```

2. **Missing .env file:**
   ```bash
   cd services/api
   cp .env.example .env  # if available
   ```

3. **Import errors:**
   - Check Python version (3.11+ required)
   - Verify all dependencies installed

---

### UI won't start

**Problem:** `npm run dev` fails.

**Solutions:**

1. Clear npm cache:
   ```bash
   npm cache clean --force
   rm -rf node_modules
   npm install
   ```

2. Check Node version:
   ```bash
   node --version  # Should be 18+
   ```

---

### "CORS error" in browser

**Problem:** API rejecting requests from UI.

**Solutions:**

1. Verify API is running on expected port (8000)
2. Verify UI is running on expected port (5173)
3. Check API CORS configuration in `main.py`

---

## DXF Import Issues

### "Invalid DXF format"

**Problem:** File not recognized as valid DXF.

**Solutions:**

1. Re-export from CAD software as DXF R2013 or R2018
2. Avoid DXF R2024 (limited support)
3. Check file isn't corrupted

---

### "No geometry found"

**Problem:** DXF imports but shows no entities.

**Solutions:**

1. Check layers aren't frozen/off in CAD software
2. Verify geometry is in XY plane (Z near 0)
3. Check for empty model space (geometry might be in paper space)

---

### "Too many open contours"

**Problem:** Geometry has gaps.

**Solutions:**

1. Use "Join Contours" with appropriate tolerance
2. Fix gaps in CAD software before export
3. Enable auto-heal feature

---

## Toolpath Issues

### "Toolpath exceeds work area"

**Problem:** Generated toolpath too large for machine.

**Solutions:**

1. Verify machine profile work area is correct
2. Check geometry scale (mm vs inches)
3. Reposition work origin

---

### "Tool too large for pocket"

**Problem:** Selected tool won't fit in geometry.

**Solutions:**

1. Use smaller tool diameter
2. Check geometry dimensions
3. Verify tool diameter setting is correct

---

### G-code errors on machine

**Problem:** Machine rejects G-code.

**Solutions:**

1. Select correct post processor for your controller
2. Check for unsupported G-codes in output
3. Verify machine profile settings match actual machine

---

## RMOS Safety Issues

### "Export blocked (RED)"

**Problem:** RMOS blocking potentially dangerous operation.

**Solutions:**

1. Review triggered rules in WhyPanel
2. Adjust parameters to resolve safety issues
3. If absolutely necessary, use override (with caution)

---

### "RMOS_STRICT_STARTUP failure"

**Problem:** API won't start due to missing safety modules.

**Solutions:**

1. Ensure all RMOS modules are present
2. Set `RMOS_STRICT_STARTUP=0` to allow startup (not recommended)
3. Check Python import errors for specifics

---

## Performance Issues

### Slow toolpath generation

**Problem:** Generation takes too long.

**Solutions:**

1. Simplify geometry (reduce point count)
2. Increase tolerance settings
3. Use larger stepover for roughing

---

### Slow UI response

**Problem:** UI sluggish or unresponsive.

**Solutions:**

1. Reduce preview detail level
2. Clear browser cache
3. Check available system memory

---

### High memory usage

**Problem:** Application using excessive RAM.

**Solutions:**

1. Close unused design sessions
2. Reduce geometry complexity
3. Restart API/UI periodically during heavy use

---

## Data Issues

### Lost settings

**Problem:** UI settings reset.

**Solutions:**

1. Check browser localStorage isn't being cleared
2. Settings stored in `localStorage` - check browser privacy settings
3. Export settings for backup

---

### Runs not showing

**Problem:** RMOS runs not appearing in list.

**Solutions:**

1. Check `RMOS_RUNS_DIR` is set correctly
2. Verify directory exists and is writable
3. Check file system permissions

---

## Getting Help

### Check Logs

```bash
# API logs
# Check terminal running uvicorn

# Browser console
# F12 → Console tab
```

### Minimum Info for Bug Reports

1. Operating system and version
2. Python version (`python --version`)
3. Node.js version (`node --version`)
4. Steps to reproduce
5. Error messages (full text)
6. Screenshots if UI issue

### Where to Report

- **GitHub Issues**: [Report a bug](https://github.com/HanzoRazer/luthiers-toolbox/issues)
- **Discussions**: [Ask a question](https://github.com/HanzoRazer/luthiers-toolbox/discussions)

---

## Related

- [Installation](getting-started/installation.md) - Setup guide
- [Configuration](getting-started/configuration.md) - Environment settings
