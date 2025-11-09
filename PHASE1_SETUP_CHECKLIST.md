# ⚙️ Phase 1 Setup & Installation Checklist

**Complete these tasks before starting Week 1 validation work**

---

## 📦 Dependencies Installation

### Client Dependencies

```powershell
cd client
```

- [ ] **Install PostHog (Product Analytics)**
  ```powershell
  npm install posthog-js
  ```
  **Expected:** Package added to `package.json`, no errors

- [ ] **Install Sentry (Error Tracking)**
  ```powershell
  npm install @sentry/vue
  ```
  **Expected:** Package added to `package.json`, no errors

- [ ] **Verify Installation**
  ```powershell
  npm list posthog-js @sentry/vue
  ```
  **Expected:** Both packages listed with versions

---

### Server Dependencies

```powershell
cd server
```

- [ ] **Install Sentry SDK**
  ```powershell
  pip install sentry-sdk[fastapi]
  ```
  **Expected:** Successfully installed

- [ ] **Install Locust (Load Testing)**
  ```powershell
  pip install locust
  ```
  **Expected:** Successfully installed

- [ ] **Verify Installation**
  ```powershell
  pip list | findstr "sentry locust"
  ```
  **Expected:** Both packages listed

---

## 🔑 Create Analytics Accounts

### 1. Google Analytics 4

- [ ] **Create Account**
  1. Go to: https://analytics.google.com
  2. Click "Start measuring"
  3. Account name: "Luthiers Tool Box"
  4. Property name: "Luthiers Tool Box - Client"
  5. Select "Web" platform
  6. Enter website URL: http://localhost:5173 (for now)

- [ ] **Get Measurement ID**
  - Location: Admin → Data Streams → Web Stream Details
  - Format: `G-XXXXXXXXXX`
  - Copy to notepad

**Status:** ☐ Complete - Measurement ID: ________________

---

### 2. PostHog

- [ ] **Create Account**
  1. Go to: https://posthog.com
  2. Click "Get started - free"
  3. Sign up (email or GitHub)
  4. Project name: "Luthiers Tool Box"
  5. Select "Web" platform

- [ ] **Get API Key**
  - Location: Project Settings → API Keys
  - Format: `phc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
  - Copy to notepad

- [ ] **Enable Session Recording**
  - Go to: Settings → Project → Session Recording
  - Toggle "Enable session recording"
  - Set sample rate: 10%

**Status:** ☐ Complete - API Key: ________________

---

### 3. Sentry

- [ ] **Create Account**
  1. Go to: https://sentry.io
  2. Click "Get Started"
  3. Sign up (email or GitHub)
  4. Create organization: "Luthiers Tool Box"

- [ ] **Create Projects**
  
  **Client Project:**
  - [ ] Click "Create Project"
  - [ ] Platform: "Vue"
  - [ ] Name: "luthiers-toolbox-client"
  - [ ] Copy DSN to notepad
  - Format: `https://xxxxx@o123456.ingest.sentry.io/123456`
  
  **Server Project:**
  - [ ] Click "Create Project"
  - [ ] Platform: "Python"
  - [ ] Name: "luthiers-toolbox-server"
  - [ ] Copy DSN to notepad

**Status:** ☐ Complete  
- Client DSN: ________________  
- Server DSN: ________________

---

## 🔧 Configure Environment Variables

### Client Configuration

```powershell
cd client
```

- [ ] **Copy Template**
  ```powershell
  Copy-Item .env.example .env.local
  ```

- [ ] **Edit `.env.local`**
  Open in editor and fill in:
  ```bash
  VITE_GA4_MEASUREMENT_ID=G-XXXXXXXXXX
  VITE_POSTHOG_API_KEY=phc_xxxxxxxxxxxxx
  VITE_POSTHOG_HOST=https://app.posthog.com
  VITE_SENTRY_DSN=https://xxxx@sentry.io/xxxx
  VITE_SENTRY_ENVIRONMENT=development
  VITE_API_BASE_URL=http://localhost:8000
  VITE_ENABLE_ANALYTICS=true
  VITE_DEBUG=true
  ```

- [ ] **Save and Close**

**Status:** ☐ Complete

---

### Server Configuration

```powershell
cd server
```

- [ ] **Create `.env` file**
  ```powershell
  New-Item -Path .env -ItemType File
  ```

- [ ] **Edit `.env`**
  Open in editor and add:
  ```bash
  SENTRY_DSN=https://xxxx@sentry.io/xxxx
  ENVIRONMENT=development
  DATABASE_URL=sqlite:///./toolbox.db
  ```

- [ ] **Save and Close**

**Status:** ☐ Complete

---

## 🧪 Test Analytics Integration

### Start Development Servers

**Terminal 1 (Server):**
```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload --port 8000
```

**Terminal 2 (Client):**
```powershell
cd client
npm run dev
```

---

### Test Client Analytics

- [ ] **Open Browser**
  - Navigate to: http://localhost:5173

- [ ] **Check Console**
  Should see:
  ```
  PostHog initialized
  Google Analytics 4 initialized
  🎸 Luthier's Tool Box initialized
  📊 Analytics: Enabled
  ```

- [ ] **Test Event Tracking**
  1. Open browser DevTools (F12)
  2. Go to Network tab
  3. Filter: "posthog"
  4. Click around the app
  5. Should see POST requests to PostHog

- [ ] **Test GA4 Events**
  1. Go to: https://analytics.google.com
  2. Navigate to: Reports → Realtime
  3. Should see 1 active user (you!)

