<template>
  <div class="soundhole-calculator">
    <!-- Header -->
    <div class="header">
      <h2>Guitar soundhole: Helmholtz + P:A calculator with builder calibration log</h2>
      <p class="subtitle">
        Two modes: Design (Gore priors + your data) and Calibration (tap-test a build, fit α, save to log).
        α is a system property — only measurement gives you the right value for your instrument.
      </p>
    </div>

    <!-- Mode switcher -->
    <div class="mode-switcher">
      <button
        :class="['mode-btn', { active: mode === 'design' }]"
        @click="mode = 'design'"
      >
        Design mode — explore geometry
      </button>
      <button
        :class="['mode-btn', { active: mode === 'cal' }]"
        @click="mode = 'cal'"
      >
        Calibration mode — record a build
      </button>
    </div>

    <!-- DESIGN MODE -->
    <template v-if="mode === 'design'">
      <!-- Metric strip -->
      <div class="metric-strip">
        <MetricCard
          label="Main hole A0"
          :value="`${r1(mainHz)} Hz`"
          sub="no side port"
        />
        <MetricCard
          label="Combined A0"
          :value="`${r1(combHz)} Hz`"
          sub="with side port"
        />
        <MetricCard
          label="P:A ratio"
          :value="`${r3(geo.pa)} m⁻¹`"
          :sub="paLabel"
          :accent="geo.pa > PA_THRESHOLD_HI ? '#0F6E56' : geo.pa > PA_THRESHOLD_LO ? '#BA7517' : undefined"
        />
        <MetricCard
          label="Active α"
          :value="alpha.toFixed(2)"
          :sub="alphaSource.length > 26 ? alphaSource.slice(0, 26) + '…' : alphaSource"
          accent="#185FA5"
        />
      </div>

      <div class="design-grid">
        <!-- Left: Controls -->
        <div class="card controls-card">
          <!-- Tab bar -->
          <div class="tab-bar">
            <button
              v-for="t in ['alpha', 'body', 'hole', 'side', 'pa']"
              :key="t"
              :class="['tab-btn', { active: dTab === t }]"
              @click="setDTab(t)"
            >
              {{ t === 'alpha' ? 'α source' : t === 'pa' ? 'P:A data' : t.charAt(0).toUpperCase() + t.slice(1) }}
            </button>
          </div>

          <!-- Alpha Source Tab -->
          <div
            v-if="dTab === 'alpha'"
            class="tab-content"
          >
            <h4>Gore end-correction factor α</h4>
            <div class="info-note">
              α is a system property — body geometry, soundhole position, top compliance, and bracing all affect it simultaneously.
              No material table can give you α. Use Gore priors as starting estimates, then calibrate from measurement.
            </div>
            <div class="alpha-display">
              <div class="alpha-value">
                {{ alpha.toFixed(2) }}
              </div>
              <div class="alpha-source">
                {{ alphaSource }}
              </div>
            </div>
            <SliderRow
              label="Set α manually"
              id="alpha"
              :min="1.20"
              :max="2.20"
              :step="0.01"
              :value="alpha"
              :display="`${alpha.toFixed(2)}`"
              @update="v => { alpha = v; alphaSource = 'Manual'; }"
            />

            <h5>Gore published priors</h5>
            <div class="prior-badges">
              <button
                v-for="p in GORE_PRIORS"
                :key="p.label"
                class="prior-badge gore"
                @click="applyGore(p)"
              >
                {{ p.label }} {{ p.alpha }}
              </button>
            </div>

            <template v-if="userPriors.length > 0">
              <h5>Your measured priors</h5>
              <div class="prior-badges">
                <button
                  v-for="p in userPriors"
                  :key="p.label"
                  class="prior-badge user"
                  @click="applyUserPrior(p)"
                >
                  {{ p.label }} {{ p.alpha }} (n={{ p.n }})
                </button>
              </div>
            </template>
            <div
              v-else
              class="no-data"
            >
              No calibration data yet. Add builds in Calibration mode.
            </div>

            <div class="info-rows">
              <InfoRow
                label="Rayleigh rigid baffle (theory)"
                value="1.70"
                mono
              />
              <InfoRow
                label="Gore dreadnought (measured)"
                value="1.63"
                mono
              />
              <InfoRow
                label="Gore typical range"
                value="1.60 – 1.80"
                mono
              />
              <InfoRow
                :label="`Leff at current α`"
                :value="`${r1(geo.leff * 1000)} mm`"
                mono
              />
            </div>
          </div>

          <!-- Body Tab -->
          <div
            v-if="dTab === 'body'"
            class="tab-content"
          >
            <h4>Body</h4>
            <div class="field-group">
              <label class="field-label">Guitar type</label>
              <select
                v-model.number="volL"
                class="select-input"
                @change="onGuitarTypeChange"
              >
                <option
                  v-for="p in GORE_PRIORS.filter(g => g.label !== 'Rayleigh')"
                  :key="p.label"
                  :value="p.vol"
                >
                  {{ p.label }}
                </option>
              </select>
            </div>
            <SliderRow
              label="Body volume (L)"
              id="vol"
              :min="8"
              :max="35"
              :step="0.5"
              :value="volL"
              :display="`${r1(volL)} L`"
              @update="v => volL = v"
            />
            <SliderRow
              label="Target A0 reference (Hz)"
              id="tgt"
              :min="70"
              :max="140"
              :step="1"
              :value="targetHz"
              :display="`${ri(targetHz)} Hz`"
              @update="v => targetHz = v"
            />
            <div class="info-rows">
              <InfoRow
                label="Volume (m³)"
                :value="`${(volL * L2M).toFixed(3)} m³`"
              />
            </div>
          </div>

          <!-- Hole Tab -->
          <div
            v-if="dTab === 'hole'"
            class="tab-content"
          >
            <h4>Main soundhole</h4>
            <div class="field-group">
              <label class="field-label">Shape</label>
              <select
                v-model="shape"
                class="select-input"
              >
                <option value="round">
                  Round
                </option>
                <option value="oval">
                  Oval
                </option>
                <option value="slot">
                  Single slot
                </option>
                <option value="dslot">
                  Double slot
                </option>
                <option value="fhole">
                  F-hole pair
                </option>
                <option value="cslot">
                  C-slot
                </option>
              </select>
            </div>
            <template v-if="shape === 'round' || shape === 'oval'">
              <SliderRow
                label="Diameter (in)"
                id="diam"
                :min="2.5"
                :max="5.5"
                :step="0.05"
                :value="diamIn"
                :display="`${diamIn.toFixed(2)} in`"
                @update="v => diamIn = v"
              />
            </template>
            <template v-if="['slot', 'dslot', 'cslot'].includes(shape)">
              <SliderRow
                label="Length (mm)"
                id="slen"
                :min="40"
                :max="420"
                :step="5"
                :value="slotLenMm"
                :display="`${ri(slotLenMm)} mm`"
                @update="v => slotLenMm = v"
              />
              <SliderRow
                label="Width (mm)"
                id="swid"
                :min="5"
                :max="50"
                :step="1"
                :value="slotWidMm"
                :display="`${ri(slotWidMm)} mm`"
                @update="v => slotWidMm = v"
              />
            </template>
            <template v-if="shape === 'fhole'">
              <SliderRow
                label="F-hole length (mm)"
                id="flen"
                :min="60"
                :max="130"
                :step="2"
                :value="fholeLenMm"
                :display="`${ri(fholeLenMm)} mm`"
                @update="v => fholeLenMm = v"
              />
              <SliderRow
                label="Waist width (mm)"
                id="fwid"
                :min="3"
                :max="14"
                :step="0.5"
                :value="fholeWidMm"
                :display="`${fholeWidMm.toFixed(1)} mm`"
                @update="v => fholeWidMm = v"
              />
            </template>
            <SliderRow
              label="Top thickness (mm)"
              id="topt"
              :min="2"
              :max="5.5"
              :step="0.1"
              :value="topThickMm"
              :display="`${r1(topThickMm)} mm`"
              @update="v => topThickMm = v"
            />
            <div class="info-rows">
              <InfoRow
                label="Effective area"
                :value="`${r2(geo.area * 1e4)} cm²`"
                mono
              />
              <InfoRow
                label="Perimeter"
                :value="`${r1(geo.perim * 1000)} mm`"
                mono
              />
              <InfoRow
                label="P:A ratio"
                :value="`${r3(geo.pa)} m⁻¹`"
                mono
              />
              <InfoRow
                label="Leff"
                :value="`${r1(geo.leff * 1000)} mm`"
                mono
              />
            </div>
          </div>

          <!-- Side Tab -->
          <div
            v-if="dTab === 'side'"
            class="tab-content"
          >
            <h4>Side soundport</h4>
            <SliderRow
              label="Port diameter (mm)"
              id="sided"
              :min="0"
              :max="80"
              :step="1"
              :value="sideDmm"
              :display="`${ri(sideDmm)} mm`"
              @update="v => sideDmm = v"
            />
            <SliderRow
              label="Side thickness (mm)"
              id="sidet"
              :min="1.5"
              :max="5"
              :step="0.1"
              :value="sideThickMm"
              :display="`${r1(sideThickMm)} mm`"
              @update="v => sideThickMm = v"
            />
            <div class="field-group">
              <label class="field-label">Count</label>
              <select
                v-model.number="sideCount"
                class="select-input"
              >
                <option :value="1">
                  1 port
                </option>
                <option :value="2">
                  2 ports
                </option>
              </select>
            </div>
            <div class="info-rows">
              <InfoRow
                label="Port area"
                :value="`${r2(sideA * 1e4)} cm²`"
                mono
              />
              <InfoRow
                label="A0 shift"
                :value="`${shift >= 0 ? '+' : ''}${r1(shift)} Hz`"
                mono
              />
              <InfoRow
                label="Port share of total"
                :value="`${r1(share)}%`"
                mono
              />
              <InfoRow
                label="φ-based diameter"
                :value="`${r1((diamIn * 25.4) / 1.618)} mm`"
                mono
              />
              <InfoRow
                label="Note"
                value="diameter÷φ ≠ area÷φ (area scales r²)"
              />
            </div>
          </div>

          <!-- P:A Data Tab -->
          <div
            v-if="dTab === 'pa'"
            class="tab-content"
          >
            <h4>Williams (2019) P:A experimental data</h4>
            <p class="pa-note">
              All slots equal-area to R45.4mm round. Rigid parlour cavity. R² = 0.953.
            </p>
            <table class="pa-table">
              <thead>
                <tr>
                  <th>Slot</th>
                  <th>Dims (mm)</th>
                  <th>P:A</th>
                  <th>Gain</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="[s, d, pa, g] in PA_DATA"
                  :key="s"
                >
                  <td>{{ s }}</td>
                  <td>{{ d }}</td>
                  <td class="mono">
                    {{ pa }}
                  </td>
                  <td>
                    <span :class="['gain-badge', gainClass(g)]">{{ g }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="pa-footer">
              High P:A shifts tone toward treble. Double slot also frees upper bout as live soundboard area.
              Source: mwguitars.com.au Parts 7–8.
            </p>
          </div>
        </div>

        <!-- Right: Gauge + Curve -->
        <div class="right-column">
          <div class="card">
            <PAGauge :pa="geo.pa" />
          </div>
          <div class="card">
            <h4>A0 vs side-port scale</h4>
            <div class="chart-container">
              <canvas ref="chartCanvas" />
            </div>
            <p class="chart-note">
              Port scaled 70–130%. Dashed = target A0.
            </p>
          </div>
          <div class="card">
            <h4>Geometry summary</h4>
            <div class="info-rows">
              <InfoRow
                label="Main hole A0"
                :value="`${r1(mainHz)} Hz`"
                mono
              />
              <InfoRow
                label="Combined A0"
                :value="`${r1(combHz)} Hz`"
                mono
              />
              <InfoRow
                label="Shift from port"
                :value="`${shift >= 0 ? '+' : ''}${r1(shift)} Hz`"
                mono
              />
              <InfoRow
                label="Efficiency est."
                :value="`+${ri((geo.eff - 1) * 100)}%`"
                mono
              />
              <InfoRow
                label="Tone shift"
                :value="geo.tone"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Verdict -->
      <div class="card verdict-card">
        <h4>Design verdict</h4>
        <div class="verdict-text">
          {{ verdictText }}
        </div>
      </div>
    </template>

    <!-- CALIBRATION MODE -->
    <template v-if="mode === 'cal'">
      <div class="cal-grid">
        <!-- Form -->
        <div class="card">
          <h4>Record a build</h4>
          <div class="info-note">
            Tap your completed instrument. Use Audacity → Analyze → Plot Spectrum to find A0
            (lowest body resonance peak, 80–130 Hz range). Enter all fields below.
            The calculator fits α from your measurement — no assumptions.
          </div>

          <div class="form-row">
            <div class="field-group">
              <label class="field-label">Build ID / instrument name</label>
              <input
                v-model="cId"
                type="text"
                class="text-input"
                placeholder="e.g. OM-007"
              >
            </div>
            <div class="field-group">
              <label class="field-label">Date measured</label>
              <input
                v-model="cDate"
                type="text"
                class="text-input"
              >
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label class="field-label">Body type</label>
              <select
                v-model="cBtype"
                class="select-input"
                @change="onCalBodyTypeChange"
              >
                <option
                  v-for="t in ['dread', 'om', 'jumbo', 'parlour', 'classical', 'custom']"
                  :key="t"
                  :value="t"
                >
                  {{ t }}
                </option>
              </select>
            </div>
            <div class="field-group">
              <label class="field-label">Body volume (L)</label>
              <input
                v-model.number="cVolL"
                type="number"
                class="text-input"
                min="8"
                max="35"
                step="0.5"
              >
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label class="field-label">Top wood species</label>
              <input
                v-model="cWood"
                type="text"
                class="text-input"
                placeholder="e.g. Engelmann spruce"
              >
            </div>
            <div class="field-group">
              <label class="field-label">Bracing style</label>
              <input
                v-model="cBrace"
                type="text"
                class="text-input"
                placeholder="e.g. Scalloped X"
              >
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label class="field-label">Soundhole shape</label>
              <select
                v-model="cShape"
                class="select-input"
              >
                <option value="round">
                  Round
                </option>
                <option value="slot">
                  Slot
                </option>
                <option value="dslot">
                  Double slot
                </option>
                <option value="fhole">
                  F-hole pair
                </option>
              </select>
            </div>
            <div class="field-group">
              <label class="field-label">Hole diameter or length (mm)</label>
              <input
                v-model.number="cDimMm"
                type="number"
                class="text-input"
                step="0.5"
              >
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label class="field-label">Top thickness at hole (mm)</label>
              <input
                v-model.number="cTopT"
                type="number"
                class="text-input"
                step="0.1"
              >
            </div>
            <div class="field-group">
              <label class="field-label key-field">Measured A0 (Hz) ← key field</label>
              <input
                v-model.number="cA0"
                type="number"
                class="text-input key-input"
                step="0.5"
              >
            </div>
          </div>

          <div class="field-group full-width">
            <label class="field-label">Notes (graduation, nut width, anomalies)</label>
            <textarea
              v-model="cNotes"
              class="text-input textarea"
              rows="2"
              placeholder="e.g. Top 2.7mm edges, 3.1mm center. Light scalloped X."
            />
          </div>

          <!-- Fitted results -->
          <div
            v-if="calFit"
            class="fitted-results"
          >
            <h5>Fitted values</h5>
            <div class="fitted-grid">
              <div class="fitted-item">
                <div class="fitted-value">
                  {{ cA0.toFixed(1) }}
                </div>
                <div class="fitted-label">
                  Hz measured A0
                </div>
              </div>
              <div class="fitted-item">
                <div class="fitted-value alpha">
                  {{ r2(calFit.alpha) }}
                </div>
                <div class="fitted-label">
                  fitted α
                </div>
              </div>
              <div class="fitted-item">
                <div class="fitted-value">
                  {{ r1(calFit.leff * 1000) }}
                </div>
                <div class="fitted-label">
                  mm Leff
                </div>
              </div>
            </div>
            <div class="fitted-interp">
              {{ interpAlpha(calFit.alpha) }}
            </div>
          </div>

          <button
            class="save-btn"
            @click="saveEntry"
          >
            Save to calibration log
          </button>
          <div
            v-if="saveMsg"
            class="save-msg"
          >
            {{ saveMsg }}
          </div>
        </div>

        <!-- Log -->
        <div class="card">
          <div class="log-header">
            <h4>Calibration log</h4>
            <span class="log-count">{{ log.length }} {{ log.length === 1 ? 'entry' : 'entries' }}</span>
          </div>

          <div
            v-if="logStats"
            class="log-stats"
          >
            <div class="stat-item">
              <div class="stat-value">
                {{ logStats.min }}
              </div>
              <div class="stat-label">
                α min
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">
                {{ logStats.mean }}
              </div>
              <div class="stat-label">
                α mean
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">
                {{ logStats.max }}
              </div>
              <div class="stat-label">
                α max
              </div>
            </div>
          </div>

          <div class="log-entries">
            <div
              v-if="log.length === 0"
              class="no-entries"
            >
              No entries yet. Record your first build on the left.
            </div>
            <LogEntry
              v-for="entry in [...log].reverse()"
              :key="entry.ts"
              :entry="entry"
              @use="useLogEntry"
              @delete="deleteEntry"
            />
          </div>

          <button
            v-if="log.length > 0"
            class="clear-btn"
            @click="clearLog"
          >
            Clear all entries
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick, defineComponent } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend
)

