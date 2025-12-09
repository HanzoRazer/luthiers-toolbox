<template>
  <div class="feasibility-panel">
    <h3 class="feasibility-panel__title">
      <span>Feasibility</span>
      <span
        v-if="feasibility"
        class="feasibility-panel__badge"
        :class="badgeClass"
      >
        {{ overallScore }}%
      </span>
    </h3>

    <!-- No data state -->
    <div v-if="!feasibility" class="feasibility-panel__empty">
      <p>Run feasibility check to see results.</p>
    </div>

    <!-- Results -->
    <template v-else>
      <!-- Global Risk Summary -->
      <div v-if="globalRisk.risk !== 'none'" class="feasibility-panel__section">
        <h4>
          <span class="risk-badge" :class="`risk-badge--${globalRisk.risk}`">
            {{ riskLabel(globalRisk.risk) }}
          </span>
          Global Risk
        </h4>
        <ul class="feasibility-panel__list">
          <li v-for="(msg, i) in globalRisk.messages" :key="'global-' + i">
            {{ msg }}
          </li>
        </ul>
      </div>

      <!-- Hard Failures -->
      <div
        v-if="hardFailures.length"
        class="feasibility-panel__section feasibility-panel__section--fail"
      >
        <h4>❌ Hard Failures ({{ hardFailures.length }})</h4>
        <ul class="feasibility-panel__list">
          <li v-for="(fail, i) in hardFailures" :key="'fail-' + i">
            {{ fail }}
          </li>
        </ul>
      </div>

      <!-- Warnings -->
      <div
        v-if="warnings.length"
        class="feasibility-panel__section feasibility-panel__section--warn"
      >
        <h4>⚠️ Warnings ({{ warnings.length }})</h4>
        <ul class="feasibility-panel__list">
          <li v-for="(warn, i) in warnings" :key="'warn-' + i">
            {{ warn }}
          </li>
        </ul>
      </div>

      <!-- Per-Path Risks -->
      <div v-if="pathRisks.length" class="feasibility-panel__section">
        <h4>Path Risks ({{ pathRisks.length }})</h4>
        <table class="feasibility-panel__table">
          <thead>
            <tr>
              <th>Path</th>
              <th>Risk</th>
              <th>Issues</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pr in pathRisks" :key="pr.pathId">
              <td class="path-id">{{ truncateId(pr.pathId) }}</td>
              <td>
                <span class="risk-badge" :class="`risk-badge--${pr.risk}`">
                  {{ riskLabel(pr.risk) }}
                </span>
              </td>
              <td>
                <ul class="issue-list">
                  <li v-for="(msg, i) in pr.messages" :key="i">{{ msg }}</li>
                </ul>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- All Clear -->
      <div
        v-if="
          !hardFailures.length &&
          !warnings.length &&
          !pathRisks.length &&
          globalRisk.risk === 'none'
        "
        class="feasibility-panel__success"
      >
        ✅ All checks passed!
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  useArtStudioEngine,
  type RiskLevel,
  type PathRiskAnnotation,
  type GlobalRiskSummary,
} from "@/stores/useArtStudioEngine";

const engine = useArtStudioEngine();

// Computed
const feasibility = computed(() => engine.feasibility.value);

const overallScore = computed(() =>
  feasibility.value ? Math.round(feasibility.value.overallScore * 100) : 0
);

const hardFailures = computed(() => feasibility.value?.hardFailures ?? []);
const warnings = computed(() => feasibility.value?.warnings ?? []);
const pathRisks = computed(
  (): PathRiskAnnotation[] => feasibility.value?.pathRisks ?? []
);

const globalRisk = computed((): GlobalRiskSummary => engine.getGlobalRisk());

const badgeClass = computed(() => {
  if (!feasibility.value) return "";
  if (hardFailures.value.length > 0) return "badge--fail";
  if (warnings.value.length > 0) return "badge--warn";
  return "badge--pass";
});

// Helpers
function riskLabel(risk: RiskLevel): string {
  switch (risk) {
    case "fail":
      return "FAIL";
    case "warn":
      return "WARN";
    case "info":
      return "INFO";
    case "none":
    default:
      return "OK";
  }
}

function truncateId(id: string): string {
  return id.length > 12 ? id.slice(0, 10) + "…" : id;
}
</script>

<style scoped>
.feasibility-panel {
  padding: 1rem;
  background: #ffffff;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 0.875rem;
}

.feasibility-panel__title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 0 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  color: #212529;
}

.feasibility-panel__badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
}

.badge--pass {
  background: #198754;
}
.badge--warn {
  background: #f57c00;
}
.badge--fail {
  background: #dc3545;
}

.feasibility-panel__empty {
  color: #6c757d;
  font-style: italic;
}

.feasibility-panel__section {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.feasibility-panel__section--fail {
  background: #fff5f5;
  border-left: 3px solid #dc3545;
}

.feasibility-panel__section--warn {
  background: #fffbeb;
  border-left: 3px solid #f57c00;
}

.feasibility-panel__section h4 {
  margin: 0 0 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.feasibility-panel__list {
  margin: 0;
  padding-left: 1.25rem;
  color: #495057;
}

.feasibility-panel__list li {
  margin-bottom: 0.25rem;
}

.feasibility-panel__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.feasibility-panel__table th,
.feasibility-panel__table td {
  padding: 0.5rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.feasibility-panel__table th {
  background: #e9ecef;
  font-weight: 600;
  color: #495057;
}

.path-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #6c757d;
}

.issue-list {
  margin: 0;
  padding-left: 1rem;
  list-style: disc;
}

.issue-list li {
  color: #495057;
}

.risk-badge {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.risk-badge--none {
  background: #e9ecef;
  color: #495057;
}
.risk-badge--info {
  background: #e3f2fd;
  color: #1565c0;
}
.risk-badge--warn {
  background: #fff3e0;
  color: #e65100;
}
.risk-badge--fail {
  background: #ffebee;
  color: #c62828;
}

.feasibility-panel__success {
  padding: 1rem;
  background: #e8f5e9;
  border-radius: 6px;
  color: #2e7d32;
  font-weight: 500;
  text-align: center;
}
</style>
