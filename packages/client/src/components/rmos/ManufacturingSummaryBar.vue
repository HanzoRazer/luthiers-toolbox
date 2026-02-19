<template>
  <div class="mfg-topbar">
    <div class="mfg-summary">
      <!-- Run Ready Badge -->
      <div class="runReady">
        <span class="runReadyLabel">Run:</span>
        <span
          class="runReadyBadge"
          :class="runReadyBadgeClass"
          :title="runReadyHover"
        >
          {{ runReadyLabel }}
        </span>
      </div>
      <div class="kpi">
        <div class="kpi-label">Total</div>
        <div class="kpi-value">{{ totalCount }}</div>
      </div>
      <div class="kpi kpi-green">
        <div class="kpi-label">GREEN</div>
        <div class="kpi-value">{{ greenCount }}</div>
      </div>
      <div class="kpi kpi-muted">
        <div class="kpi-label">Undecided</div>
        <div class="kpi-value">{{ undecidedCount }}</div>
      </div>
      <div class="kpi kpi-yellow">
        <div class="kpi-label">YELLOW</div>
        <div class="kpi-value">{{ yellowCount }}</div>
      </div>
      <div class="kpi kpi-red">
        <div class="kpi-label">RED</div>
        <div class="kpi-value">{{ redCount }}</div>
      </div>
    </div>

    <div class="mfg-export">
      <input
        :value="packageName"
        class="inputSmall"
        placeholder="Optional package name…"
        :disabled="bulkPackaging"
        @input="$emit('update:packageName', ($event.target as HTMLInputElement).value)"
      >
      <button
        class="btn primary"
        type="button"
        :disabled="!!exportDisabledReason"
        :title="exportDisabledReason || 'Download one ZIP containing all GREEN candidate zips + manifest.json'"
        @click="$emit('exportPackage')"
      >
        {{ bulkPackaging ? 'Packaging…' : 'Export GREEN-only package' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  totalCount: number
  greenCount: number
  undecidedCount: number
  yellowCount: number
  redCount: number
  runReadyLabel: string
  runReadyHover: string
  runReadyBadgeClass: string
  packageName: string
  bulkPackaging: boolean
  exportDisabledReason: string | null
}>()

defineEmits<{
  'update:packageName': [value: string]
  exportPackage: []
}>()
</script>

<style scoped>
.mfg-topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
}

.mfg-summary {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.runReady {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  padding: 8px 10px;
}

.runReadyLabel {
  font-size: 11px;
  opacity: 0.65;
}

.runReadyBadge {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.4px;
  border-radius: 999px;
  padding: 6px 10px;
  user-select: none;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.badgeReady {
  background: rgba(34, 197, 94, 0.14);
}

.badgeBlocked {
  background: rgba(239, 68, 68, 0.12);
}

.badgeEmpty {
  background: rgba(107, 114, 128, 0.12);
}

.kpi {
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
  padding: 8px 12px;
  min-width: 72px;
  background: white;
  text-align: center;
}

.kpi-label {
  font-size: 11px;
  opacity: 0.65;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.kpi-value {
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.kpi-green { border-color: #22c55e; }
.kpi-green .kpi-value { color: #16a34a; }

.kpi-yellow { border-color: #eab308; }
.kpi-yellow .kpi-value { color: #ca8a04; }

.kpi-red { border-color: #ef4444; }
.kpi-red .kpi-value { color: #dc2626; }

.kpi-muted { border-color: #9ca3af; }
.kpi-muted .kpi-value { color: #6b7280; }

.mfg-export {
  display: flex;
  gap: 8px;
  align-items: center;
}

.inputSmall {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #ccc;
  min-width: 180px;
}

.btn {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn.primary {
  background: #2563eb;
  color: white;
  border-color: #1d4ed8;
}

.btn.primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn.primary:disabled {
  background: #93c5fd;
  border-color: #93c5fd;
  cursor: not-allowed;
}
</style>