// ─── Physics constants ────────────────────────────────────────────────────────

const C = 343       // speed of sound m/s at 20°C
const I2M = 0.0254  // inches to metres
const L2M = 0.001   // litres to m³
const PA_THRESHOLD_HI = 0.10  // Williams 2019 significant gain threshold
const PA_THRESHOLD_LO = 0.08  // Williams 2019 approaching threshold

// ─── Gore published priors ────────────────────────────────────────────────────

interface GorePrior {
  label: string
  alpha: number
  vol: number
  diam: number
  range: string
  note: string
}

const GORE_PRIORS: GorePrior[] = [
  { label: 'Dreadnought', alpha: 1.63, vol: 24, diam: 4.00, range: '90–105 Hz', note: 'Gore & Gilet measured' },
  { label: 'OM / 000', alpha: 1.70, vol: 17, diam: 3.875, range: '100–115 Hz', note: 'Gore & Gilet' },
  { label: 'Jumbo', alpha: 1.65, vol: 28, diam: 4.25, range: '85–100 Hz', note: 'Gore & Gilet' },
  { label: 'Parlour', alpha: 1.75, vol: 13, diam: 3.50, range: '110–125 Hz', note: 'Gore & Gilet' },
  { label: 'Classical', alpha: 1.78, vol: 15, diam: 3.50, range: '115–130 Hz', note: 'Gore & Gilet' },
  { label: 'Rayleigh', alpha: 1.70, vol: 24, diam: 4.00, range: 'varies', note: 'Rigid baffle theory' }
]

