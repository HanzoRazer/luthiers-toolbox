<script setup lang="ts">
/**
 * CalculatorResultCards - Grid of calculator output cards
 * Extracted from ArtStudioCalculatorDebugPanel.vue
 */
import type { CalculatorResult } from '@/stores/useArtStudioEngine'

defineProps<{
  result: CalculatorResult
}>()

function heatClass(category: string): string {
  switch (category) {
    case 'COOL':
      return 'ok'
    case 'WARM':
      return 'warn'
    case 'HOT':
      return 'danger'
    default:
      return ''
  }
}

function riskClass(risk: string): string {
  switch (risk) {
    case 'GREEN':
      return 'ok'
    case 'YELLOW':
      return 'warn'
    case 'RED':
      return 'danger'
    default:
      return ''
  }
}

function kickbackClass(category: string): string {
  switch (category) {
    case 'LOW':
      return 'ok'
    case 'MEDIUM':
      return 'warn'
    case 'HIGH':
      return 'danger'
    default:
      return ''
  }
}
</script>

<template>
  <div class="result-cards">
    <div
      v-if="result.chipload"
      class="result-card"
    >
      <h5>Chipload</h5>
      <p class="value">
        {{ result.chipload.chipload_mm?.toFixed(4) ?? "N/A" }} mm
      </p>
      <p
        class="status"
        :class="result.chipload.in_range ? 'ok' : 'warn'"
      >
        {{ result.chipload.in_range ? "✓ In Range" : "⚠ Out of Range" }}
      </p>
      <p class="message">
        {{ result.chipload.message }}
      </p>
    </div>

    <div
      v-if="result.bite_per_tooth"
      class="result-card"
    >
      <h5>Bite per Tooth</h5>
      <p class="value">
        {{ result.bite_per_tooth.bite_mm?.toFixed(4) ?? "N/A" }} mm
      </p>
      <p
        class="status"
        :class="result.bite_per_tooth.in_range ? 'ok' : 'warn'"
      >
        {{ result.bite_per_tooth.in_range ? "✓ In Range" : "⚠ Out of Range" }}
      </p>
      <p class="message">
        {{ result.bite_per_tooth.message }}
      </p>
    </div>

    <div
      v-if="result.heat"
      class="result-card"
    >
      <h5>Heat Risk</h5>
      <p class="value">
        {{ (result.heat.heat_risk * 100).toFixed(0) }}%
      </p>
      <p
        class="status"
        :class="heatClass(result.heat.category)"
      >
        {{ result.heat.category }}
      </p>
      <p class="message">
        {{ result.heat.message }}
      </p>
    </div>

    <div
      v-if="result.deflection"
      class="result-card"
    >
      <h5>Deflection</h5>
      <p class="value">
        {{ result.deflection.deflection_mm?.toFixed(4) ?? "N/A" }} mm
      </p>
      <p
        class="status"
        :class="riskClass(result.deflection.risk)"
      >
        {{ result.deflection.risk }}
      </p>
      <p class="message">
        {{ result.deflection.message }}
      </p>
    </div>

    <div
      v-if="result.rim_speed"
      class="result-card"
    >
      <h5>Rim Speed</h5>
      <p class="value">
        {{ result.rim_speed.surface_speed_m_per_min?.toFixed(1) ?? "N/A" }} m/min
      </p>
      <p
        class="status"
        :class="result.rim_speed.within_limits ? 'ok' : 'danger'"
      >
        {{ result.rim_speed.within_limits ? "✓ Within Limits" : "❌ EXCEEDS MAX" }}
      </p>
      <p class="message">
        {{ result.rim_speed.message }}
      </p>
    </div>

    <div
      v-if="result.kickback"
      class="result-card"
    >
      <h5>Kickback Risk</h5>
      <p class="value">
        {{ (result.kickback.risk_score * 100).toFixed(0) }}%
      </p>
      <p
        class="status"
        :class="kickbackClass(result.kickback.category)"
      >
        {{ result.kickback.category }}
      </p>
      <p class="message">
        {{ result.kickback.message }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.result-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.35rem;
}

.result-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 0.35rem;
}

.result-card h5 {
  font-size: 0.7rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.15rem;
}

.result-card .value {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.result-card .status {
  font-size: 0.7rem;
  font-weight: 500;
  margin: 0.1rem 0;
}

.result-card .status.ok {
  color: #198754;
}
.result-card .status.warn {
  color: #ffc107;
}
.result-card .status.danger {
  color: #dc3545;
}

.result-card .message {
  font-size: 0.65rem;
  color: #6c757d;
  margin: 0;
  line-height: 1.3;
}
</style>
