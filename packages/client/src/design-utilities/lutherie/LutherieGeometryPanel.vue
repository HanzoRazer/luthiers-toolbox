<!--
  LutherieGeometryPanel.vue
  ==========================
  The Production Shop — Scientific Calculator / Woodwork tab

  Three geometry families:
    1. Right Triangle & Compound Angles
       Dovetail neck joints, scarf joints, headstock angles
    2. Pitch / Brace Geometry
       Fan bracing, X-braces, tone bars — rise over run for precise cuts
    3. Arc / Circle Tools
       Rosette radii, purfling bends, binding curves, radius dish depth

  Mounted as a new sub-category inside WoodworkPanel, replacing the
  existing basic miter/bevel panel which is preserved as-is.
-->

<template>
  <div class="lgp">

    <!-- Sub-category nav -->
    <div class="lgp-tabs">
      <button
        v-for="t in SUB_TABS"
        :key="t.id"
        :class="['lgp-tab', { 'lgp-tab--on': activeSubTab === t.id }]"
        @click="activeSubTab = t.id"
      >{{ t.label }}</button>
    </div>

    <!-- ====================================================================
         1. RIGHT TRIANGLE & COMPOUND ANGLES
    ==================================================================== -->
    <div v-if="activeSubTab === 'triangle'" class="lgp-panel">

      <!-- Preset strip -->
      <div class="lgp-presets">
        <button
          v-for="p in RIGHT_TRIANGLE_PRESETS"
          :key="p.label"
          class="lgp-preset-btn"
          @click="loadTriPreset(p)"
        >{{ p.label }}</button>
      </div>

      <!-- Solve mode -->
      <div class="lgp-row">
        <span class="lgp-label">Solve from</span>
        <select v-model="triInput.mode" class="lgp-select">
          <option v-for="m in SOLVE_MODES" :key="m.id" :value="m.id">{{ m.label }}</option>
        </select>
      </div>

      <!-- Inputs (show only relevant fields per mode) -->
      <div class="lgp-inputs">
        <div v-if="showTriField('rise')" class="lgp-row">
          <label class="lgp-label">Rise (mm)</label>
          <input v-model.number="triInput.rise" type="number" step="0.1" class="lgp-input lgp-mono">
        </div>
        <div v-if="showTriField('run')" class="lgp-row">
          <label class="lgp-label">Run (mm)</label>
          <input v-model.number="triInput.run" type="number" step="0.1" class="lgp-input lgp-mono">
        </div>
        <div v-if="showTriField('hyp')" class="lgp-row">
          <label class="lgp-label">Hypotenuse (mm)</label>
          <input v-model.number="triInput.hyp" type="number" step="0.1" class="lgp-input lgp-mono">
        </div>
        <div v-if="showTriField('angle')" class="lgp-row">
          <label class="lgp-label">Angle (°)</label>
          <input v-model.number="triInput.angleDeg" type="number" step="0.1" min="0" max="89.9" class="lgp-input lgp-mono">
        </div>
      </div>

      <!-- Results -->
      <div v-if="triResult.valid" class="lgp-results">
        <div class="lgp-result-grid">
          <div class="lgp-stat">
            <div class="lgp-stat-label">Angle</div>
            <div class="lgp-stat-val">{{ triResult.angleDeg.toFixed(3) }}°</div>
          </div>
          <div class="lgp-stat">
            <div class="lgp-stat-label">Complement</div>
            <div class="lgp-stat-val">{{ triResult.complementDeg.toFixed(3) }}°</div>
          </div>
          <div class="lgp-stat">
            <div class="lgp-stat-label">Rise</div>
            <div class="lgp-stat-val lgp-mono">{{ triResult.rise.toFixed(3) }} mm</div>
          </div>
          <div class="lgp-stat">
            <div class="lgp-stat-label">Run</div>
            <div class="lgp-stat-val lgp-mono">{{ triResult.run.toFixed(3) }} mm</div>
          </div>
          <div class="lgp-stat">
            <div class="lgp-stat-label">Hypotenuse</div>
            <div class="lgp-stat-val lgp-mono">{{ triResult.hyp.toFixed(3) }} mm</div>
          </div>
          <div class="lgp-stat">
            <div class="lgp-stat-label">Pitch</div>
            <div class="lgp-stat-val">{{ triResult.pitchPercent.toFixed(2) }}%</div>
          </div>
        </div>
        <!-- SVG diagram -->
        <svg :viewBox="`0 0 200 120`" class="lgp-tri-svg">
          <line x1="10" y1="100" x2="170" y2="100" stroke="var(--color-border-secondary)" stroke-width="1"/>
          <line x1="10" y1="100" x2="10" y2="20" stroke="var(--color-border-secondary)" stroke-width="1"/>
          <line x1="10" y1="20" x2="170" y2="100" stroke="#378ADD" stroke-width="1.5"/>
          <!-- Right angle mark -->
          <rect x="10" y="88" width="10" height="10" fill="none" stroke="var(--color-border-secondary)" stroke-width="0.8"/>
          <!-- Labels -->
          <text x="90" y="112" text-anchor="middle" font-size="9" fill="var(--color-text-secondary)">run {{ triResult.run.toFixed(1) }}</text>
          <text x="3" y="62" text-anchor="middle" font-size="9" fill="var(--color-text-secondary)" transform="rotate(-90,3,62)">rise {{ triResult.rise.toFixed(1) }}</text>
          <text x="100" y="55" text-anchor="middle" font-size="9" fill="#378ADD" transform="rotate(-27,100,55)">hyp {{ triResult.hyp.toFixed(1) }}</text>
          <text x="40" y="95" text-anchor="middle" font-size="9" fill="#BA7517">{{ triResult.angleDeg.toFixed(1) }}°</text>
        </svg>
      </div>
      <div v-else class="lgp-error">{{ triResult.error }}</div>

      <!-- Compound angle section -->
      <div class="lgp-divider">Compound Angle (two-plane cuts)</div>
      <div class="lgp-hint">Dovetail neck joint: primary = neck angle, secondary = lateral cant. Scarf joint: primary = scarf angle, secondary = 0.</div>
      <div class="lgp-inputs">
        <div class="lgp-row">
          <label class="lgp-label">Primary angle (°)</label>
          <input v-model.number="compInput.primaryDeg" type="number" step="0.1" min="0.1" max="89" class="lgp-input lgp-mono">
        </div>
        <div class="lgp-row">
          <label class="lgp-label">Secondary angle (°)</label>
          <input v-model.number="compInput.secondaryDeg" type="number" step="0.1" min="0.1" max="89" class="lgp-input lgp-mono">
        </div>
      </div>
      <div v-if="compResult.valid" class="lgp-result-grid" style="margin-top:8px">
        <div class="lgp-stat">
          <div class="lgp-stat-label">Compound angle</div>
          <div class="lgp-stat-val" style="color:#BA7517">{{ compResult.compoundDeg.toFixed(3) }}°</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Saw miter</div>
          <div class="lgp-stat-val lgp-mono">{{ compResult.miterDeg.toFixed(3) }}°</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Saw bevel</div>
          <div class="lgp-stat-val lgp-mono">{{ compResult.bevelDeg.toFixed(3) }}°</div>
        </div>
      </div>
    </div>

    <!-- ====================================================================
         2. PITCH / BRACE GEOMETRY
    ==================================================================== -->
    <div v-else-if="activeSubTab === 'brace'" class="lgp-panel">

      <div class="lgp-presets">
        <button
          v-for="p in BRACE_PRESETS"
          :key="p.label"
          class="lgp-preset-btn"
          @click="loadBracePreset(p)"
        >{{ p.label }}</button>
      </div>

      <div class="lgp-row">
        <label class="lgp-label">Crown rise (mm)</label>
        <input v-model.number="braceInput.riseMm" type="number" step="0.5" min="1" class="lgp-input lgp-mono">
      </div>
      <div class="lgp-row">
        <label class="lgp-label">Arch radius (mm)</label>
        <input v-model.number="braceInput.radiusMm" type="number" step="5" min="0" class="lgp-input lgp-mono">
        <span class="lgp-unit">0 = straight</span>
      </div>

      <!-- Brace runs -->
      <div class="lgp-divider">Brace runs</div>
      <div
        v-for="(run, idx) in braceInput.runsMm"
        :key="idx"
        class="lgp-row"
      >
        <label class="lgp-label">Brace {{ idx + 1 }} run (mm)</label>
        <input
          :value="run"
          type="number"
          step="1"
          min="10"
          class="lgp-input lgp-mono"
          @change="braceInput.runsMm[idx] = parseFloat(($event.target as HTMLInputElement).value) || run"
        >
        <button class="lgp-remove-btn" @click="removeBraceRun(idx)">×</button>
      </div>
      <button class="lgp-add-btn" @click="addBraceRun">+ Add brace</button>

      <!-- Results table -->
      <div v-if="braceResult.valid && braceResult.braces.length" class="lgp-brace-table-wrap">
        <table class="lgp-brace-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Run (mm)</th>
              <th>Length (mm)</th>
              <th>Pitch °</th>
              <th>Cut °</th>
              <th>H mid (mm)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(b, idx) in braceResult.braces" :key="idx">
              <td>{{ idx + 1 }}</td>
              <td class="lgp-mono">{{ b.runMm }}</td>
              <td class="lgp-mono" style="color:#378ADD">{{ b.braceLength }}</td>
              <td class="lgp-mono" style="color:#BA7517">{{ b.pitchAngleDeg.toFixed(2) }}°</td>
              <td class="lgp-mono">{{ b.cutAngleDeg.toFixed(2) }}°</td>
              <td class="lgp-mono">{{ b.heightAtCenter }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!braceResult.valid" class="lgp-error">{{ braceResult.error }}</div>

      <div class="lgp-hint" style="margin-top:8px">
        Pitch ° = angle at brace foot. Cut ° = 90 − pitch = table saw cut angle.
        H mid = height at span midpoint (flat brace) or arc midpoint (radiused brace).
      </div>
    </div>

    <!-- ====================================================================
         3. ARC / CIRCLE TOOLS
    ==================================================================== -->
    <div v-else-if="activeSubTab === 'arc'" class="lgp-panel">

      <div class="lgp-presets">
        <button
          v-for="p in ARC_PRESETS"
          :key="p.label"
          class="lgp-preset-btn"
          @click="loadArcPreset(p)"
        >{{ p.label }}</button>
      </div>

      <div class="lgp-row">
        <label class="lgp-label">Radius (mm)</label>
        <input v-model.number="arcInput.radiusMm" type="number" step="0.5" min="0.1" class="lgp-input lgp-mono">
        <span class="lgp-unit">{{ (arcInput.radiusMm / 25.4).toFixed(3) }}"</span>
      </div>
      <div class="lgp-row">
        <label class="lgp-label">Central angle (°)</label>
        <input v-model.number="arcInput.centralAngleDeg" type="number" step="1" min="1" max="360" class="lgp-input lgp-mono">
      </div>

      <div v-if="arcResult.valid" class="lgp-result-grid" style="margin-top:10px">
        <div class="lgp-stat">
          <div class="lgp-stat-label">Diameter</div>
          <div class="lgp-stat-val lgp-mono">{{ arcResult.diameterMm.toFixed(2) }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Circumference</div>
          <div class="lgp-stat-val lgp-mono">{{ arcResult.circumferenceMm.toFixed(2) }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Arc length</div>
          <div class="lgp-stat-val lgp-mono" style="color:#378ADD">{{ arcResult.arcLengthMm.toFixed(2) }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Chord length</div>
          <div class="lgp-stat-val lgp-mono">{{ arcResult.chordLengthMm.toFixed(2) }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Sagitta (rise)</div>
          <div class="lgp-stat-val lgp-mono" style="color:#BA7517">{{ arcResult.sagittaMm.toFixed(3) }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Radius (inches)</div>
          <div class="lgp-stat-val lgp-mono">{{ (arcResult.radiusMm / 25.4).toFixed(3) }}"</div>
        </div>
      </div>
      <div v-else class="lgp-error">{{ arcResult.error }}</div>

      <!-- Sagitta diagram -->
      <svg v-if="arcResult.valid && arcInput.centralAngleDeg < 360" viewBox="0 0 220 120" class="lgp-arc-svg">
        <path
          :d="arcSvgPath"
          fill="none"
          stroke="#378ADD"
          stroke-width="1.5"
        />
        <!-- Chord -->
        <line :x1="arcChordX1" y1="90" :x2="arcChordX2" y2="90" stroke="var(--color-border-secondary)" stroke-width="1" stroke-dasharray="3 2"/>
        <!-- Sagitta arrow -->
        <line :x1="arcMidX" y1="90" :x2="arcMidX" :y2="arcApexY" stroke="#BA7517" stroke-width="1" stroke-dasharray="3 2"/>
        <!-- Labels -->
        <text :x="arcMidX" y="106" text-anchor="middle" font-size="8" fill="var(--color-text-secondary)">chord {{ arcResult.chordLengthMm.toFixed(1) }}mm</text>
        <text :x="arcMidX + 18" :y="(90 + arcApexY) / 2 + 3" text-anchor="start" font-size="8" fill="#BA7517">sag {{ arcResult.sagittaMm.toFixed(2) }}mm</text>
      </svg>

      <!-- Bend allowance section -->
      <div class="lgp-divider">Binding / Purfling Bend Allowance</div>
      <div class="lgp-row">
        <label class="lgp-label">Stock thickness (mm)</label>
        <input v-model.number="bendInput.thicknessMm" type="number" step="0.1" min="0.1" max="10" class="lgp-input lgp-mono">
      </div>
      <div class="lgp-row">
        <label class="lgp-label">Material</label>
        <select v-model="bendInput.material" class="lgp-select">
          <option v-for="(mat, key) in BEND_MATERIALS" :key="key" :value="key">{{ mat.label }}</option>
        </select>
      </div>
      <div class="lgp-result-grid" style="margin-top:8px">
        <div class="lgp-stat">
          <div class="lgp-stat-label">Min bend radius</div>
          <div class="lgp-stat-val lgp-mono" style="color:#378ADD">{{ bendResult.minRadiusMm }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Min radius (in)</div>
          <div class="lgp-stat-val lgp-mono">{{ bendResult.minRadiusIn.toFixed(3) }}"</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Kerf spacing</div>
          <div class="lgp-stat-val lgp-mono">{{ bendResult.kerfSpacingMm }} mm</div>
        </div>
        <div class="lgp-stat">
          <div class="lgp-stat-label">Kerfs / 360°</div>
          <div class="lgp-stat-val lgp-mono">{{ bendResult.kerfsPerCircle }}</div>
        </div>
      </div>
      <div v-if="bendResult.warning" class="lgp-warn">{{ bendResult.warning }}</div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLutherieGeometry } from '../composables/useLutherieGeometry'
import type { RightTriangleSolveMode } from '../composables/useLutherieGeometry'

const SUB_TABS = [
  { id: 'triangle', label: 'Right Triangle & Compound' },
  { id: 'brace',    label: 'Pitch / Brace Layout' },
  { id: 'arc',      label: 'Arc & Circle' },
] as const

type SubTab = typeof SUB_TABS[number]['id']
const activeSubTab = ref<SubTab>('triangle')

const {
  triInput, triResult,
  compInput, compResult,
  braceInput, braceResult, addBraceRun, removeBraceRun,
  arcInput, arcResult,
  bendInput, bendResult,
  RIGHT_TRIANGLE_PRESETS, ARC_PRESETS, BRACE_PRESETS,
  BEND_MATERIALS,
  SOLVE_MODES,
  loadTriPreset, loadArcPreset, loadBracePreset,
} = useLutherieGeometry()

// Which input fields to show per solve mode
const FIELDS_BY_MODE: Record<RightTriangleSolveMode, string[]> = {
  rise_run:   ['rise', 'run'],
  angle_run:  ['angle', 'run'],
  angle_rise: ['angle', 'rise'],
  angle_hyp:  ['angle', 'hyp'],
  rise_hyp:   ['rise', 'hyp'],
}
function showTriField(field: string): boolean {
  return FIELDS_BY_MODE[triInput.value.mode]?.includes(field) ?? false
}

// Arc SVG helpers
const ARC_SVG_W = 220
const ARC_SVG_H = 120
const ARC_CENTER_X = ARC_SVG_W / 2
const ARC_FLOOR_Y = 90
const ARC_SCALE = 0.12   // mm → svg px

const arcSvgPath = computed(() => {
  const r = arcResult.value.radiusMm * ARC_SCALE
  const theta = arcInput.value.centralAngleDeg * Math.PI / 180
  const half = theta / 2
  const cx = ARC_CENTER_X
  const cy = ARC_FLOOR_Y + r * Math.cos(half)
  const x1 = cx - r * Math.sin(half)
  const y1 = cy - r * Math.cos(half) + r * Math.cos(half)
  const x2 = cx + r * Math.sin(half)
  const y2 = y1
  const apexX = cx
  const apexY = cy - r
  const large = theta > Math.PI ? 1 : 0
  return `M ${x1} ${ARC_FLOOR_Y} A ${r} ${r} 0 ${large} 1 ${x2} ${ARC_FLOOR_Y}`
})

const arcChordX1 = computed(() => {
  const r = arcResult.value.radiusMm * ARC_SCALE
  const half = (arcInput.value.centralAngleDeg / 2) * Math.PI / 180
  return ARC_CENTER_X - r * Math.sin(half)
})
const arcChordX2 = computed(() => {
  const r = arcResult.value.radiusMm * ARC_SCALE
  const half = (arcInput.value.centralAngleDeg / 2) * Math.PI / 180
  return ARC_CENTER_X + r * Math.sin(half)
})
const arcMidX = computed(() => ARC_CENTER_X)
const arcApexY = computed(() => {
  const r = arcResult.value.radiusMm * ARC_SCALE
  const sag = arcResult.value.sagittaMm * ARC_SCALE
  return ARC_FLOOR_Y - sag
})
</script>

<style scoped>
.lgp { font-family: var(--font-sans, system-ui); }
.lgp-tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px; }
.lgp-tab { font-size: 11px; padding: 3px 10px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: transparent; color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.lgp-tab--on { background: var(--color-background-tertiary); color: var(--color-text-primary); border-color: var(--color-border-secondary); }
.lgp-panel { display: flex; flex-direction: column; gap: 8px; }
.lgp-presets { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 4px; }
.lgp-preset-btn { font-size: 11px; padding: 2px 8px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; white-space: nowrap; }
.lgp-preset-btn:hover { background: var(--color-background-tertiary); }
.lgp-row { display: flex; align-items: center; gap: 8px; }
.lgp-label { font-size: 12px; color: var(--color-text-secondary); flex: 0 0 160px; white-space: nowrap; }
.lgp-input { font-size: 12px; padding: 3px 5px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); width: 90px; font-family: inherit; }
.lgp-select { font-size: 12px; padding: 3px 6px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); font-family: inherit; }
.lgp-unit { font-size: 11px; color: var(--color-text-tertiary); }
.lgp-mono { font-family: var(--font-mono, monospace); }
.lgp-inputs { display: flex; flex-direction: column; gap: 6px; }
.lgp-results { display: flex; flex-direction: column; gap: 8px; }
.lgp-result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 6px; }
.lgp-stat { background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 7px 10px; }
.lgp-stat-label { font-size: 10px; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
.lgp-stat-val { font-size: 14px; font-weight: 500; color: var(--color-text-primary); }
.lgp-divider { font-size: 10px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; border-top: 0.5px solid var(--color-border-tertiary); padding-top: 8px; margin-top: 4px; }
.lgp-hint { font-size: 10px; color: var(--color-text-tertiary); line-height: 1.5; font-style: italic; }
.lgp-error { font-size: 12px; color: var(--color-text-danger, #E24B4A); padding: 6px; background: var(--color-background-danger); border-radius: var(--border-radius-md); }
.lgp-warn { font-size: 11px; color: var(--color-text-warning); padding: 6px 8px; background: var(--color-background-warning); border-radius: var(--border-radius-md); }
.lgp-tri-svg { width: 100%; max-width: 260px; margin-top: 6px; }
.lgp-arc-svg { width: 100%; max-width: 260px; margin-top: 6px; }
.lgp-add-btn { font-size: 11px; padding: 2px 9px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-secondary); cursor: pointer; font-family: inherit; align-self: flex-start; }
.lgp-remove-btn { background: none; border: none; color: var(--color-text-tertiary); cursor: pointer; font-size: 14px; padding: 0 2px; }
.lgp-remove-btn:hover { color: var(--color-text-danger, #E24B4A); }
.lgp-brace-table-wrap { overflow-x: auto; }
.lgp-brace-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.lgp-brace-table th { font-size: 10px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; padding: 4px 7px; background: var(--color-background-secondary); border-bottom: 0.5px solid var(--color-border-tertiary); white-space: nowrap; }
.lgp-brace-table td { padding: 3px 7px; border-bottom: 0.5px solid var(--color-border-tertiary); font-family: var(--font-mono, monospace); }
.lgp-brace-table tr:last-child td { border-bottom: none; }
</style>