const PA_DATA: [string, string, string, string][] = [
  ['Round R45', '—', '0.044', 'baseline'],
  ['S3 rect', '150×43', '0.060', '~same'],
  ['S6 rect', '210×31', '0.074', 'slight'],
  ['S6B C-slot', '300×21.7', '0.096', '~+30%'],
  ['S7 C-slot', '341×19', '0.112', '+60%'],
  ['S8 C-slot', '386×17', '0.123', '+60%'],
  ['DS1 S-slot', '2×380×17', '0.126', '+80%']
]

// ─── Utility functions ────────────────────────────────────────────────────────

const r1 = (n: number) => Math.round(n * 10) / 10
const r2 = (n: number) => Math.round(n * 100) / 100
const r3 = (n: number) => Math.round(n * 1000) / 1000
const ri = (n: number) => Math.round(n)

function helmholtz(area: number, vol: number, leff: number): number {
  if (area <= 0 || vol <= 0 || leff <= 0) return 0
  return (C / (2 * Math.PI)) * Math.sqrt(area / (vol * leff))
}

interface GeoResult {
  area: number
  perim: number
  leff: number
  model: string
  eff: number
  tone: string
  pa: number
}

interface GeoParams {
  shape: string
  diamIn: number
  slotLenMm: number
  slotWidMm: number
  fholeLenMm: number
  fholeWidMm: number
  topThickMm: number
  alpha: number
}

