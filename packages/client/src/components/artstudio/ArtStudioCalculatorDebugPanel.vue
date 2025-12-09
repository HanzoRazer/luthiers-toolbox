<template>
  <section class="calc-debug">
    <h3>Calculator Debug</h3>

    <form class="calc-debug__form" @submit.prevent="onEvaluate">
      <div class="form-row">
        <label>Tool ID</label>
        <input v-model="toolId" type="text" placeholder="e.g., ENDMILL-6MM" />
      </div>

      <div class="form-row">
        <label>Material ID</label>
        <input v-model="materialId" type="text" placeholder="e.g., MAPLE" />
      </div>

      <div class="form-row">
        <label>Tool Kind</label>
        <select v-model="toolKind">
          <option value="router_bit">Router Bit</option>
          <option value="saw_blade">Saw Blade</option>
        </select>
      </div>

      <div class="form-row">
        <label>Feed (mm/min)</label>
        <input v-model.number="feedMmMin" type="number" min="0" step="100" />
      </div>

      <div class="form-row">
        <label>RPM</label>
        <input v-model.number="rpm" type="number" min="0" step="500" />
      </div>

      <div class="form-row">
        <label>Depth of Cut (mm)</label>
        <input v-model.number="docMm" type="number" min="0" step="0.5" />
      </div>

      <div class="form-row">
        <label>Width of Cut (mm)</label>
        <input v-model.number="wocMm" type="number" min="0" step="0.5" />
      </div>

      <details class="tool-params">
        <summary>Tool Parameters</summary>
        <div class="form-row">
          <label>Tool Diameter (mm)</label>
          <input
            v-model.number="toolDiameterMm"
            type="number"
            min="0"
            step="0.5"
          />
        </div>
        <div class="form-row">
          <label>Flutes / Teeth</label>
          <input v-model.number="fluteCount" type="number" min="1" max="100" />
        </div>
      </details>

      <button type="submit" class="evaluate-btn" :disabled="loading">
        {{ loading ? "Evaluating..." : "Evaluate Cut" }}
      </button>
    </form>

    <div v-if="error" class="calc-debug__error">❌ {{ error }}</div>

    <div v-if="result" class="calc-debug__result">
      <h4>
        Result
        <span
          :class="['risk-badge', `risk-${result.overall_risk.toLowerCase()}`]"
        >
          {{ result.overall_risk }}
        </span>
      </h4>

      <!-- Warnings & Failures -->
      <div v-if="result.hard_failures.length" class="result-failures">
        <strong>❌ Hard Failures:</strong>
        <ul>
          <li v-for="f in result.hard_failures" :key="f">{{ f }}</li>
        </ul>
      </div>

      <div v-if="result.warnings.length" class="result-warnings">
        <strong>⚠ Warnings:</strong>
        <ul>
          <li v-for="w in result.warnings" :key="w">{{ w }}</li>
        </ul>
      </div>

      <!-- Calculator outputs -->
      <div class="result-cards">
        <div v-if="result.chipload" class="result-card">
          <h5>Chipload</h5>
          <p class="value">
            {{ result.chipload.chipload_mm?.toFixed(4) ?? "N/A" }} mm
          </p>
          <p class="status" :class="result.chipload.in_range ? 'ok' : 'warn'">
            {{ result.chipload.in_range ? "✓ In Range" : "⚠ Out of Range" }}
          </p>
          <p class="message">{{ result.chipload.message }}</p>
        </div>

        <div v-if="result.bite_per_tooth" class="result-card">
          <h5>Bite per Tooth</h5>
          <p class="value">
            {{ result.bite_per_tooth.bite_mm?.toFixed(4) ?? "N/A" }} mm
          </p>
          <p
            class="status"
            :class="result.bite_per_tooth.in_range ? 'ok' : 'warn'"
          >
            {{
              result.bite_per_tooth.in_range ? "✓ In Range" : "⚠ Out of Range"
            }}
          </p>
          <p class="message">{{ result.bite_per_tooth.message }}</p>
        </div>

        <div v-if="result.heat" class="result-card">
          <h5>Heat Risk</h5>
          <p class="value">{{ (result.heat.heat_risk * 100).toFixed(0) }}%</p>
          <p class="status" :class="heatClass(result.heat.category)">
            {{ result.heat.category }}
          </p>
          <p class="message">{{ result.heat.message }}</p>
        </div>

        <div v-if="result.deflection" class="result-card">
          <h5>Deflection</h5>
          <p class="value">
            {{ result.deflection.deflection_mm?.toFixed(4) ?? "N/A" }} mm
          </p>
          <p class="status" :class="riskClass(result.deflection.risk)">
            {{ result.deflection.risk }}
          </p>
          <p class="message">{{ result.deflection.message }}</p>
        </div>

        <div v-if="result.rim_speed" class="result-card">
          <h5>Rim Speed</h5>
          <p class="value">
            {{
              result.rim_speed.surface_speed_m_per_min?.toFixed(1) ?? "N/A"
            }}
            m/min
          </p>
          <p
            class="status"
            :class="result.rim_speed.within_limits ? 'ok' : 'danger'"
          >
            {{
              result.rim_speed.within_limits
                ? "✓ Within Limits"
                : "❌ EXCEEDS MAX"
            }}
          </p>
          <p class="message">{{ result.rim_speed.message }}</p>
        </div>

        <div v-if="result.kickback" class="result-card">
          <h5>Kickback Risk</h5>
          <p class="value">
            {{ (result.kickback.risk_score * 100).toFixed(0) }}%
          </p>
          <p class="status" :class="kickbackClass(result.kickback.category)">
            {{ result.kickback.category }}
          </p>
          <p class="message">{{ result.kickback.message }}</p>
        </div>
      </div>

      <!-- Raw JSON toggle -->
      <details class="raw-json">
        <summary>Raw JSON</summary>
        <pre>{{ JSON.stringify(result, null, 2) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
  useArtStudioEngine,
  type CalculatorResult,
} from "@/stores/useArtStudioEngine";

const engine = useArtStudioEngine();

// Form state
const toolId = ref("ENDMILL-6MM");
const materialId = ref("MAPLE");
const toolKind = ref<"router_bit" | "saw_blade">("router_bit");
const feedMmMin = ref(3000);
const rpm = ref(18000);
const docMm = ref(3);
const wocMm = ref(3);
const toolDiameterMm = ref(6);
const fluteCount = ref(2);

// Result state
const result = ref<CalculatorResult | null>(null);
const error = ref<string | null>(null);
const loading = ref(false);

async function onEvaluate() {
  error.value = null;
  result.value = null;
  loading.value = true;

  try {
    const res = await engine.evaluateCutOperation({
      tool_id: toolId.value,
      material_id: materialId.value,
      tool_kind: toolKind.value,
      feed_mm_min: feedMmMin.value,
      rpm: rpm.value,
      depth_of_cut_mm: docMm.value,
      width_of_cut_mm: wocMm.value || undefined,
      tool_diameter_mm: toolDiameterMm.value || undefined,
      flute_count: fluteCount.value || undefined,
    });
    result.value = res;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

function heatClass(category: string): string {
  switch (category) {
    case "COOL":
      return "ok";
    case "WARM":
      return "warn";
    case "HOT":
      return "danger";
    default:
      return "";
  }
}

function riskClass(risk: string): string {
  switch (risk) {
    case "GREEN":
      return "ok";
    case "YELLOW":
      return "warn";
    case "RED":
      return "danger";
    default:
      return "";
  }
}

function kickbackClass(category: string): string {
  switch (category) {
    case "LOW":
      return "ok";
    case "MEDIUM":
      return "warn";
    case "HIGH":
      return "danger";
    default:
      return "";
  }
}
</script>

<style scoped>
.calc-debug {
  border-top: 1px solid #dee2e6;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  font-size: 0.85rem;
}

.calc-debug h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.calc-debug__form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.35rem 0.5rem;
  margin-bottom: 0.5rem;
}

.form-row {
  display: flex;
  flex-direction: column;
}

.form-row label {
  font-size: 0.7rem;
  color: #6c757d;
  margin-bottom: 0.1rem;
}

.form-row input,
.form-row select {
  padding: 0.25rem 0.35rem;
  font-size: 0.8rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.tool-params {
  grid-column: span 2;
  background: #f8f9fa;
  padding: 0.25rem;
  border-radius: 4px;
  margin-top: 0.25rem;
}

.tool-params summary {
  font-size: 0.75rem;
  color: #495057;
  cursor: pointer;
}

.tool-params .form-row {
  margin-top: 0.25rem;
}

.evaluate-btn {
  grid-column: span 2;
  padding: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: none;
  background: #0d6efd;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.25rem;
}

.evaluate-btn:hover:not(:disabled) {
  background: #0b5ed7;
}

.evaluate-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.calc-debug__error {
  color: #dc3545;
  background: #f8d7da;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
}

.calc-debug__result {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 0.5rem;
}

.calc-debug__result h4 {
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.risk-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 600;
}

.risk-green {
  background: #d1e7dd;
  color: #0f5132;
}
.risk-yellow {
  background: #fff3cd;
  color: #664d03;
}
.risk-red {
  background: #f8d7da;
  color: #842029;
}

.result-failures,
.result-warnings {
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.result-failures {
  background: #f8d7da;
  color: #842029;
}

.result-warnings {
  background: #fff3cd;
  color: #664d03;
}

.result-failures ul,
.result-warnings ul {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
}

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

.raw-json {
  margin-top: 0.5rem;
  font-size: 0.7rem;
}

.raw-json summary {
  cursor: pointer;
  color: #6c757d;
}

.raw-json pre {
  background: #f1f3f4;
  padding: 0.35rem;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
  font-size: 0.65rem;
  margin-top: 0.25rem;
}
</style>
