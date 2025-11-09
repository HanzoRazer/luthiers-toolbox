# 🧩 Phase 1: MVP Validation Checklist (Weeks 1-4)

**Goal:** Validate product-market fit before scaling  
**Timeline:** November 4 - December 1, 2025  
**Owner:** Project Lead

---

## Week 1: Setup & User Research (Nov 4-10)

### Day 1-2: Analytics Infrastructure ✓

- [ ] **Install Google Analytics 4**
  ```bash
  # Add to client/index.html
  # GA4 Measurement ID: G-XXXXXXXXXX
  ```
  - [ ] Create GA4 property at analytics.google.com
  - [ ] Add tracking code to `client/index.html`
  - [ ] Set up custom events: `dxf_export`, `calculator_used`, `feature_clicked`
  - [ ] Test events in GA4 DebugView

- [ ] **Install PostHog (Open-source Analytics)**
  ```bash
  cd client
  npm install posthog-js
  ```
  - [ ] Create account at posthog.com (free tier: 1M events/mo)
  - [ ] Add initialization to `client/src/main.ts`
  - [ ] Set up session recordings (sample 10% of sessions)
  - [ ] Create funnels: Signup → First Design → Export DXF

- [ ] **Setup Sentry Error Tracking**
  ```bash
  cd client
  npm install @sentry/vue
  
  cd ../server
  pip install sentry-sdk[fastapi]
  ```
  - [ ] Create project at sentry.io
  - [ ] Add Sentry to `client/src/main.ts`
  - [ ] Add Sentry to `server/app.py`
  - [ ] Test error reporting with intentional bug

**Deliverable:** Analytics dashboard showing real-time user activity

---

### Day 3-5: User Interview Preparation

- [ ] **Create Interview Guide**
  - [ ] Save as `docs/user_interview_guide.md`
  - [ ] Include 15 questions covering: workflow, pain points, pricing
  - [ ] Add consent form for recording