function getMainGeometry(params: GeoParams): GeoResult {
  const { shape, diamIn, slotLenMm, slotWidMm, fholeLenMm, fholeWidMm, topThickMm, alpha } = params
  const tT = topThickMm / 1000
  const al = alpha
  let area = 0, perim = 0, leff = 0, model = '', eff = 1.0, tone = ''

  if (shape === 'round' || shape === 'oval') {
    const r = (diamIn * I2M) / 2
    area = Math.PI * r * r
    perim = 2 * Math.PI * r
    leff = tT + al * r
    model = 'Area model (Helmholtz, round/oval)'
    eff = 1.0
    tone = 'Balanced bass/treble — round baseline'
  } else if (shape === 'slot' || shape === 'cslot') {
    const L = slotLenMm / 1000, W = slotWidMm / 1000
    area = L * W
    perim = 2 * (L + W)
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE
    model = 'Perimeter model (slot)'
    const pa = area > 0 ? perim / area : 0
    eff = pa > PA_THRESHOLD_HI ? 1.6 : pa > PA_THRESHOLD_LO ? 1.25 : 1.0
    tone = pa > PA_THRESHOLD_HI
      ? 'Treble gain, bass reduction vs round (Williams 2019)'
      : 'Similar to round below P:A threshold'
  } else if (shape === 'dslot') {
    const L = slotLenMm / 1000, W = slotWidMm / 1000
    area = L * W * 2
    perim = 2 * (L + W) * 2
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE
    model = 'Perimeter model (double slot)'
    const pa = area > 0 ? perim / area : 0
    eff = pa > PA_THRESHOLD_HI ? 1.8 : pa > PA_THRESHOLD_LO ? 1.3 : 1.0
    tone = pa > PA_THRESHOLD_HI
      ? 'Strong treble gain; upper bout freed as live soundboard area'
      : 'Approaching threshold — lengthen or narrow slot'
  } else if (shape === 'fhole') {
    const Lf = fholeLenMm / 1000, Wf = fholeWidMm / 1000
    const pH = 2 * (Lf + Wf) * 0.88
    area = pH * Wf * 0.95 * 2
    perim = pH * 2
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE * 0.78
    model = 'Nia et al. perimeter model (f-hole pair)'
    eff = 1.35
    tone = 'Higher treble efficiency vs equal-area round (Nia et al. 2015)'
  }

  const pa = area > 0 ? perim / area : 0
  return { area, perim, leff, model, eff, tone, pa }
}

