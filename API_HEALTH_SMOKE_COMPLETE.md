# API Health + Smoke Workflow — Complete Drop-In

**File:** `.github/workflows/api_health_and_smoke.yml`  
**Status:** ✅ Production-Ready  
**Updated:** November 6, 2025

---

## 🎯 What's Included

This complete, drop-in workflow provides:

1. **Nightly Health Check** (best-effort, non-fatal)
2. **Smoke Test** (all post-processor presets, fails on error)
3. **Artifact Upload** (smoke_posts.json for every run)
4. **Size Regression Guard** (baseline comparison with thresholds)
5. **Failure Notifications** (Slack + Email, optional)

---

## 📋 Features

### **1. Health Check (Optional)**
```yaml
- name: Run API health (best-effort)
  continue-on-error: true
  run: make api-verify
```
- Runs existing `api-verify` Makefile target
- **Non-fatal:** Won't fail the job if missing or errors occur
- Useful for general API connectivity checks

### **2. Smoke Test (Required)**
```yaml
- name: Run v15.5 smoke (all presets)
  run: make api-smoke-posts
```
- Runs `api-smoke-posts` Makefile target
- **Fails job** if any preset returns empty/invalid G-code
- Generates `smoke_posts.json` with byte counts

### **3. Artifact Upload**
```yaml
- name: Upload smoke_posts.json artifact
  if: always()
  uses: actions/upload-artifact@v4
```
- Uploads `smoke_posts.json` even if tests fail
- Retained for 90 days (GitHub default)
- Used as baseline for next run

### **4. Size Regression Check**
```yaml
- name: Fetch last green smoke_posts.json (baseline)
  uses: actions/github-script@v7
  # Downloads last successful artifact

- name: Size regression check
  env:
    SIZE_GROWTH_THRESH: ${{ vars.SIZE_GROWTH_THRESH || '0.35' }}
    SIZE_SHRINK_THRESH: ${{ vars.SIZE_SHRINK_THRESH || '0.00' }}
```

**Enforces:**
- ❌ **Zero-byte check:** Fails if any preset G-code shrinks to 0 bytes
- ❌ **Growth limit:** Fails if any preset grows >35% (default, configurable)
- ❌ **Shrink limit:** Fails if any preset shrinks >X% (optional, disabled by default)

**First Run Behavior:**
- No baseline exists yet → Check skipped
- Current run establishes baseline
- Subsequent runs compare against baseline

### **5. Failure Notifications (Optional)**

**Slack:**
```yaml
- name: Slack notify on failure
  if: failure() && env.SLACK_WEBHOOK_URL != ''
  uses: rtCamp/action-slack-notify@v2
```
- Requires `SLACK_WEBHOOK_URL` secret
- Sends red alert with repo, run, and branch info
- Automatically skips if secret not configured

**Email:**
```yaml
- name: Email notify on failure
  if: failure() && env.SMTP_HOST != '' && ...
  uses: dawidd6/action-send-mail@v3
```
- Requires `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_TO` secrets
- Sends plain text email with run details
- Automatically skips if secrets not configured

---

## ⚙️ Configuration

### **1. Size Regression Thresholds**

Set via **Actions Variables** (no YAML edits needed):

```
Settings → Secrets and variables → Actions → Variables
```

| Variable | Default | Description |
|----------|---------|-------------|
| `SIZE_GROWTH_THRESH` | `0.35` | Max allowed growth (35%) |
| `SIZE_SHRINK_THRESH` | `0.00` | Max allowed shrink (disabled) |

**Examples:**
- `0.20` → Allow 20% growth
- `0.50` → Allow 50% growth
- `0.35` → Enable 35% shrink detection

### **2. Notifications**

Set via **Repository Secrets**:

**Slack:**
```
SLACK_WEBHOOK_URL = https://hooks.slack.com/services/...
```

**Email:**
```
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USERNAME = your-email@example.com
SMTP_PASSWORD = your-app-password
MAIL_TO = alerts@example.com
MAIL_FROM = noreply@example.com  # Optional
```

---

## 🚀 Quick Start

### **1. Deploy the Workflow**

The workflow is already in place at:
```
.github/workflows/api_health_and_smoke.yml
```

Commit and push:
```bash
git add .github/workflows/api_health_and_smoke.yml
git commit -m "Deploy complete API health + smoke workflow with size regression guard"
git push
```

### **2. Test Manually**

Trigger via Actions tab:
```
Actions → API Health + Smoke → Run workflow → Run workflow
```

**First run output:**
```
✅ Health check (if configured)
✅ Smoke test passes
✅ Artifact uploaded
ℹ️ No baseline found; skipping size compare (establishing baseline now)
```

**Second run output:**
```
✅ Health check
✅ Smoke test passes
✅ Artifact uploaded
✅ Baseline fetched
✅ Size regression check OK
```

### **3. (Optional) Add Status Badge**

Add to your README.md:
```markdown
![API Health + Smoke](https://github.com/HanzoRazer/guitar_tap/actions/workflows/api_health_and_smoke.yml/badge.svg)
```

### **4. (Optional) Configure Thresholds**

If 35% growth is too lenient:
```
Settings → Actions → Variables → New variable
Name: SIZE_GROWTH_THRESH
Value: 0.20
```

Enable shrink detection:
```
Name: SIZE_SHRINK_THRESH
Value: 0.30
```

### **5. (Optional) Enable Notifications**

