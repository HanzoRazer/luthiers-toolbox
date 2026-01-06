<template>
  <div class="analytics-dashboard">
    <div class="header-row">
      <div class="title-block">
        <h2>RMOS Analytics Dashboard</h2>
        <p class="subtitle">Patterns • Materials • Jobs • Advanced Signals</p>
      </div>
      <div class="summary-card" v-if="summaryReady">
        <div class="summary-item">
          <span class="k">Dur Anom:</span>
          <span class="v">{{ durationAnomalies.length }}</span>
        </div>
        <div class="summary-item">
          <span class="k">Succ Anom:</span>
          <span class="v">{{ successAnomalies.length }}</span>
        </div>
        <div class="summary-item" v-if="riskResult">
          <span class="k">Risk:</span>
          <span class="v" :class="riskClass(riskResult.risk_score)">{{ (riskResult.risk_score*100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <!-- Core Panels -->
    <section class="panel">
      <h3>Pattern Complexity</h3>
      <div v-if="loading.complexity" class="loading">Loading...</div>
      <div v-else class="grid">
        <div v-for="(val,key) in complexity" :key="key" class="grid-item">
          <span class="label">{{ key }}</span>
          <span class="value">{{ val }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Material Efficiency</h3>
      <div v-if="loading.efficiency" class="loading">Loading...</div>
      <div v-else class="grid">
        <div v-for="(m,idx) in materialEfficiency" :key="idx" class="grid-item">
          <span class="label">{{ m.material }}</span>
          <span class="value">{{ formatPct(m.efficiency) }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Job Status Distribution</h3>
      <div v-if="loading.status" class="loading">Loading...</div>
      <div v-else class="grid">
        <div v-for="(val,key) in statusDist" :key="key" class="grid-item">
          <span class="label">{{ key }}</span>
          <span class="value">{{ val }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Success Rate Trends</h3>
      <div v-if="loading.success" class="loading">Loading...</div>
      <div v-else class="trend">
        <div v-for="(pt,idx) in successTrend" :key="idx" class="trend-point">
          <span>{{ pt.date }}: {{ formatPct(pt.success_rate) }}</span>
        </div>
      </div>
    </section>

    <!-- Advanced Panels -->
    <section class="panel">
      <h3>Correlation Heatmap</h3>
      <div v-if="loading.correlation" class="loading">Loading correlations...</div>
      <div v-else-if="!correlation || correlation.matrix.length === 0" class="empty">No correlation data</div>
      <div v-else class="heatmap">
        <div class="heatmap-row header">
          <div class="cell header-cell"></div>
          <div v-for="(name,idx) in correlation.features" :key="'h_'+idx" class="cell header-cell">{{ name }}</div>
        </div>
        <div v-for="(row,ri) in correlation.matrix" :key="'r_'+ri" class="heatmap-row">
          <div class="cell header-cell">{{ correlation.features[ri] }}</div>
          <div v-for="(val,ci) in row" :key="ri+'_'+ci" class="cell" :style="{ backgroundColor: heatColor(val) }" :title="heatTitle(ri, ci, val)">
            {{ val.toFixed(2) }}
          </div>
        </div>
        <div class="legend">
          <span class="legend-title">Correlation Legend</span>
          <div class="legend-bar">
            <div class="legend-stop neg">-1</div>
            <div class="legend-stop mid">0</div>
            <div class="legend-stop pos">+1</div>
          </div>
          <span class="legend-notes">Blue=inverse • White=neutral • Red=direct</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Anomaly Alerts</h3>
      <div class="alerts">
        <div class="alerts-group">
          <h4>Duration</h4>
          <div v-if="loading.anomDurations" class="loading">Loading...</div>
          <div v-else-if="!durationAnomalies.length" class="empty">No duration anomalies</div>
          <ul v-else>
            <li v-for="(a,idx) in durationAnomalies" :key="'d_'+idx" :class="severityClass(a.z_score)">
              <span class="badge">z={{ a.z_score.toFixed(2) }}</span>
              <span>#{{ a.job_id }} — {{ a.job_type }} — {{ a.duration_min.toFixed(1) }}m</span>
            </li>
          </ul>
        </div>
        <div class="alerts-group">
          <h4>Success</h4>
          <div v-if="loading.anomSuccess" class="loading">Loading...</div>
          <div v-else-if="!successAnomalies.length" class="empty">No success anomalies</div>
          <ul v-else>
            <li v-for="(a,idx) in successAnomalies" :key="'s_'+idx" :class="severityClass(a.z_score)">
              <span class="badge">z={{ a.z_score.toFixed(2) }}</span>
              <span>{{ a.window_start }} → {{ a.window_end }} — {{ formatPct(a.success_rate) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Failure Risk Predictor</h3>
      <div class="risk-form">
        <label>
          Job Type
          <input v-model="riskForm.jobType" placeholder="e.g. Pocket" />
        </label>
        <label>
          Material
          <input v-model="riskForm.material" placeholder="e.g. Maple" />
        </label>
        <label>
          Tool Ø (mm)
          <input type="number" v-model.number="riskForm.toolDiameter" min="1" step="0.1" />
        </label>
        <button @click="predictRisk" :disabled="loading.predict">Predict</button>
      </div>
      <div v-if="loading.predict" class="loading">Predicting...</div>
      <div v-else-if="riskResult" class="risk-result" :class="riskClass(riskResult.risk_score)">
        <div class="risk-score">Risk: {{ (riskResult.risk_score*100).toFixed(0) }}%</div>
        <div class="risk-advice">{{ riskResult.advice }}</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

// Core state
const complexity = ref<Record<string, number>>({})
const materialEfficiency = ref<Array<{material:string, efficiency:number}>>([])
const statusDist = ref<Record<string, number>>({})
const successTrend = ref<Array<{date:string, success_rate:number}>>([])

// Advanced state
type CorrelationMatrix = { features: string[], matrix: number[][] }
const correlation = ref<CorrelationMatrix | null>(null)
const durationAnomalies = ref<Array<{job_id:number, job_type:string, duration_min:number, z_score:number}>>([])
const successAnomalies = ref<Array<{window_start:string, window_end:string, success_rate:number, z_score:number}>>([])
const riskForm = ref<{jobType:string; material:string; toolDiameter:number}>({ jobType:'Pocket', material:'Maple', toolDiameter:6.0 })
const riskResult = ref<{risk_score:number; advice:string} | null>(null)

// Loading flags
const loading = ref<Record<string, boolean>>({
  complexity:true,
  efficiency:true,
  status:true,
  success:true,
  correlation:true,
  anomDurations:true,
  anomSuccess:true,
  predict:false,
})

// Summary readiness
const summaryReady = computed(() => !loading.value.anomDurations && !loading.value.anomSuccess)

function formatPct(p:number){ return `${(p*100).toFixed(1)}%` }

// Fetchers (align with router paths)
async function fetchComplexity(){ try{ const r = await fetch('/api/analytics/pattern/complexity'); if(r.ok) complexity.value = await r.json() } finally { loading.value.complexity=false } }
async function fetchEfficiency(){ try{ const r = await fetch('/api/analytics/material/efficiency'); if(r.ok) materialEfficiency.value = await r.json() } finally { loading.value.efficiency=false } }
async function fetchStatus(){ try{ const r = await fetch('/api/analytics/job/status_distribution'); if(r.ok) statusDist.value = await r.json() } finally { loading.value.status=false } }
async function fetchSuccess(){ try{ const r = await fetch('/api/analytics/job/success_trends'); if(r.ok) successTrend.value = await r.json() } finally { loading.value.success=false } }
async function fetchCorrelation(){ try{ const r = await fetch('/api/analytics/advanced/correlation'); if(r.ok) correlation.value = await r.json(); else correlation.value={features:[],matrix:[]} } finally { loading.value.correlation=false } }
async function fetchDurationAnomalies(){ try{ const r = await fetch('/api/analytics/advanced/anomalies/durations'); durationAnomalies.value = r.ok ? await r.json() : [] } finally { loading.value.anomDurations=false } }
async function fetchSuccessAnomalies(){ try{ const r = await fetch('/api/analytics/advanced/anomalies/success'); successAnomalies.value = r.ok ? await r.json() : [] } finally { loading.value.anomSuccess=false } }
async function predictRisk(){ try{ loading.value.predict=true; const r = await fetch('/api/analytics/advanced/predict',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(riskForm.value) }); riskResult.value = r.ok? await r.json(): { risk_score:0, advice:'No prediction available'} } finally { loading.value.predict=false } }

// Helpers
function heatColor(val:number){ const v=Math.max(-1,Math.min(1,val)); const r=v>0?Math.round(255*v):0; const b=v<0?Math.round(255*-v):0; const g=255-Math.round(255*Math.abs(v)); return `rgb(${r},${g},${b})` }
function heatTitle(ri:number,ci:number,val:number){ if(!correlation.value) return ''; return `${correlation.value.features[ri]} vs ${correlation.value.features[ci]}: ${val.toFixed(3)}` }
function severityClass(z:number){ const az=Math.abs(z); if(az>=2.5) return 'alert critical'; if(az>=1.5) return 'alert warning'; return 'alert info' }
function riskClass(score:number){ if(score>=0.66) return 'risk high'; if(score>=0.33) return 'risk medium'; return 'risk low' }

onMounted(() => {
  fetchComplexity();
  fetchEfficiency();
  fetchStatus();
  fetchSuccess();
  fetchCorrelation();
  fetchDurationAnomalies();
  fetchSuccessAnomalies();
})
</script>

<style scoped>
.analytics-dashboard{ display:flex; flex-direction:column; gap:18px; padding:8px; }
.header-row{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; }
.title-block h2{ margin:0; font-size:20px; }
.subtitle{ margin:4px 0 0; color:#666; font-size:13px; }
.summary-card{ display:flex; gap:12px; background:#f7f9fc; border:1px solid #dbe3ec; padding:8px 12px; border-radius:8px; }
.summary-item{ display:flex; gap:4px; align-items:center; font-size:12px; }
.summary-item .k{ color:#555; }
.summary-item .v{ font-weight:600; }
.panel{ border:1px solid #e1e5ea; border-radius:8px; padding:12px; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,0.03); }
.loading{ color:#888; font-size:13px; }
.grid{ display:grid; grid-template-columns: repeat(auto-fill,minmax(140px,1fr)); gap:8px; }
.grid-item{ display:flex; justify-content:space-between; font-size:13px; background:#fafafa; border:1px solid #eee; padding:6px 8px; border-radius:6px; }
.label{ color:#555; }
.value{ font-weight:600; }
.trend{ display:flex; flex-direction:column; gap:4px; max-height:220px; overflow:auto; }
.trend-point{ font-family:monospace; font-size:12px; }
/* Heatmap */
.heatmap{ display:flex; flex-direction:column; gap:4px; overflow-x:auto; }
.heatmap-row{ display:flex; }
.cell{ width:90px; height:32px; display:flex; align-items:center; justify-content:center; color:#111; font-size:12px; border:1px solid #eee; }
.header-cell{ background:#f5f7fa; font-weight:600; }
.legend{ margin-top:8px; display:flex; flex-direction:column; gap:4px; font-size:11px; }
.legend-title{ font-weight:600; }
.legend-bar{ display:flex; width:270px; }
.legend-stop{ flex:1; text-align:center; padding:4px 0; border:1px solid #ddd; }
.legend-stop.neg{ background:rgb(0,120,255); color:#fff; }
.legend-stop.mid{ background:#ffffff; }
.legend-stop.pos{ background:rgb(255,80,80); color:#fff; }
.legend-notes{ color:#555; }
/* Alerts */
.alerts{ display:flex; gap:16px; flex-wrap:wrap; }
.alerts-group{ flex:1; min-width:240px; }
.alerts-group ul{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:6px; }
.alert{ padding:6px 8px; border-radius:6px; display:flex; align-items:center; gap:8px; font-size:12px; }
.alert.info{ background:#f4f7ff; border:1px solid #cfe0ff; }
.alert.warning{ background:#fff7e6; border:1px solid #ffe0a3; }
.alert.critical{ background:#ffecec; border:1px solid #ffb3b3; }
.badge{ background:#fff; border:1px solid #ddd; border-radius:4px; padding:2px 6px; font-size:11px; }
.empty{ color:#999; font-size:12px; }
/* Risk */
.risk-form{ display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap; margin-bottom:8px; }
.risk-form label{ display:flex; flex-direction:column; gap:4px; font-size:12px; }
.risk-form input{ padding:6px 8px; border:1px solid #ccc; border-radius:6px; font-size:13px; }
.risk-form button{ padding:8px 14px; background:#0057d8; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px; }
.risk-form button:disabled{ opacity:.6; cursor:default; }
.risk-result{ margin-top:4px; padding:10px; border-radius:8px; font-size:13px; }
.risk.low{ background:#f1fff1; border:1px solid #c6e9c6; }
.risk.medium{ background:#fffbe6; border:1px solid #ffe8a3; }
.risk.high{ background:#fff1f1; border:1px solid #ffb3b3; }
.risk-score{ font-weight:700; }
.risk-advice{ color:#444; margin-top:2px; }
</style>