interface FitResult {
  leff: number
  alpha: number
  ext: number
}

function fitAlpha(params: { area: number; topThickMm: number; measuredA0Hz: number; volL: number }): FitResult | null {
  const { area, topThickMm, measuredA0Hz, volL } = params
  const vol = volL * L2M
  const tT = topThickMm / 1000
  if (area <= 0 || measuredA0Hz <= 0 || vol <= 0) return null
  const fLeff = (C * C * area) / (4 * Math.PI * Math.PI * measuredA0Hz * measuredA0Hz * vol)
  const rEff = Math.sqrt(area / Math.PI)
  const fAlpha = rEff > 0 ? fLeff / rEff : 1.7
  return { leff: fLeff, alpha: fAlpha, ext: fLeff - tT }
}

function interpAlpha(alpha: number): string {
  if (alpha < 1.40) return 'Low — stiffer than typical or check measurement'
  if (alpha < 1.60) return 'Below Gore range — heavy bracing or stiff top'
  if (alpha <= 1.80) return 'Within Gore typical range (1.6–1.8)'
  if (alpha <= 1.95) return 'Above Gore range — compliant top or light bracing'
  return 'Unusually high — verify measurement'
}

interface CurvePoint {
  scale: number
  pct: number
  hz: number
}

function buildCurve(geo: GeoResult, sideArea: number, sideLeff: number, volM3: number): CurvePoint[] {
  const pts: CurvePoint[] = []
  for (let m = 0.7; m <= 1.3; m += 0.01) {
    const sa = sideArea * m
    const tot = geo.area + sa
    const lf = tot > 0 ? (geo.area * geo.leff + sa * sideLeff) / tot : geo.leff
    pts.push({ scale: r2(m), pct: ri(m * 100), hz: r1(helmholtz(tot, volM3, lf)) })
  }
  return pts
}

// ─── LocalStorage calibration log ────────────────────────────────────────────

const LOG_KEY = 'soundhole_cal_log'

interface LogEntryData {
  id: string
  date: string
  btype: string
  vol: number
  wood: string
  brace: string
  shape: string
  dim: number
  topt: number
  a0: number
  alpha: number
  leff: number
  notes: string
  ts: number
}

function loadLog(): LogEntryData[] {
  try {
    return JSON.parse(localStorage.getItem(LOG_KEY) || '[]')
  } catch {
    return []
  }
}

function saveLogToStorage(entries: LogEntryData[]) {
  localStorage.setItem(LOG_KEY, JSON.stringify(entries))
}

// ─── State ────────────────────────────────────────────────────────────────────

// Mode
const mode = ref<'design' | 'cal'>('design')

// Design inputs
const alpha = ref(1.70)
const alphaSource = ref('Gore — OM / default prior')
const volL = ref(24)
const targetHz = ref(100)
const shape = ref('round')
const diamIn = ref(4.0)
const slotLenMm = ref(150)
const slotWidMm = ref(43)
const fholeLenMm = ref(85)
const fholeWidMm = ref(6)
const topThickMm = ref(3.0)
const sideDmm = ref(40)
const sideThickMm = ref(2.3)
const sideCount = ref(1)

// Design sub-tab
type DesignTab = 'alpha' | 'body' | 'hole' | 'side' | 'pa'
const dTab = ref<DesignTab>('alpha')
function setDTab(t: string) {
  dTab.value = t as DesignTab
}

// Calibration inputs
const cId = ref('')
const cDate = ref(new Date().toISOString().slice(0, 10))
const cBtype = ref('dread')
const cVolL = ref(24)
const cWood = ref('')
const cBrace = ref('')
const cShape = ref('round')
const cDimMm = ref(101.6)
const cTopT = ref(3.0)
const cA0 = ref(98)
const cNotes = ref('')
const saveMsg = ref('')

// Calibration log
const log = ref<LogEntryData[]>(loadLog())

// Chart
const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

// ─── Computed ─────────────────────────────────────────────────────────────────

const geo = computed(() => getMainGeometry({
  shape: shape.value,
  diamIn: diamIn.value,
  slotLenMm: slotLenMm.value,
  slotWidMm: slotWidMm.value,
  fholeLenMm: fholeLenMm.value,
  fholeWidMm: fholeWidMm.value,
  topThickMm: topThickMm.value,
  alpha: alpha.value
}))

const volM3 = computed(() => volL.value * L2M)
const sideR = computed(() => sideDmm.value / 1000 / 2)
const sideA = computed(() => Math.PI * sideR.value * sideR.value * sideCount.value)
const sideLeff = computed(() => sideThickMm.value / 1000 + alpha.value * sideR.value)
const totA = computed(() => geo.value.area + sideA.value)
const cLeff = computed(() => totA.value > 0 ? (geo.value.area * geo.value.leff + sideA.value * sideLeff.value) / totA.value : geo.value.leff)
const mainHz = computed(() => helmholtz(geo.value.area, volM3.value, geo.value.leff))
const combHz = computed(() => helmholtz(totA.value, volM3.value, cLeff.value))
const shift = computed(() => combHz.value - mainHz.value)
const share = computed(() => totA.value > 0 ? (sideA.value / totA.value) * 100 : 0)

const curve = computed(() => buildCurve(geo.value, sideA.value, sideLeff.value, volM3.value))

const paLabel = computed(() => {
  if (geo.value.pa > PA_THRESHOLD_HI) return 'above threshold'
  if (geo.value.pa > PA_THRESHOLD_LO) return 'approaching 0.10'
  return 'below threshold'
})