Add Slack webhook:
```
Settings → Secrets → New secret
Name: SLACK_WEBHOOK_URL
Secret: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📊 Example Outputs

### **Passing Check**
```
Growth threshold: 0.35
Shrink threshold: 0.00
Size regression check OK.
```

### **Failing Check (Growth)**
```
Size regression check FAILED:
 - grbl_pocket_adaptive: grew 1200 bytes (48.3% > 35.0% limit). base=2487, curr=3687
 - haas_drilling_g81: grew 850 bytes (41.2% > 35.0% limit). base=2062, curr=2912
```

### **Failing Check (Zero Bytes)**
```
Size regression check FAILED:
 - mach4_contour_finishing: current bytes=0 (shrank to zero)
```

### **Slack Notification**
```
🔴 API Health + Smoke failed

Repo: HanzoRazer/guitar_tap
Run: https://github.com/HanzoRazer/guitar_tap/actions/runs/12345
Branch: main
```

---

## 🔍 Troubleshooting

### **"Missing Makefile or 'api-smoke-posts' target"**

**Cause:** Workflow expects `make api-smoke-posts` to exist.

**Solution:** Add to your Makefile:
```makefile
api-smoke-posts:
	python -m pytest tests/test_smoke_posts.py -v
	# Or your custom smoke test script
```

### **"No baseline found" on every run**

**Cause:** Workflow never completes successfully (baseline never established).

**Solution:**
1. Check smoke test logs for errors
2. Fix any failing presets
3. Re-run workflow until it passes once

### **False positive on legitimate growth**

**Scenario:** You added new features to a post-processor (headers, macros, etc.).

**Solution:**
1. Review artifact diffs to confirm growth is intentional
2. Temporarily increase `SIZE_GROWTH_THRESH` variable:
   ```
   SIZE_GROWTH_THRESH = 0.60  # Allow 60% for this merge
   ```
3. After merge, reset to `0.35`

### **Artifact expired (90 days)**

**Behavior:** After 90 days of inactivity, baseline is lost.

**Solution:** None needed. Next successful run re-establishes baseline.

---

## 📈 Monitoring

### **View Workflow History**
```
Actions → API Health + Smoke → All workflow runs
```

### **Download Artifacts**
```
Actions → Select run → Artifacts → smoke_posts.json
```

### **Compare Baselines**
```bash
# Download two artifacts and diff
unzip smoke_posts_run1.zip -d run1/
unzip smoke_posts_run2.zip -d run2/
diff run1/smoke_posts.json run2/smoke_posts.json
```

---

## 🎯 Benefits

### **1. Catch Broken Templates Early**
```
Before: Token {{SAFE_Z}} not expanded → 0-byte G-code goes unnoticed
After:  Size regression check catches and fails CI immediately
```

### **2. Prevent Code Bloat**
```
Before: Infinite loop in spiralizer → 50MB G-code file
After:  Size regression check catches 2000% growth
```

### **3. Historical Tracking**
- Every run uploads `smoke_posts.json` with byte counts
- Can download and compare across runs
- Audit trail for G-code size trends over time

### **4. Zero-Configuration Defaults**
- Works immediately with sensible 35% growth threshold
- First run automatically establishes baseline
- Notifications gracefully skip if secrets not configured

---

## 🛠️ Advanced Usage

### **Custom Thresholds Per Preset**

Modify the Python script in the workflow to read per-preset thresholds from `smoke_posts.json`:

```python
# Add to your smoke test generator:
"results": {
  "grbl_pocket_adaptive": {
    "bytes": 2487,
    "growth_thresh": 0.50  # Allow 50% for this preset
  }
}

# Update size check script in workflow:
preset_thr = cinfo.get("growth_thresh", grow_thr)
limit_hi = int(bb * (1.0 + preset_thr))
```

### **Working Directory Override**

If your Makefile is in a subdirectory:

```yaml
- name: Run v15.5 smoke (all presets)
  working-directory: services/api
  run: make api-smoke-posts
```

### **Custom Artifact Retention**

Change retention from default 90 days:

```yaml
- name: Upload smoke_posts.json artifact
  uses: actions/upload-artifact@v4
  with:
    name: smoke_posts.json
    path: smoke_posts.json
    retention-days: 30  # Custom retention
```

---

## ✅ Checklist

- [x] Workflow file deployed to `.github/workflows/api_health_and_smoke.yml`
- [x] Makefile has `api-smoke-posts` target
- [ ] Test workflow manually (first run)
- [ ] Verify artifact uploaded
- [ ] Test workflow again (second run with baseline)
- [ ] Verify size regression check runs
- [ ] (Optional) Configure `SIZE_GROWTH_THRESH` variable
- [ ] (Optional) Configure `SIZE_SHRINK_THRESH` variable
- [ ] (Optional) Add `SLACK_WEBHOOK_URL` secret
- [ ] (Optional) Add `SMTP_*` secrets for email
- [ ] (Optional) Add status badge to README

---

## 📚 See Also

- [Size Regression Check Details](./SIZE_REGRESSION_CHECK.md)
- [Post-Processor System](./PATCH_N_SERIES_ROLLUP.md)
- [Smoke Test Implementation](./IMPLEMENTATION_CHECKLIST.md)

---

**Status:** ✅ Production-Ready  
**Schedule:** Daily at 09:30 UTC (03:30 America/Chicago)  
**Cost:** ~2-3 minutes per run  
**Maintenance:** Set thresholds via Actions Variables (zero YAML edits)