- [ ] **Recruit 10-15 Luthiers**
  - [ ] Post in MIMF forums (luthiersforum.com)
  - [ ] Post in r/Luthier subreddit
  - [ ] DM 20 luthiers on Instagram (#guitarluthier)
  - [ ] Email 5 lutherie schools (Galloup, LMII, etc.)
  - [ ] Offer $25 Amazon gift card for 30-min interview

- [ ] **Schedule Interviews**
  - [ ] Use Calendly for booking
  - [ ] Target: 2 interviews per day for Week 2-3
  - [ ] Record via Zoom (with permission)

**Deliverable:** 10 scheduled interviews

---

### Day 6-7: Survey Creation

- [ ] **Create User Survey (Google Forms)**
  - Questions to include:
    - What CAD tools do you currently use?
    - How much time do you spend on guitar design per week?
    - What's the most frustrating part of CNC lutherie?
    - Which feature would you use most? (rank 1-5)
    - Would you pay for this tool? How much?
  - [ ] Add demographic questions (pro/hobbyist, years experience)
  - [ ] Include NPS question: "How likely to recommend?" (0-10)

- [ ] **Distribute Survey**
  - [ ] Post in 3 Facebook lutherie groups
  - [ ] Post on r/Luthier with mod permission
  - [ ] Email to beta user list (if any)
  - [ ] Add banner to Tool Box app: "Help us improve - 2 min survey"
  - [ ] Target: 50+ responses

**Deliverable:** Survey live with 10+ responses by end of week

---

## Week 2-3: User Interviews & Technical Benchmarking (Nov 11-24)

### User Interviews (10 total)

**Interview Schedule:**
- [ ] Interview #1: Pro luthier (acoustic)
- [ ] Interview #2: Pro luthier (electric)
- [ ] Interview #3: CNC shop owner
- [ ] Interview #4: Lutherie school instructor
- [ ] Interview #5: Hobbyist (3+ years experience)
- [ ] Interview #6: Hobbyist (beginner)
- [ ] Interview #7: Repair shop owner
- [ ] Interview #8: Wood supplier with CNC services
- [ ] Interview #9: CAD/CAM professional (non-luthier)
- [ ] Interview #10: Guitar designer (artist/custom)

**After Each Interview:**
- [ ] Transcribe notes within 24 hours
- [ ] Tag key insights: `pain_point`, `feature_request`, `pricing_feedback`
- [ ] Update interview summary spreadsheet

---

### Technical Benchmarking

- [ ] **Performance Testing**
  ```bash
  # Client performance
  cd client
  npm run build
  npx lighthouse http://localhost:5173 --view
  # Target: Performance score 90+, FCP < 1.8s
  ```
  - [ ] Run Lighthouse audit (desktop + mobile)
  - [ ] Check bundle size: `npm run build -- --report`
  - [ ] Profile DXF export time with 1000-point polyline
  - [ ] Test on slow 3G network (Chrome DevTools throttling)

- [ ] **API Load Testing**
  ```bash
  cd server
  pip install locust
  # Create tests/locustfile.py (see roadmap)
  locust -f tests/locustfile.py --host=http://localhost:8000
  ```
  - [ ] Test `/math/offset/polycurve` with 100 concurrent users
  - [ ] Test `/api/rosette/calculate` response time (target <200ms)
  - [ ] Check memory usage under load (target <500MB)
  - [ ] Document max concurrent users before degradation

- [ ] **Browser Compatibility**
  - [ ] Test Chrome (latest)
  - [ ] Test Firefox (latest)
  - [ ] Test Safari (latest)
  - [ ] Test Edge (latest)
  - [ ] Document any rendering issues

- [ ] **Error Rate Analysis**
  - [ ] Check Sentry for error frequency
  - [ ] Calculate error rate: (errors / total requests) × 100
  - [ ] Target: <2% error rate
  - [ ] Identify top 5 most frequent errors
  - [ ] Create bug tickets for critical issues

**Deliverable:** Benchmarking report with pass/fail on targets

---

## Week 4: Analysis & Validation Report (Nov 25 - Dec 1)

### Data Analysis

- [ ] **Survey Analysis**
  - [ ] Calculate NPS score: % Promoters (9-10) - % Detractors (0-6)
  - [ ] Target: NPS > 40
  - [ ] Create pie chart of "most wanted features"
  - [ ] Calculate average willingness-to-pay
  - [ ] Identify 3 most common pain points

- [ ] **Interview Synthesis**
  - [ ] Create affinity diagram (group similar insights)
  - [ ] Count feature requests (rank by frequency)
  - [ ] Extract 10 best user quotes
  - [ ] Identify 3 user personas
  - [ ] Calculate: % users who would switch from current tool

- [ ] **Analytics Review**
  - [ ] Pull GA4 reports:
    - Daily active users (DAU)
    - Average session duration
    - Most-used features (calculator breakdown)
    - Drop-off points (where users leave)
  - [ ] Review PostHog session recordings (watch 10 sessions)
  - [ ] Calculate time-to-first-value (signup → first DXF export)

---

### MVP Validation Report

**Create:** `docs/MVP_VALIDATION_REPORT.md`

**Sections:**

#### 1. Executive Summary
- [ ] 3-sentence summary of findings
- [ ] Go/No-Go recommendation with rationale
- [ ] Key metrics dashboard (users, NPS, error rate)

#### 2. User Feedback Summary
- [ ] Interview highlights (10 quotes)
- [ ] Survey results (charts + key stats)
- [ ] User personas (3 profiles with photos, goals, pain points)

#### 3. Technical Performance
- [ ] Benchmark results table (actual vs. target)
- [ ] Performance audit summary
- [ ] Critical bugs identified (with severity)
- [ ] Browser compatibility matrix

#### 4. Feature Prioritization
- [ ] Impact × Feasibility matrix (2×2 grid)
- [ ] Must-have features for V2.0 (top 3)
- [ ] Nice-to-have features (top 5)
- [ ] Backlog for V3.0

#### 5. Business Validation
- [ ] Willingness to pay analysis
  - Average: $XX/mo
  - Range: $X - $Y
  - % willing to pay: XX%
- [ ] Competitor comparison table
- [ ] Market size estimate (TAM/SAM/SOM)

#### 6. Recommendations
- [ ] Product changes needed before launch
- [ ] Technical debt to address
- [ ] Feature roadmap priorities
- [ ] Pricing strategy recommendation

#### 7. Go/No-Go Decision

**Decision Criteria:**

| Metric | Threshold | Result | Pass? |
|--------|-----------|--------|-------|
| NPS Score | ≥40 | ___ | ☐ |
| Error Rate | <2% | ___% | ☐ |
| Lighthouse Score | ≥85 | ___ | ☐ |
| Time to First Value | <15 min | ___ min | ☐ |
| Would Recommend | ≥70% | ___% | ☐ |
| Critical Bugs | <5 | ___ | ☐ |

**Decision:**
- ✅ **GO:** 5+ criteria pass → Proceed to Phase 2
- 🟡 **ITERATE:** 3-4 criteria pass → Fix critical issues, re-validate in 2 weeks
- ❌ **PIVOT:** <3 criteria pass → Major changes needed or consider pivot

**Deliverable:** Complete validation report + go/no-go decision by Dec 1

---

## Quick Reference: Tools & Credentials

### Analytics
- **Google Analytics 4:** https://analytics.google.com
- **PostHog:** https://app.posthog.com
- **Sentry:** https://sentry.io

### User Research
- **Calendly:** https://calendly.com (interview scheduling)
- **Google Forms:** https://forms.google.com (surveys)
- **Zoom:** https://zoom.us (interviews)
- **Notion:** https://notion.so (notes organization)

### Testing
- **Lighthouse:** `npx lighthouse <url> --view`
- **Locust:** http://localhost:8089 (load testing UI)
- **BrowserStack:** https://browserstack.com (cross-browser testing)

---

## Budget Estimate

| Item | Cost | Notes |
|------|------|-------|
| PostHog (analytics) | $0 | Free tier: 1M events/mo |
| Sentry (errors) | $0 | Free tier: 5K errors/mo |
| Interview incentives | $250 | 10 × $25 gift cards |
| Survey tool | $0 | Google Forms (free) |
| BrowserStack | $29 | 1 month trial |
| **Total** | **$279** | One-time cost |

---

## Success Metrics (Phase 1)

By end of Week 4, we should have:

- ✅ **10+ user interviews** completed and transcribed
- ✅ **50+ survey responses** with insights extracted
- ✅ **Analytics installed** with 100+ events tracked
- ✅ **Benchmark results** documented (performance, load, errors)
- ✅ **Validation report** with go/no-go decision
- ✅ **Feature roadmap** prioritized by user feedback

---

## Next Steps After Phase 1

If **GO** decision:
→ Begin Phase 2: Architecture Refactoring (add tests, refactor, CI/CD)

If **ITERATE** decision:
→ Fix critical issues, re-run validation in 2 weeks

If **PIVOT** decision:
→ Review findings, consider major product changes or new direction

---

**Status:** Ready to begin  
**Start Date:** November 4, 2025  
**Review Date:** December 1, 2025  
**Owner:** [Your Name]