const verdictText = computed(() => {
  let v = combHz.value < 85 ? 'Very low A0 — warm, loose bass.'
    : combHz.value < 95 ? 'Low A0 — rich bass, large-body character.'
    : combHz.value <= 110 ? 'Typical dreadnought/OM zone — balanced voicing.'
    : combHz.value <= 120 ? 'Moderate-high A0 — tighter, quicker response.'
    : 'High A0 — lean low end, typical parlour or classical.'
  if (geo.value.pa > PA_THRESHOLD_HI) v += ' High P:A slot: +60–80% radiated power vs round (Williams 2019).'
  v += ` α = ${alpha.value.toFixed(2)} (${alphaSource.value.slice(0, 40)}).`
  return v
})

// Calibration
const calArea = computed(() => {
  const d = cDimMm.value / 1000
  if (cShape.value === 'round') return Math.PI * (d / 2) * (d / 2)
  if (cShape.value === 'slot') return d * 0.04
  if (cShape.value === 'dslot') return d * 0.035 * 2
  if (cShape.value === 'fhole') return d * 0.006 * 2
  return 0
})

const calFit = computed(() => fitAlpha({
  area: calArea.value,
  topThickMm: cTopT.value,
  measuredA0Hz: cA0.value,
  volL: cVolL.value
}))

const userPriors = computed(() => {
  const byType: Record<string, number[]> = {}
  log.value.forEach(e => {
    if (!byType[e.btype]) byType[e.btype] = []
    byType[e.btype].push(e.alpha)
  })
  return Object.entries(byType).map(([bt, alphas]) => ({
    label: bt,
    alpha: r2(alphas.reduce((a, b) => a + b, 0) / alphas.length),
    n: alphas.length
  }))
})

const logStats = computed(() => {
  if (log.value.length === 0) return null
  const alphas = log.value.map(e => e.alpha)
  return {
    min: r2(Math.min(...alphas)),
    max: r2(Math.max(...alphas)),
    mean: r2(alphas.reduce((a, b) => a + b, 0) / alphas.length)
  }
})

// ─── Methods ──────────────────────────────────────────────────────────────────

function applyGore(prior: GorePrior) {
  alpha.value = prior.alpha
  alphaSource.value = `Gore — ${prior.label} (${prior.note})`
  volL.value = prior.vol
  diamIn.value = prior.diam
}

function applyUserPrior(prior: { label: string; alpha: number; n: number }) {
  alpha.value = prior.alpha
  alphaSource.value = `Your mean: ${prior.label} (${prior.n} builds)`
}

function useLogEntry(entry: LogEntryData) {
  alpha.value = entry.alpha
  alphaSource.value = `Measured: ${entry.id} (${entry.date})`
  mode.value = 'design'
}

function saveEntry() {
  if (!calFit.value) return
  const entry: LogEntryData = {
    id: cId.value.trim() || `Build ${new Date().toLocaleDateString()}`,
    date: cDate.value,
    btype: cBtype.value,
    vol: cVolL.value,
    wood: cWood.value,
    brace: cBrace.value,
    shape: cShape.value,
    dim: cDimMm.value,
    topt: cTopT.value,
    a0: cA0.value,
    alpha: r2(calFit.value.alpha),
    leff: r1(calFit.value.leff * 1000),
    notes: cNotes.value,
    ts: Date.now()
  }
  log.value = [...log.value, entry]
  saveMsg.value = `Saved — ${entry.id}`
  setTimeout(() => { saveMsg.value = '' }, 3000)
}

function deleteEntry(ts: number) {
  log.value = log.value.filter(e => e.ts !== ts)
}

function clearLog() {
  if (window.confirm('Clear all calibration entries?')) {
    log.value = []
  }
}

function onGuitarTypeChange() {
  const p = GORE_PRIORS.find(g => g.vol === volL.value)
  if (p) {
    diamIn.value = p.diam
  }
}

function onCalBodyTypeChange() {
  const p = GORE_PRIORS.find(g => g.label.toLowerCase().includes(cBtype.value))
  if (p) {
    cVolL.value = p.vol
  }
}

function gainClass(g: string): string {
  if (g.includes('+6') || g.includes('+8')) return 'high'
  if (g.includes('+3')) return 'medium'
  return 'low'
}

// ─── Chart ────────────────────────────────────────────────────────────────────

function createChart() {
  if (!chartCanvas.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: curve.value.map(p => `${p.pct}%`),
      datasets: [{
        label: 'A0 (Hz)',
        data: curve.value.map(p => p.hz),
        borderColor: '#0F6E56',
        backgroundColor: 'rgba(15, 110, 86, 0.1)',
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `${context.parsed.y} Hz`
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Port Scale' },
          ticks: { font: { size: 10 } }
        },
        y: {
          title: { display: true, text: 'A0 (Hz)' },
          ticks: { font: { size: 10 } }
        }
      }
    }
  })
}

// ─── Watchers ─────────────────────────────────────────────────────────────────

watch(log, (newLog) => {
  saveLogToStorage(newLog)
}, { deep: true })

watch(
  [curve, targetHz, () => mode.value],
  () => {
    if (mode.value === 'design') {
      nextTick(() => createChart())
    }
  }
)

// ─── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  nextTick(() => {
    if (mode.value === 'design') {
      createChart()
    }
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<!-- Sub-components defined inline for simplicity -->
<script lang="ts">
// MetricCard component
const MetricCard = {
  name: 'MetricCard',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    sub: { type: String, default: '' },
    accent: { type: String, default: undefined }
  },
  template: `
    <div class="metric-card">
      <div class="metric-label">{{ label }}</div>
      <div class="metric-value" :style="{ color: accent }">{{ value }}</div>
      <div v-if="sub" class="metric-sub">{{ sub }}</div>
    </div>
  `
}

