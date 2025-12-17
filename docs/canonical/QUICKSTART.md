# 🎸 Luthier's Tool Box - Quick Start Guide

**Welcome!** This guide will get you from zero to running the full stack in **10 minutes**.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Node.js 20+** ([Download](https://nodejs.org))
- ✅ **Python 3.11+** ([Download](https://python.org))
- ✅ **Git** ([Download](https://git-scm.com))
- ✅ **Docker** (optional, for production) ([Download](https://docker.com))

Check versions:
```powershell
node --version    # Should be v20.x or higher
python --version  # Should be 3.11.x or higher
git --version
```

---

## 🚀 Quick Start (Development)

### 1. Clone Repository

```powershell
git clone https://github.com/HanzoRazer/luthiers-tool-box
cd luthiers-tool-box
```

### 2. Set Up Backend (FastAPI Server)

```powershell
# Navigate to server directory
cd server

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # PowerShell
# OR: .venv\Scripts\activate.bat  # CMD

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app:app --reload --port 8000
```

✅ Server running at **http://localhost:8000**  
📄 API docs at **http://localhost:8000/docs**

---

### 3. Set Up Frontend (Vue 3 Client)

Open a **new terminal** (keep server running):

```powershell
# Navigate to client directory
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Client running at **http://localhost:5173**

---

### 4. Verify Everything Works

Open browser to **http://localhost:5173**

You should see:
- 🎸 Luthier's Tool Box home page
- Navigation: Design, Calculator, Export, CurveLab
- No console errors

Try:
1. Click **"CurveLab"** → Draw a shape → Export JSON
2. Click **"Calculator"** → Test rosette calculator
3. Check network tab: API calls should hit `http://localhost:8000`

---

## 🐳 Quick Start (Docker - Production-like)

If you prefer Docker (no local Node/Python setup needed):

```powershell
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build
```

Access:
- **Client:** http://localhost:8080
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

Stop services:
```powershell
docker compose down
```

---

## 📁 Project Structure

```
luthiers-tool-box/
├── client/                  # Vue 3 Frontend
│   ├── src/
│   │   ├── components/      # Vue components (CurveLab, calculators)
│   │   ├── utils/           # API client, analytics, helpers
│   │   └── App.vue          # Main app component
│   ├── package.json
│   └── vite.config.ts
│
├── server/                  # FastAPI Backend
│   ├── app.py               # Main FastAPI app
│   ├── curvemath_router.py  # Curve operations API
│   ├── pipelines/           # Calculator pipelines (rosette, bracing)
│   ├── tests/               # Pytest tests
│   └── requirements.txt
│
├── guitar_tap/              # Desktop companion tool (PyQt6)
│   └── guitar_tap.py
│
├── docs/                    # Documentation
│   ├── MVP_TO_PRODUCTION_ROADMAP.md
│   ├── PHASE1_VALIDATION_CHECKLIST.md
│   └── user_interview_guide.md
│
└── docker-compose.yml       # Production deployment
```

---

## 🧪 Running Tests

### Client Tests (Vitest)

```powershell
cd client
npm run test              # Run once
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage report
```

### Server Tests (Pytest)

```powershell
cd server
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=.            # With coverage
pytest tests/test_curvemath.py  # Specific file
```

---

## 🔧 Common Issues & Solutions

### Issue: `npm install` fails

**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -r node_modules
npm install
```

### Issue: Python module not found

**Solution:**
```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Port 8000 or 5173 already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or change port
uvicorn app:app --port 8001  # Server
npm run dev -- --port 5174   # Client
```

### Issue: CORS errors in browser console

**Solution:**
The server already has CORS configured. If you still see errors:

1. Check `server/app.py` has:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       allow_methods=["*"],
       allow_headers=["*"]
   )
   ```

2. Clear browser cache and reload

### Issue: TypeScript errors in VS Code

**Solution:**
```powershell
cd client
npm install  # Ensure all deps installed

# Restart VS Code TypeScript server:
# Ctrl+Shift+P → "TypeScript: Restart TS Server"
```

---

## 📊 Phase 1: Validation (Next Steps)

Now that your environment is running, follow **PHASE1_VALIDATION_CHECKLIST.md**:

1. **Week 1:** Set up analytics (GA4, PostHog, Sentry)
2. **Week 2-3:** Conduct user interviews
3. **Week 4:** Write validation report

See `docs/PHASE1_VALIDATION_CHECKLIST.md` for detailed tasks.

---

## 🌐 Environment Variables

Create `.env.local` files for configuration:

### Client `.env.local`

```bash
# Copy from .env.example
cp .env.example .env.local

# Edit with your values
VITE_GA4_MEASUREMENT_ID=G-XXXXXXXXXX
VITE_POSTHOG_API_KEY=phc_xxxxxxxxxxxxx
VITE_SENTRY_DSN=https://xxxx@sentry.io/xxxx
```

### Server `.env`

```bash
# Create server/.env
SENTRY_DSN=https://xxxx@sentry.io/xxxx
ENVIRONMENT=development
DATABASE_URL=sqlite:///./toolbox.db
```

---

## 📚 Key Resources

- **API Documentation:** http://localhost:8000/docs (when server running)
- **Project Roadmap:** `MVP_TO_PRODUCTION_ROADMAP.md`
- **Phase 1 Tasks:** `PHASE1_VALIDATION_CHECKLIST.md`
- **User Interviews:** `docs/user_interview_guide.md`
- **Architecture:** See `.github/copilot-instructions.md`

---

## 🆘 Getting Help

- **Issues:** Check existing GitHub issues or create new one
- **Discord:** [Join our community] (TBD)
- **Email:** support@luthierstoolbox.com (TBD)
- **Forums:** MIMF.com, r/Luthier

---

## ✅ Success Checklist

Before you start development, verify:

- [ ] Server running at http://localhost:8000
- [ ] Client running at http://localhost:5173
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] CurveLab component loads without errors
- [ ] Can draw and export JSON from CurveLab
- [ ] Tests pass: `npm run test` and `pytest`
- [ ] No console errors in browser DevTools

---

**🎉 You're ready to build!**

Next: Read `MVP_TO_PRODUCTION_ROADMAP.md` for the full development plan.

**Happy coding! 🎸**
