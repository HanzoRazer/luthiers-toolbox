# N9.0 Analytics Engine — Quick Reference

**Status:** ✅ Production Ready  
**Version:** N9.0  
**Files:** 7 (6 new + 1 updated)  
**Lines:** ~2,800  
**Endpoints:** 18 REST APIs

---

## 🚀 Quick Start

### **1. Start API**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **2. Test Endpoints**
```powershell
.\scripts\Test-Analytics-N9.ps1
```

### **3. Use Dashboard**
```vue
<script setup>
import AnalyticsDashboard from '@/components/rmos/AnalyticsDashboard.vue'
</script>

<template>
  <AnalyticsDashboard />
</template>
```

---

## 📡 API Endpoints

### **Pattern Analytics**

```bash
# Complexity distribution (Simple/Medium/Complex/Expert)
GET /api/analytics/patterns/complexity

# Ring statistics (min/max/avg/median)
GET /api/analytics/patterns/rings

# Geometry metrics (radius, segments, density)
GET /api/analytics/patterns/geometry

# Strip family usage
GET /api/analytics/patterns/families

# Top patterns by job count
GET /api/analytics/patterns/popularity?limit=10

# Single pattern analytics
GET /api/analytics/patterns/{pattern_id}/details
```

### **Material Analytics**

```bash
# Material type distribution
GET /api/analytics/materials/distribution

# Strip consumption (count, length, dimensions)
GET /api/analytics/materials/consumption

# Material efficiency (waste %, success rates)
GET /api/analytics/materials/efficiency

# Dimensional analysis (width/thickness ranges)
GET /api/analytics/materials/dimensions

# Supplier analytics (quality metrics)
GET /api/analytics/materials/suppliers

# Inventory status
GET /api/analytics/materials/inventory
```

### **Job Analytics**

```bash
# Success rate trends (daily)
GET /api/analytics/jobs/success-trends?days=30

# Duration analysis by job type
GET /api/analytics/jobs/duration

# Status distribution
GET /api/analytics/jobs/status

# Throughput metrics (jobs per day/week/month)
GET /api/analytics/jobs/throughput

# Failure analysis (by type/pattern/material)
GET /api/analytics/jobs/failures

# Job type distribution
GET /api/analytics/jobs/types

# Recent jobs summary
GET /api/analytics/jobs/recent?limit=10
```

---

## 🔢 Key Algorithms

### **Pattern Complexity Score**
```python
score = ring_count * 10 + (total_segments / 100) * 5

# Categories:
# 0-30   = Simple
# 31-60  = Medium
# 61-100 = Complex
# 100+   = Expert
```

### **Ring Density**
```python
density = total_segments / (2 * π * radius_mm)
# Units: segments per mm of circumference
```

### **Material Efficiency**
```python
efficiency = 100 - avg_waste_percentage
# Range: 0-100 (higher = better)
```

### **Success Rate**
```python
success_rate = (completed_jobs / total_jobs) * 100
```

---

## 📊 Dashboard Components

### **Stats Cards**
- Total patterns
- Total materials
- Overall success rate
- Average jobs per day

### **Charts**
1. **Bar Chart**: Pattern complexity distribution
2. **Bar Chart**: Material efficiency (top 5)
3. **Donut Chart**: Job status distribution
4. **Line Chart**: Success rate trend (30 days)

### **Color Coding**

**Complexity**:
- 🟢 Green: Simple (0-30)
- 🔵 Blue: Medium (31-60)
- 🟠 Orange: Complex (61-100)
- 🔴 Red: Expert (100+)

**Efficiency**:
- 🟢 Green: 80%+ (excellent)
- 🟡 Yellow-Green: 60-80% (good)
- 🟠 Orange: 40-60% (fair)
- 🔴 Red: <40% (poor)

**Status**:
- 🟢 Green: completed
- 🔴 Red: failed
- 🟠 Orange: pending
- 🔵 Blue: running

---

## 🧪 Testing

### **Run All Tests**
```powershell
.\scripts\Test-Analytics-N9.ps1
```

### **Expected Output**
```
=== N9.0 RMOS Analytics Engine Test Suite ===

=== Pattern Analytics ===
1. ✓ Complexity distribution retrieved
2. ✓ Ring statistics retrieved
...
18. ✓ Recent jobs retrieved

=== Test Summary ===
  Passed: 18
  Failed: 0

✓ All N9.0 Analytics Engine tests passed!
```

### **Manual Testing**
```powershell
# Test single endpoint
curl http://localhost:8000/api/analytics/patterns/complexity

# Test with query params
curl "http://localhost:8000/api/analytics/jobs/success-trends?days=7"

# Test pattern details
curl http://localhost:8000/api/analytics/patterns/{pattern_id}/details
```

---

## 📁 File Structure

```
services/api/app/
├── analytics/
│   ├── __init__.py                 # Package initializer
│   ├── pattern_analytics.py        # Pattern complexity engine (339 lines)
│   ├── material_analytics.py       # Material efficiency engine (367 lines)
│   └── job_analytics.py            # Job performance engine (393 lines)
├── routers/
│   └── analytics_router.py         # REST API endpoints (399 lines)
└── main.py                          # Router registration (updated)

packages/client/src/components/rmos/
└── AnalyticsDashboard.vue           # Interactive dashboard (637 lines)

scripts/
└── Test-Analytics-N9.ps1            # PowerShell test suite (463 lines)

docs/
├── N9_0_ANALYTICS_COMPLETE.md       # Full documentation
└── N9_0_ANALYTICS_QUICKREF.md       # This file
```