// SliderRow component
const SliderRow = {
  name: 'SliderRow',
  props: {
    label: { type: String, required: true },
    id: { type: String, required: true },
    min: { type: Number, required: true },
    max: { type: Number, required: true },
    step: { type: Number, required: true },
    value: { type: Number, required: true },
    display: { type: String, required: true }
  },
  emits: ['update'],
  template: `
    <div class="slider-row">
      <label :for="id" class="slider-label">{{ label }}</label>
      <input
        type="range"
        :id="id"
        :min="min"
        :max="max"
        :step="step"
        :value="value"
        @input="$emit('update', parseFloat($event.target.value))"
        class="slider-input"
      />
      <span class="slider-display">{{ display }}</span>
    </div>
  `
}

// InfoRow component
const InfoRow = {
  name: 'InfoRow',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    mono: { type: Boolean, default: false }
  },
  template: `
    <div class="info-row">
      <span class="info-label">{{ label }}</span>
      <span :class="['info-value', { mono }]">{{ value }}</span>
    </div>
  `
}

// PAGauge component - typed with defineComponent for TypeScript
const PAGauge = defineComponent({
  name: 'PAGauge',
  props: {
    pa: { type: Number, required: true }
  },
  computed: {
    pct(): number { return Math.min(100, (this.pa ?? 0) / 0.13 * 100) },
    color(): string {
      const pa = this.pa ?? 0
      return pa > 0.10 ? '#0F6E56' : pa > 0.08 ? '#BA7517' : '#888780'
    },
    label(): string {
      const pa = this.pa ?? 0
      return pa > 0.10 ? 'above threshold' : pa > 0.08 ? 'approaching 0.10' : 'below threshold'
    },
    description(): string {
      const pa = this.pa ?? 0
      if (pa > 0.10) return 'Above 0.10: Williams 2019 measured +60% (single slot) to +80% (double slot) vs equal-area round. Gains mainly in 165–330 Hz band.'
      if (pa > 0.08) return 'Approaching threshold. Lengthen or narrow the slot to push P:A above 0.10.'
      return 'Below 0.08: perimeter effect not dominant. Little efficiency advantage over round.'
    }
  },
  template: `
    <div class="pa-gauge">
      <div class="pa-header">
        <span class="pa-title">P:A efficiency</span>
        <span :class="['pa-badge', pa > 0.10 ? 'high' : pa > 0.08 ? 'med' : 'low']">{{ label }}</span>
      </div>
      <div class="pa-bar-bg">
        <div class="pa-bar" :style="{ width: pct + '%', background: color }" />
      </div>
      <div class="pa-scale">
        <span>0</span>
        <span class="med-marker">0.08</span>
        <span class="hi-marker">0.10</span>
        <span>0.13</span>
      </div>
      <div class="pa-desc">{{ description }}</div>
    </div>
  `
})

// LogEntry component
const LogEntry = {
  name: 'LogEntry',
  props: {
    entry: { type: Object, required: true }
  },
  emits: ['use', 'delete'],
  template: `
    <div class="log-entry">
      <div class="entry-info">
        <div class="entry-id">{{ entry.id }}</div>
        <div class="entry-meta">{{ entry.date }} · {{ entry.btype }} · {{ entry.wood || '—' }} · {{ entry.brace || '—' }}</div>
        <div class="entry-data">A0 = {{ entry.a0 }} Hz · Leff = {{ entry.leff }} mm · {{ entry.shape }}</div>
        <div v-if="entry.notes" class="entry-notes">{{ entry.notes }}</div>
      </div>
      <div class="entry-actions">
        <div class="entry-alpha">α {{ entry.alpha }}</div>
        <button class="use-btn" @click="$emit('use', entry)">use in design</button>
        <button class="delete-btn" @click="$emit('delete', entry.ts)">delete</button>
      </div>
    </div>
  `
}

export default {
  components: { MetricCard, SliderRow, InfoRow, PAGauge, LogEntry }
}
</script>

<style scoped>
.soundhole-calculator {
  padding: 1.5rem;
  font-family: system-ui, -apple-system, sans-serif;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 1rem;
}

.header h2 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  color: #2c3e50;
}

.subtitle {
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
}

.mode-switcher {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.mode-btn {
  flex: 1;
  padding: 0.65rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  background: #f5f5f5;
  color: #666;
  transition: all 0.2s;
}

.mode-btn.active {
  background: #fff;
  color: #111;
  border-color: #3b82f6;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.metric-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.metric-label {
  font-size: 0.7rem;
  color: #666;
  margin-bottom: 0.2rem;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.metric-sub {
  font-size: 0.65rem;
  color: #999;
  margin-top: 0.15rem;
}

.design-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 1rem 1.25rem;
}

.controls-card {
  /* specific styles for left panel */
}

.tab-bar {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.25rem;
  flex-wrap: wrap;
}

.tab-btn {
  font-size: 0.8rem;
  padding: 0.3rem 0.7rem;
  border: none;
  cursor: pointer;
  border-radius: 5px 5px 0 0;
  background: none;
  color: #666;
  font-weight: 400;
}

.tab-btn.active {
  background: #f0f0f0;
  color: #111;
  font-weight: 600;
}

.tab-content h4 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #2c3e50;
}

.tab-content h5 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem;
  color: #444;
}

.info-note {
  font-size: 0.75rem;
  color: #555;
  background: #f5f5f5;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  border-left: 3px solid #185FA5;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.alpha-display {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
}

.alpha-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #185FA5;
}

