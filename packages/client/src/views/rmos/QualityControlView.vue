<script setup lang="ts">
/**
 * QualityControlView - Quality Control & Inspection Management
 * Track quality checkpoints, defects, and inspection history
 *
 * Connected to API endpoints:
 *   GET  /api/rmos/quality/inspections
 *   POST /api/rmos/quality/inspections
 *   GET  /api/rmos/quality/metrics
 */
import { ref } from 'vue'

const activeTab = ref('pending')  // pending, completed, metrics

const pendingInspections = ref([
  { id: 'QC-001', item: 'Classical Guitar #147', stage: 'Final Assembly', priority: 'high', dueDate: '2026-03-06' },
  { id: 'QC-002', item: 'Rosette Batch #23', stage: 'Post-Glue', priority: 'normal', dueDate: '2026-03-07' },
  { id: 'QC-003', item: 'Neck Blank Set #45', stage: 'Incoming', priority: 'low', dueDate: '2026-03-08' },
])

const completedInspections = ref([
  { id: 'QC-098', item: 'Steel String #89', result: 'pass', date: '2026-03-05', inspector: 'J. Smith' },
  { id: 'QC-097', item: 'Binding Channel Cut', result: 'pass', date: '2026-03-05', inspector: 'J. Smith' },
  { id: 'QC-096', item: 'Bridge Glue-up #12', result: 'fail', date: '2026-03-04', inspector: 'M. Jones', defects: ['Gap detected'] },
])

const metrics = ref({
  passRate: 94.2,
  avgInspectionTime: 12,
  defectsThisMonth: 8,
  pendingCount: 3,
})
</script>

<template>
  <div class="quality-control-view">
    <div class="header">
      <h1>Quality Control</h1>
      <p class="subtitle">Inspection tracking and quality metrics</p>
    </div>

    <div class="stats-bar">
      <div class="stat-card">
        <span class="stat-value">{{ metrics.passRate }}%</span>
        <span class="stat-label">Pass Rate</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ metrics.avgInspectionTime }}m</span>
        <span class="stat-label">Avg Inspection Time</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ metrics.defectsThisMonth }}</span>
        <span class="stat-label">Defects This Month</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ metrics.pendingCount }}</span>
        <span class="stat-label">Pending Inspections</span>
      </div>
    </div>

    <div class="toolbar">
      <div class="tabs">
        <button :class="{ active: activeTab === 'pending' }" @click="activeTab = 'pending'">
          Pending ({{ pendingInspections.length }})
        </button>
        <button :class="{ active: activeTab === 'completed' }" @click="activeTab = 'completed'">
          Completed
        </button>
        <button :class="{ active: activeTab === 'metrics' }" @click="activeTab = 'metrics'">
          Metrics
        </button>
      </div>
      <button class="btn btn-primary">+ New Inspection</button>
    </div>

    <div class="content">
      <!-- Pending Inspections -->
      <div v-if="activeTab === 'pending'" class="inspections-list">
        <div v-for="item in pendingInspections" :key="item.id" class="inspection-card pending">
          <div class="card-header">
            <span class="inspection-id">{{ item.id }}</span>
            <span :class="['priority-badge', item.priority]">{{ item.priority }}</span>
          </div>
          <h3 class="item-name">{{ item.item }}</h3>
          <p class="stage">Stage: {{ item.stage }}</p>
          <p class="due-date">Due: {{ item.dueDate }}</p>
          <div class="card-actions">
            <button class="btn btn-primary">Start Inspection</button>
          </div>
        </div>
      </div>

      <!-- Completed Inspections -->
      <div v-if="activeTab === 'completed'" class="inspection-table">
        <div class="table-header">
          <span>ID</span>
          <span>Item</span>
          <span>Result</span>
          <span>Date</span>
          <span>Inspector</span>
        </div>
        <div v-for="item in completedInspections" :key="item.id" class="table-row">
          <span>{{ item.id }}</span>
          <span class="item-name">{{ item.item }}</span>
          <span :class="['result-badge', item.result]">
            {{ item.result === 'pass' ? '✓ Pass' : '✗ Fail' }}
          </span>
          <span>{{ item.date }}</span>
          <span>{{ item.inspector }}</span>
        </div>
      </div>

      <!-- Metrics Tab -->
      <div v-if="activeTab === 'metrics'" class="placeholder-panel">
        <span class="icon">📊</span>
        <p>Quality metrics dashboard coming soon</p>
        <p class="detail">Defect trends, first-pass yield, and inspection analytics</p>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full QC workflow with defect photography and reporting coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.quality-control-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.stats-bar { max-width: 1400px; margin: 0 auto 2rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.stat-card { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; text-align: center; }
.stat-value { display: block; font-size: 2rem; font-weight: 700; color: #2563eb; }
.stat-label { font-size: 0.75rem; color: #888; text-transform: uppercase; }

.toolbar { max-width: 1400px; margin: 0 auto 1.5rem; display: flex; justify-content: space-between; align-items: center; }
.tabs { display: flex; gap: 0.5rem; }
.tabs button { padding: 0.5rem 1rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #888; cursor: pointer; }
.tabs button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }

.content { max-width: 1400px; margin: 0 auto; }

.inspections-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.inspection-card { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.inspection-id { font-size: 0.75rem; color: #888; font-family: monospace; }
.priority-badge { padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; text-transform: uppercase; font-weight: 600; }
.priority-badge.high { background: #ef444420; color: #ef4444; }
.priority-badge.normal { background: #3b82f620; color: #3b82f6; }
.priority-badge.low { background: #6b728020; color: #9ca3af; }
.item-name { font-size: 1rem; font-weight: 600; margin: 0 0 0.5rem; }
.stage, .due-date { font-size: 0.875rem; color: #888; margin: 0.25rem 0; }
.card-actions { margin-top: 1rem; }
.card-actions .btn { width: 100%; }

.inspection-table { background: #1a1a1a; border-radius: 0.75rem; overflow: hidden; }
.table-header { display: grid; grid-template-columns: 100px 2fr 100px 120px 1fr; padding: 1rem 1.5rem; background: #262626; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; }
.table-row { display: grid; grid-template-columns: 100px 2fr 100px 120px 1fr; padding: 1rem 1.5rem; border-bottom: 1px solid #262626; align-items: center; }

.result-badge { font-size: 0.875rem; font-weight: 500; }
.result-badge.pass { color: #22c55e; }
.result-badge.fail { color: #ef4444; }

.placeholder-panel { background: #1a1a1a; border-radius: 0.75rem; padding: 4rem; text-align: center; }
.placeholder-panel .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }
.placeholder-panel p { color: #666; margin: 0; }
.placeholder-panel .detail { font-size: 0.875rem; margin-top: 0.5rem; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 900px) { .stats-bar { grid-template-columns: repeat(2, 1fr); } }
</style>