---

## 🔧 Common Use Cases

### **1. View Pattern Complexity Breakdown**
```typescript
const response = await fetch('/api/analytics/patterns/complexity')
const data = await response.json()

// data.categories = {
//   "Simple": { count: 5, percentage: 33.3 },
//   "Medium": { count: 7, percentage: 46.7 },
//   "Complex": { count: 2, percentage: 13.3 },
//   "Expert": { count: 1, percentage: 6.7 }
// }
```

### **2. Check Material Efficiency**
```typescript
const response = await fetch('/api/analytics/materials/efficiency')
const data = await response.json()

// data.by_material = {
//   "Maple": { efficiency_score: 85.2, success_rate: 92.1 },
//   "Walnut": { efficiency_score: 78.4, success_rate: 88.5 },
//   ...
// }
```

### **3. Monitor Success Rate Trends**
```typescript
const response = await fetch('/api/analytics/jobs/success-trends?days=30')
const data = await response.json()

// data.daily_trends = [
//   { date: "2025-01-01", total_jobs: 12, completed: 10, success_rate: 83.3 },
//   { date: "2025-01-02", total_jobs: 15, completed: 14, success_rate: 93.3 },
//   ...
// ]
```

### **4. Find Top Patterns**
```typescript
const response = await fetch('/api/analytics/patterns/popularity?limit=5')
const data = await response.json()

// data.top_patterns = [
//   { pattern_name: "Celtic Knot", job_count: 45 },
//   { pattern_name: "Herringbone", job_count: 38 },
//   ...
// ]
```

---

## 🐛 Troubleshooting

### **No Data in Dashboard**
**Cause**: RMOS stores empty  
**Fix**: Seed data with N8.6 endpoints or run N8.7 migration

### **Success Trends Empty**
**Cause**: Jobs missing `created_at` timestamps  
**Fix**: Ensure ISO format: `YYYY-MM-DDTHH:MM:SS`

### **Material Efficiency 0%**
**Cause**: Jobs missing `waste_percentage` in metadata  
**Fix**: Add waste percentage to job metadata

### **Charts Not Rendering**
**Cause**: Browser compatibility or fetch errors  
**Fix**: Check console, ensure Vue 3 + fetch API supported

---

## 🎯 Query Parameters

| Endpoint | Parameter | Type | Range | Default | Description |
|----------|-----------|------|-------|---------|-------------|
| `/patterns/popularity` | `limit` | int | 1-100 | 10 | Max patterns to return |
| `/jobs/success-trends` | `days` | int | 1-365 | 30 | Days to analyze |
| `/jobs/recent` | `limit` | int | 1-100 | 10 | Max jobs to return |

---

## 📊 Response Examples

### **Pattern Complexity**
```json
{
  "total_patterns": 15,
  "categories": {
    "Simple": { "count": 5, "percentage": 33.3 },
    "Medium": { "count": 7, "percentage": 46.7 },
    "Complex": { "count": 2, "percentage": 13.3 },
    "Expert": { "count": 1, "percentage": 6.7 }
  }
}
```

### **Material Efficiency**
```json
{
  "by_material": {
    "Maple": {
      "total_strips": 120,
      "avg_waste_percentage": 12.5,
      "success_rate": 92.1,
      "efficiency_score": 87.5
    }
  }
}
```

### **Success Trends**
```json
{
  "period_days": 30,
  "overall_success_rate": 88.4,
  "daily_trends": [
    {
      "date": "2025-01-01",
      "total_jobs": 12,
      "completed": 10,
      "failed": 2,
      "success_rate": 83.3
    }
  ]
}
```

### **Job Status Distribution**
```json
{
  "total_jobs": 500,
  "distribution": {
    "completed": { "count": 420, "percentage": 84.0 },
    "failed": { "count": 50, "percentage": 10.0 },
    "pending": { "count": 30, "percentage": 6.0 }
  },
  "most_common": {
    "status": "completed",
    "count": 420,
    "percentage": 84.0
  }
}
```

---

## 🚀 Next Steps

### **Integration Tasks**
1. Add dashboard to main navigation menu
2. Connect to RMOS sandbox UI
3. Add analytics route to router
4. Create analytics landing page

### **Enhancement Ideas**
- **N9.1**: Advanced analytics (correlations, predictions, anomalies)
- **N9.2**: Export & reports (CSV, PDF, email)
- **N9.3**: Real-time analytics (WebSocket, streaming)
- **N9.4**: Custom analytics (user-defined metrics)

---

## 📚 Related Docs

- [N9.0 Complete Summary](./N9_0_ANALYTICS_COMPLETE.md) — Full documentation
- [N8.6 RMOS Stores](./N8_6_RMOS_STORES_SUMMARY.md) — Data layer
- [N8.7 Migration System](./N8_7_MIGRATION_COMPLETE.md) — Legacy migration
- [RMOS Quickref](./RMOS_QUICKREF.md) — API overview

---

**Status:** ✅ Production Ready  
**Build:** ~2,800 lines  
**Endpoints:** 18 REST APIs  
**Tests:** 18 comprehensive validations  
**Dashboard:** Full analytics UI
