<script setup lang="ts">
/**
 * GateStatusBadge.vue
 *
 * Displays the three-state gate result for a CAM operation.
 * RED   → hard block, generate button disabled
 * YELLOW → warnings present, generate enabled with orange banner
 * GREEN  → clean, generate enabled silently
 *
 * Used in NeckOpPanel.vue (one per operation).
 */

export interface GateCheck {
  name:    string
  status:  'GREEN' | 'YELLOW' | 'RED'
  value:   number | null
  message: string
}

export interface GateResult {
  overall_risk:  'GREEN' | 'YELLOW' | 'RED'
  checks:        GateCheck[]
  warnings:      string[]
  hard_failures: string[]
  z_ceiling_ok:  boolean
  z_ceiling_msg: string
}

const props = defineProps<{
  gate:      GateResult | null
  loading?:  boolean
  compact?:  boolean   // true = single-line badge only, false = expanded checks
}>()
</script>

<template>
  <div class="gate-wrap">

    <!-- Loading state -->
    <div v-if="loading" class="gate-loading">
      <span class="spin-sm"></span>
      <span class="gate-loading-txt">Evaluating…</span>
    </div>

    <!-- No gate yet -->
    <div v-else-if="!gate" class="gate-empty">─</div>

    <!-- Badge row -->
    <template v-else>
      <div class="gate-badge-row">
        <div class="gate-badge" :class="gate.overall_risk.toLowerCase()">
          <span class="gate-dot"></span>
          <span class="gate-label">{{ gate.overall_risk }}</span>
        </div>
        <div v-if="gate.hard_failures.length" class="gate-count red">
          {{ gate.hard_failures.length }} block{{ gate.hard_failures.length > 1 ? 's' : '' }}
        </div>
        <div v-else-if="gate.warnings.length" class="gate-count yellow">
          {{ gate.warnings.length }} warn
        </div>
      </div>

      <!-- Z ceiling -->
      <div v-if="!gate.z_ceiling_ok" class="gate-z-warn">
        ⚠ {{ gate.z_ceiling_msg }}
      </div>

      <!-- Expanded checks (shown when compact=false) -->
      <div v-if="!compact && gate.checks.length" class="gate-checks">
        <div v-for="c in gate.checks" :key="c.name"
          class="gate-check-row" :class="c.status.toLowerCase()">
          <span class="chk-dot"></span>
          <span class="chk-name">{{ c.name }}</span>
          <span class="chk-val" v-if="c.value !== null">{{ c.value }}</span>
          <span class="chk-msg">{{ c.message }}</span>
        </div>
      </div>

      <!-- Hard failure messages -->
      <div v-if="!compact && gate.hard_failures.length" class="gate-failures">
        <div v-for="f in gate.hard_failures" :key="f" class="gate-fail-msg">
          ✕ {{ f }}
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.gate-wrap { display: flex; flex-direction: column; gap: 4px; }

/* Loading */
.gate-loading { display: flex; align-items: center; gap: 5px; }
.spin-sm {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1.5px solid var(--w4); border-top-color: var(--br);
  animation: spin .7s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.gate-loading-txt { font-size: 8px; color: var(--dim3); font-family: var(--mono); }

/* Empty */
.gate-empty { font-size: 9px; color: var(--dim3); }

/* Badge row */
.gate-badge-row { display: flex; align-items: center; gap: 6px; }

.gate-badge {
  display: flex; align-items: center; gap: 4px;
  padding: 2px 7px 2px 5px;
  border-radius: 3px;
  border: 1px solid;
}
.gate-badge.green  { background: rgba(90,184,106,.1);  border-color: var(--green2); }
.gate-badge.yellow { background: rgba(200,150,48,.12); border-color: var(--amber);  }
.gate-badge.red    { background: rgba(200,72,72,.12);  border-color: var(--red);    }

.gate-dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.gate-badge.green  .gate-dot { background: var(--green2); }
.gate-badge.yellow .gate-dot { background: var(--amber);  }
.gate-badge.red    .gate-dot { background: var(--red);    }

.gate-label { font-size: 8px; font-family: var(--mono); letter-spacing: .8px; }
.gate-badge.green  .gate-label { color: var(--green2); }
.gate-badge.yellow .gate-label { color: var(--amber);  }
.gate-badge.red    .gate-label { color: var(--red);    }

.gate-count {
  font-size: 7px; font-family: var(--mono); letter-spacing: .5px;
  padding: 1px 5px; border-radius: 2px;
}
.gate-count.red    { background: rgba(200,72,72,.1);   color: var(--red);   border: 1px solid var(--red);    }
.gate-count.yellow { background: rgba(200,150,48,.1);  color: var(--amber); border: 1px solid var(--amber);  }

/* Z ceiling warning */
.gate-z-warn {
  font-size: 8px; color: var(--red);
  padding: 3px 6px; background: rgba(200,72,72,.08);
  border-left: 2px solid var(--red); border-radius: 0 2px 2px 0;
}

/* Per-check rows */
.gate-checks { display: flex; flex-direction: column; gap: 2px; margin-top: 2px; }
.gate-check-row {
  display: grid; grid-template-columns: 8px 60px auto 1fr;
  align-items: center; gap: 5px; padding: 2px 4px;
  border-radius: 2px;
}
.gate-check-row.green  { background: rgba(90,184,106,.05); }
.gate-check-row.yellow { background: rgba(200,150,48,.06); }
.gate-check-row.red    { background: rgba(200,72,72,.06);  }

.chk-dot {
  width: 5px; height: 5px; border-radius: 50%;
}
.green  .chk-dot { background: var(--green2); }
.yellow .chk-dot { background: var(--amber);  }
.red    .chk-dot { background: var(--red);    }

.chk-name { font-size: 8px; color: var(--dim); }
.chk-val  { font-size: 8px; color: var(--v1);  font-family: var(--mono); }
.chk-msg  { font-size: 7px; color: var(--dim3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Hard failures */
.gate-failures { display: flex; flex-direction: column; gap: 2px; margin-top: 2px; }
.gate-fail-msg {
  font-size: 8px; color: var(--red); padding: 2px 6px;
  background: rgba(200,72,72,.06); border-radius: 2px;
}
</style>