- [ ] **Test Sentry Error Tracking**
  1. Open browser console
  2. Type: `throw new Error("Test error")`
  3. Check Sentry dashboard for error

**Status:** ☐ All tests passed

---

### Test Server Integration

- [ ] **Check Server Logs**
  Terminal 1 should show:
  ```
  INFO: Application startup complete.
  ```

- [ ] **Test Sentry on Server**
  1. Make an API request that will fail:
     ```powershell
     Invoke-RestMethod -Uri "http://localhost:8000/api/nonexistent" -Method POST
     ```
  2. Check Sentry server project for error

- [ ] **Test API Docs**
  - Navigate to: http://localhost:8000/docs
  - Should load without errors

**Status:** ☐ All tests passed

---

## 📊 Verify Analytics Dashboards

### PostHog Dashboard

- [ ] **Login to PostHog**
  - URL: https://app.posthog.com
  
- [ ] **Check Events**
  - Go to: Events → Live Events
  - Should see `$pageview` events

- [ ] **Create Funnel**
  - Go to: Insights → New Insight → Funnel
  - Steps: 
    1. Event: `$pageview` (Any page)
    2. Event: `calculator_used`
    3. Event: `dxf_export`
  - Save as: "Design to Export Funnel"

- [ ] **Enable Recordings**
  - Go to: Session Recordings
  - Play a recording (if any)

**Status:** ☐ Complete

---

### Google Analytics 4 Dashboard

- [ ] **Login to GA4**
  - URL: https://analytics.google.com

- [ ] **Check Realtime**
  - Go to: Reports → Realtime
  - Should see active users

- [ ] **Create Custom Events**
  - Go to: Configure → Events → Create Event
  - Event name: `dxf_export_success`
  - Conditions: `event_name` equals `dxf_export`

**Status:** ☐ Complete

---

### Sentry Dashboard

- [ ] **Login to Sentry**
  - URL: https://sentry.io

- [ ] **Check Issues**
  - Go to: Issues → All Unresolved
  - Should see test errors (if you triggered any)

- [ ] **Set Alert Rules**
  - Go to: Alerts → Create Alert
  - Condition: "Error rate exceeds 2%"
  - Action: Email notification

**Status:** ☐ Complete

---

## 🚀 Bonus: Optional Tools

### Calendly (Interview Scheduling)

- [ ] Create account: https://calendly.com
- [ ] Set availability (30-min slots)
- [ ] Copy scheduling link

**Status:** ☐ Complete - Link: ________________

---

### Otter.ai (Transcription)

- [ ] Create account: https://otter.ai
- [ ] Link Zoom account (if using Zoom)
- [ ] Test transcription with sample recording

**Status:** ☐ Complete

---

### Notion (Notes Organization)

- [ ] Create account: https://notion.so
- [ ] Create workspace: "Luthiers Tool Box"
- [ ] Create databases:
  - Interview notes
  - Feature requests
  - Bug tracker

**Status:** ☐ Complete

---

## ✅ Final Verification Checklist

Before starting Week 1 validation:

- [ ] All npm packages installed (`posthog-js`, `@sentry/vue`)
- [ ] All pip packages installed (`sentry-sdk`, `locust`)
- [ ] GA4 account created, Measurement ID obtained
- [ ] PostHog account created, API key obtained
- [ ] Sentry accounts created (client + server DSNs obtained)
- [ ] `.env.local` configured (client)
- [ ] `.env` configured (server)
- [ ] Dev servers start without errors
- [ ] PostHog events appear in dashboard
- [ ] GA4 realtime shows activity
- [ ] Sentry captures test errors
- [ ] Calendly link ready (optional)
- [ ] Interview guide reviewed

**Total Progress:** ____ / 14 items complete

---

## 🆘 Troubleshooting

### PostHog not initializing

**Issue:** Console shows "PostHog API key not found"

**Fix:**
1. Check `.env.local` has correct `VITE_POSTHOG_API_KEY`
2. Restart dev server (`Ctrl+C`, then `npm run dev`)
3. Hard refresh browser (`Ctrl+Shift+R`)

---

### GA4 not tracking

**Issue:** No events in GA4 Realtime

**Fix:**
1. Check Measurement ID format: `G-XXXXXXXXXX`
2. Verify DebugView in GA4 (Admin → DebugView)
3. Disable ad blockers/privacy extensions
4. Wait 5 minutes (GA4 has lag)

---

### Sentry errors not appearing

**Issue:** Test errors don't show in Sentry dashboard

**Fix:**
1. Check DSN format: `https://xxxx@o123.ingest.sentry.io/123`
2. Check Sentry project environment matches (development)
3. Check network tab for POST requests to `sentry.io`
4. Ensure error was actually thrown (check console)

---

### Cannot import analytics module

**Issue:** `Cannot find module './utils/analytics'`

**Fix:**
1. Check file exists: `client/src/utils/analytics.ts`
2. Check import path in `main.ts`: `import analytics from './utils/analytics'`
3. Restart VS Code TypeScript server
4. Run `npm install` again

---

## 📝 Installation Notes

**Date Completed:** ________________  
**Completed By:** ________________  
**Issues Encountered:** 





**Next Step:** Begin Week 1 validation tasks in `PHASE1_VALIDATION_CHECKLIST.md`

---

**Installation Status:** ☐ Complete ☐ Partial ☐ Not Started