.alpha-source {
  font-size: 0.75rem;
  color: #555;
  margin-top: 0.15rem;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.slider-label {
  font-size: 0.8rem;
  color: #555;
  min-width: 9.5rem;
}

.slider-input {
  flex: 1;
}

.slider-display {
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 4rem;
  text-align: right;
}

.prior-badges {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.prior-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.prior-badge.gore {
  background: #E6F1FB;
  color: #0C447C;
}

.prior-badge.user {
  background: #E1F5EE;
  color: #085041;
}

.no-data {
  font-size: 0.75rem;
  color: #aaa;
  margin-top: 0.5rem;
}

.info-rows {
  margin-top: 0.75rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  padding: 0.3rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.info-label {
  color: #555;
}

.info-value {
  font-weight: 400;
}

.info-value.mono {
  font-family: monospace;
  font-weight: 600;
}

.field-group {
  margin-bottom: 0.65rem;
}

.field-label {
  display: block;
  font-size: 0.75rem;
  color: #555;
  margin-bottom: 0.2rem;
}

.select-input,
.text-input {
  font-size: 0.85rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  width: 100%;
  background: #fff;
  color: #111;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.right-column h4 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.chart-container {
  position: relative;
  height: 130px;
}

.chart-note {
  font-size: 0.7rem;
  color: #aaa;
  margin-top: 0.25rem;
}

/* PA Gauge */
.pa-gauge {
  /* contained in card */
}

.pa-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.35rem;
}

.pa-title {
  font-size: 0.95rem;
  font-weight: 600;
}

.pa-badge {
  font-size: 0.65rem;
  padding: 0.15rem 0.5rem;
  border-radius: 5px;
  font-weight: 600;
}

.pa-badge.high {
  background: #E1F5EE;
  color: #0F6E56;
}

.pa-badge.med {
  background: #FAEEDA;
  color: #BA7517;
}

.pa-badge.low {
  background: #F1EFE8;
  color: #888780;
}

.pa-bar-bg {
  height: 7px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.pa-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.pa-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.65rem;
  color: #999;
  margin-top: 0.2rem;
}

.med-marker {
  color: #BA7517;
}

.hi-marker {
  color: #0F6E56;
  font-weight: 700;
}

.pa-desc {
  font-size: 0.75rem;
  color: #555;
  margin-top: 0.5rem;
  line-height: 1.5;
}

/* PA Table */
.pa-note {
  font-size: 0.75rem;
  color: #555;
  margin-bottom: 0.5rem;
}

.pa-table {
  width: 100%;
  font-size: 0.75rem;
  border-collapse: collapse;
}

.pa-table th {
  padding: 0.2rem 0.3rem;
  color: #666;
  border-bottom: 1px solid #ddd;
  text-align: left;
}

.pa-table td {
  padding: 0.25rem 0.3rem;
  border-bottom: 1px solid #eee;
}

.pa-table .mono {
  font-family: monospace;
}

.gain-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-weight: 600;
}

.gain-badge.high {
  background: #E1F5EE;
  color: #085041;
}

.gain-badge.medium {
  background: #FAEEDA;
  color: #633806;
}

.gain-badge.low {
  background: #F1EFE8;
  color: #444;
}

.pa-footer {
  font-size: 0.65rem;
  color: #999;
  margin-top: 0.5rem;
  line-height: 1.5;
}

/* Verdict */
.verdict-card h4 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.verdict-text {
  font-size: 0.85rem;
  line-height: 1.7;
  padding: 0.65rem 0.9rem;
  background: #f5f5f5;
  border-radius: 8px;
  color: #555;
}

/* Calibration Mode */
.cal-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.full-width {
  margin-bottom: 0.75rem;
}

.textarea {
  resize: vertical;
}

.key-field {
  font-weight: 600;
  color: #185FA5;
}

.key-input {
  font-weight: 700;
  font-size: 1rem;
}

.fitted-results {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
}

.fitted-results h5 {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.fitted-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.fitted-item {
  text-align: center;
  background: #fff;
  border-radius: 6px;
  padding: 0.5rem 0.3rem;
}

.fitted-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.fitted-value.alpha {
  color: #0F6E56;
}

.fitted-label {
  font-size: 0.65rem;
  color: #666;
}

.fitted-interp {
  font-size: 0.75rem;
  color: #555;
}

.save-btn {
  width: 100%;
  padding: 0.65rem;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid #ccc;
  background: #fff;
  cursor: pointer;
}

.save-btn:hover {
  background: #f5f5f5;
}

.save-msg {
  font-size: 0.75rem;
  color: #0F6E56;
  margin-top: 0.35rem;
}

/* Log */
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.log-header h4 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.log-count {
  font-size: 0.75rem;
  color: #666;
}

.log-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.stat-item {
  text-align: center;
  background: #f5f5f5;
  border-radius: 6px;
  padding: 0.4rem 0.3rem;
}

.stat-value {
  font-size: 1rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.65rem;
  color: #666;
}

.log-entries {
  max-height: 30rem;
  overflow-y: auto;
}

.no-entries {
  text-align: center;
  padding: 2rem;
  color: #aaa;
  font-size: 0.85rem;
}

.log-entry {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #eee;
  font-size: 0.8rem;
}

.entry-info {
  flex: 1;
}

.entry-id {
  font-weight: 600;
}

.entry-meta,
.entry-data {
  color: #666;
  font-size: 0.75rem;
  margin-top: 0.15rem;
}

.entry-notes {
  color: #999;
  font-size: 0.75rem;
  margin-top: 0.15rem;
}

.entry-actions {
  text-align: right;
  flex-shrink: 0;
  margin-left: 0.75rem;
}

.entry-alpha {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0F6E56;
}

.use-btn {
  font-size: 0.65rem;
  margin-top: 0.2rem;
  padding: 0.15rem 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: none;
  cursor: pointer;
  color: #185FA5;
  display: block;
}

.delete-btn {
  font-size: 0.65rem;
  margin-top: 0.15rem;
  border: none;
  background: none;
  cursor: pointer;
  color: #aaa;
  padding: 0;
}

.clear-btn {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #A32D2D;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

@media (max-width: 900px) {
  .metric-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .design-grid,
  .cal-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
