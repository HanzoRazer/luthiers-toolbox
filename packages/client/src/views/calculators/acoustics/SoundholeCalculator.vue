<template>
  <div class="soundhole-calculator" :style="{ padding: '1rem 0', fontFamily: 'var(--font-sans, system-ui)' }">
    <!-- Header -->
    <div :style="{ marginBottom: '13px' }">
      <div :style="{ fontSize: '15px', fontWeight: 700, marginBottom: '3px' }">
        Guitar soundhole: Helmholtz + P:A calculator with builder calibration log
      </div>
      <div :style="{ fontSize: '12px', color: 'var(--color-text-secondary, #555)' }">
        Two modes: Design (Gore priors + your data) and Calibration (tap-test a build, fit α, save to log).
        α is a system property — only measurement gives you the right value for your instrument.
      </div>
    </div>

    <!-- Mode switcher -->
    <div :style="{ display: 'flex', gap: '6px', marginBottom: '14px' }">
      <button :style="modeBtn(mode === 'design')" @click="mode = 'design'">
        Design mode — explore geometry
      </button>
      <button :style="modeBtn(mode === 'cal')" @click="mode = 'cal'">
        Calibration mode — record a build
      </button>
    </div>

    <!-- DESIGN MODE -->
    <template v-if="mode === 'design'">
      <!-- Metric strip -->
      <div :style="{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: '10px', marginBottom: '12px' }">
        <MetricCard label="Main hole A0" :value="`${r1(mainHz)} Hz`" sub="no side port" />
        <MetricCard label="Combined A0" :value="`${r1(combHz)} Hz`" sub="with side port" />
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

      <div :style="{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: '12px', marginBottom: '12px' }">
        <!-- Left: controls -->
        <div :style="cardStyle">
          <!-- Tab bar -->
          <div :style="{ display: 'flex', gap: '3px', marginBottom: '11px', borderBottom: '0.5px solid var(--color-border-tertiary, #ddd)', paddingBottom: '2px', flexWrap: 'wrap' }">
            <button
              v-for="t in ['alpha','body','hole','side','pa']"
              :key="t"
              :style="tabStyle(dTab === t)"
              @click="dTab = t"
            >
              {{ t === 'alpha' ? 'α source' : t === 'pa' ? 'P:A data' : t.charAt(0).toUpperCase() + t.slice(1) }}
            </button>
          </div>

          <!-- α source tab -->
          <div v-if="dTab === 'alpha'">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }">Gore end-correction factor α</div>
            <div :style="priNote">
              α is a system property — body geometry, soundhole position, top compliance, and bracing all affect it simultaneously.
              No material table can give you α. Use Gore priors as starting estimates, then calibrate from measurement.
            </div>
            <div :style="{ background: 'var(--color-background-secondary, #f5f5f5)', borderRadius: '8px', padding: '10px 12px', marginBottom: '10px' }">
              <div :style="{ fontSize: '24px', fontWeight: 700, color: '#185FA5' }">{{ alpha.toFixed(2) }}</div>
              <div :style="{ fontSize: '11px', color: 'var(--color-text-secondary, #555)', marginTop: '2px' }">{{ alphaSource }}</div>
            </div>
            <SliderRow
              label="Set α manually"
              id="alpha"
              :min="1.20"
              :max="2.20"
              :step="0.01"
              :value="alpha"
              @update="v => { alpha = v; alphaSource = 'Manual'; }"
              :display="alpha.toFixed(2)"
            />

            <div :style="{ fontSize: '12px', fontWeight: 600, marginTop: '10px', marginBottom: '6px' }">Gore published priors</div>
            <div :style="{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginBottom: '10px' }">
              <button
                v-for="p in GORE_PRIORS"
                :key="p.label"
                @click="applyGore(p)"
                :style="priorBadge({ background: '#E6F1FB', color: '#0C447C' })"
              >
                {{ p.label }} {{ p.alpha }}
              </button>
            </div>

            <template v-if="userPriors.length > 0">
              <div :style="{ fontSize: '12px', fontWeight: 600, marginBottom: '6px' }">Your measured priors</div>
              <div :style="{ display: 'flex', gap: '5px', flexWrap: 'wrap' }">
                <button
                  v-for="p in userPriors"
                  :key="p.label"
                  @click="applyUserPrior(p)"
                  :style="priorBadge({ background: '#E1F5EE', color: '#085041' })"
                >
                  {{ p.label }} {{ p.alpha }} (n={{ p.n }})
                </button>
              </div>
            </template>
            <div v-else :style="{ fontSize: '11px', color: 'var(--color-text-tertiary, #aaa)', marginTop: '6px' }">
              No calibration data yet. Add builds in Calibration mode.
            </div>

            <div :style="{ marginTop: '10px' }">
              <InfoRow label="Rayleigh rigid baffle (theory)" value="1.70" mono />
              <InfoRow label="Gore dreadnought (measured)" value="1.63" mono />
              <InfoRow label="Gore typical range" value="1.60 – 1.80" mono />
              <InfoRow label="Leff at current α" :value="`${r1(geo.leff * 1000)} mm`" mono />
            </div>
          </div>

          <!-- Body tab -->
          <div v-if="dTab === 'body'">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '9px' }">Body</div>
            <div :style="{ marginBottom: '9px' }">
              <label :style="{ fontSize: '12px', color: 'var(--color-text-secondary, #555)', display: 'block', marginBottom: '3px' }">Guitar type</label>
              <select :value="volL" @change="handleBodyTypeChange" :style="{ ...textInput, width: '100%' }">
                <option v-for="p in GORE_PRIORS.filter(p => p.label !== 'Rayleigh')" :key="p.label" :value="p.vol">{{ p.label }}</option>
              </select>
            </div>
            <SliderRow label="Body volume (L)" id="vol" :min="8" :max="35" :step="0.5" :value="volL" @update="volL = $event" :display="`${r1(volL)} L`" />
            <SliderRow label="Target A0 reference (Hz)" id="tgt" :min="70" :max="140" :step="1" :value="targetHz" @update="targetHz = $event" :display="`${ri(targetHz)} Hz`" />
            <div :style="{ marginTop: '8px' }">
              <InfoRow label="Volume (m³)" :value="`${(volL * L2M).toFixed(3)} m³`" />
            </div>
          </div>

          <!-- Hole tab -->
          <div v-if="dTab === 'hole'">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '9px' }">Main soundhole</div>
            <div :style="{ marginBottom: '9px' }">
              <label :style="fieldLabel">Shape</label>
              <select v-model="shape" :style="textInput">
                <option value="round">Round</option>
                <option value="oval">Oval</option>
                <option value="slot">Single slot</option>
                <option value="dslot">Double slot</option>
                <option value="fhole">F-hole pair</option>
                <option value="cslot">C-slot</option>
              </select>
            </div>
            <template v-if="shape === 'round' || shape === 'oval'">
              <SliderRow label="Diameter (in)" id="diam" :min="2.5" :max="5.5" :step="0.05" :value="diamIn" @update="diamIn = $event" :display="`${diamIn.toFixed(2)} in`" />
            </template>
            <template v-if="shape === 'slot' || shape === 'dslot' || shape === 'cslot'">
              <SliderRow label="Length (mm)" id="slen" :min="40" :max="420" :step="5" :value="slotLenMm" @update="slotLenMm = $event" :display="`${ri(slotLenMm)} mm`" />
              <SliderRow label="Width (mm)" id="swid" :min="5" :max="50" :step="1" :value="slotWidMm" @update="slotWidMm = $event" :display="`${ri(slotWidMm)} mm`" />
            </template>
            <template v-if="shape === 'fhole'">
              <SliderRow label="F-hole length (mm)" id="flen" :min="60" :max="130" :step="2" :value="fholeLenMm" @update="fholeLenMm = $event" :display="`${ri(fholeLenMm)} mm`" />
              <SliderRow label="Waist width (mm)" id="fwid" :min="3" :max="14" :step="0.5" :value="fholeWidMm" @update="fholeWidMm = $event" :display="`${fholeWidMm.toFixed(1)} mm`" />
            </template>
            <SliderRow label="Top thickness (mm)" id="topt" :min="2" :max="5.5" :step="0.1" :value="topThickMm" @update="topThickMm = $event" :display="`${r1(topThickMm)} mm`" />
            <div :style="{ marginTop: '8px' }">
              <InfoRow label="Effective area" :value="`${r2(geo.area * 1e4)} cm²`" mono />
              <InfoRow label="Perimeter" :value="`${r1(geo.perim * 1000)} mm`" mono />
              <InfoRow label="P:A ratio" :value="`${r3(geo.pa)} m⁻¹`" mono />
              <InfoRow label="Leff" :value="`${r1(geo.leff * 1000)} mm`" mono />
            </div>
          </div>

          <!-- Side tab -->
          <div v-if="dTab === 'side'">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '9px' }">Side soundport</div>
            <SliderRow label="Port diameter (mm)" id="sided" :min="0" :max="80" :step="1" :value="sideDmm" @update="sideDmm = $event" :display="`${ri(sideDmm)} mm`" />
            <SliderRow label="Side thickness (mm)" id="sidet" :min="1.5" :max="5" :step="0.1" :value="sideThickMm" @update="sideThickMm = $event" :display="`${r1(sideThickMm)} mm`" />
            <div :style="{ marginBottom: '8px' }">
              <label :style="fieldLabel">Count</label>
              <select v-model.number="sideCount" :style="textInput">
                <option :value="1">1 port</option>
                <option :value="2">2 ports</option>
              </select>
            </div>
            <div :style="{ marginTop: '8px' }">
              <InfoRow label="Port area" :value="`${r2(sideA * 1e4)} cm²`" mono />
              <InfoRow label="A0 shift" :value="`${shift >= 0 ? '+' : ''}${r1(shift)} Hz`" mono />
              <InfoRow label="Port share of total" :value="`${r1(share)}%`" mono />
              <InfoRow label="φ-based diameter" :value="`${r1((diamIn * 25.4) / 1.618)} mm`" mono />
              <InfoRow label="Note" value="diameter÷φ ≠ area÷φ (area scales r²)" />
            </div>
          </div>

          <!-- P:A data tab -->
          <div v-if="dTab === 'pa'">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }">Williams (2019) P:A experimental data</div>
            <div :style="{ fontSize: '11px', color: 'var(--color-text-secondary, #555)', marginBottom: '8px' }">
              All slots equal-area to R45.4mm round. Rigid parlour cavity. R² = 0.953.
            </div>
            <table :style="{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }">
              <thead>
                <tr :style="{ color: 'var(--color-text-secondary, #666)', borderBottom: '0.5px solid var(--color-border-tertiary, #ddd)' }">
                  <td :style="{ padding: '2px 4px' }">Slot</td>
                  <td>Dims (mm)</td>
                  <td>P:A</td>
                  <td>Gain</td>
                </tr>
              </thead>
              <tbody>
                <tr v-for="[s, d, pa, g] in paTableData" :key="s" :style="{ borderBottom: '0.5px solid var(--color-border-tertiary, #eee)' }">
                  <td :style="{ padding: '3px 4px' }">{{ s }}</td>
                  <td>{{ d }}</td>
                  <td :style="{ fontFamily: 'monospace' }">{{ pa }}</td>
                  <td>
                    <span :style="{
                      fontSize: '10px', padding: '1px 5px', borderRadius: '4px', fontWeight: 600,
                      background: g.includes('+6') || g.includes('+8') ? '#E1F5EE' : g.includes('+3') ? '#FAEEDA' : '#F1EFE8',
                      color: g.includes('+6') || g.includes('+8') ? '#085041' : g.includes('+3') ? '#633806' : '#444'
                    }">{{ g }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div :style="{ fontSize: '10px', color: 'var(--color-text-tertiary, #999)', marginTop: '6px', lineHeight: 1.5 }">
              High P:A shifts tone toward treble. Double slot also frees upper bout as live soundboard area.
              Source: mwguitars.com.au Parts 7–8.
            </div>
          </div>
        </div>

        <!-- Right: gauge + curve -->
        <div>
          <div :style="{ ...cardStyle, marginBottom: '12px' }">
            <PAGauge :pa="geo.pa" />
          </div>
          <div :style="{ ...cardStyle, marginBottom: '12px' }">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }">A0 vs side-port scale</div>
            <CurveChart :data="curve" :target="targetHz" />
            <div :style="{ fontSize: '10px', color: 'var(--color-text-tertiary, #aaa)', marginTop: '3px' }">
              Port scaled 70–130%. Dashed = target A0.
            </div>
          </div>
          <div :style="cardStyle">
            <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }">Geometry summary</div>
            <InfoRow label="Main hole A0" :value="`${r1(mainHz)} Hz`" mono />
            <InfoRow label="Combined A0" :value="`${r1(combHz)} Hz`" mono />
            <InfoRow label="Shift from port" :value="`${shift >= 0 ? '+' : ''}${r1(shift)} Hz`" mono />
            <InfoRow label="Efficiency est." :value="`+${ri((geo.eff - 1) * 100)}%`" mono />
            <InfoRow label="Tone shift" :value="geo.tone" />
          </div>
        </div>
      </div>

      <!-- Verdict -->
      <div :style="cardStyle">
        <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }">Design verdict</div>
        <div :style="{ fontSize: '12px', lineHeight: 1.7, padding: '9px 12px', background: 'var(--color-background-secondary, #f5f5f5)', borderRadius: '8px', color: 'var(--color-text-secondary, #555)' }">
          {{ verdictText }}
        </div>
      </div>
    </template>

    <!-- CALIBRATION MODE -->
    <template v-if="mode === 'cal'">
      <div :style="{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: '12px' }">
        <!-- Form -->
        <div :style="cardStyle">
          <div :style="{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }">Record a build</div>
          <div :style="priNote">
            Tap your completed instrument. Use Audacity → Analyze → Plot Spectrum to find A0
            (lowest body resonance peak, 80–130 Hz range). Enter all fields below.
            The calculator fits α from your measurement — no assumptions.
          </div>

          <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }">
            <div :style="fieldGroup">
              <label :style="fieldLabel">Build ID / instrument name</label>
              <input :style="textInput" v-model="cId" placeholder="e.g. OM-007" />
            </div>
            <div :style="fieldGroup">
              <label :style="fieldLabel">Date measured</label>
              <input :style="textInput" type="text" v-model="cDate" />
            </div>
          </div>

          <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }">
            <div :style="fieldGroup">
              <label :style="fieldLabel">Body type</label>
              <select :style="textInput" v-model="cBtype" @change="handleCalBodyTypeChange">
                <option v-for="t in ['dread','om','jumbo','parlour','classical','custom']" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div :style="fieldGroup">
              <label :style="fieldLabel">Body volume (L)</label>
              <input :style="textInput" type="number" v-model.number="cVolL" min="8" max="35" step="0.5" />
            </div>
          </div>

          <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }">
            <div :style="fieldGroup">
              <label :style="fieldLabel">Top wood species</label>
              <input :style="textInput" v-model="cWood" placeholder="e.g. Engelmann spruce" />
            </div>
            <div :style="fieldGroup">
              <label :style="fieldLabel">Bracing style</label>
              <input :style="textInput" v-model="cBrace" placeholder="e.g. Scalloped X" />
            </div>
          </div>

          <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }">
            <div :style="fieldGroup">
              <label :style="fieldLabel">Soundhole shape</label>
              <select :style="textInput" v-model="cShape">
                <option value="round">Round</option>
                <option value="slot">Slot</option>
                <option value="dslot">Double slot</option>
                <option value="fhole">F-hole pair</option>
              </select>
            </div>
            <div :style="fieldGroup">
              <label :style="fieldLabel">Hole diameter or length (mm)</label>
              <input :style="textInput" type="number" v-model.number="cDimMm" step="0.5" />
            </div>
          </div>

          <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }">
            <div :style="fieldGroup">
              <label :style="fieldLabel">Top thickness at hole (mm)</label>
              <input :style="textInput" type="number" v-model.number="cTopT" step="0.1" />
            </div>
            <div :style="fieldGroup">
              <label :style="fieldLabel">Measured A0 (Hz) ← key field</label>
              <input :style="{ ...textInput, fontWeight: 700, fontSize: '14px' }" type="number" v-model.number="cA0" step="0.5" />
            </div>
          </div>

          <div :style="{ ...fieldGroup, marginBottom: '10px' }">
            <label :style="fieldLabel">Notes (graduation, nut width, anomalies)</label>
            <textarea :style="{ ...textInput, resize: 'vertical' }" rows="2" v-model="cNotes"
              placeholder="e.g. Top 2.7mm edges, 3.1mm center. Light scalloped X." />
          </div>

          <!-- Fitted results -->
          <div v-if="calFit" :style="{ ...cardStyle, background: 'var(--color-background-secondary, #f5f5f5)', marginBottom: '10px' }">
            <div :style="{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }">Fitted values</div>
            <div :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '8px' }">
              <div :style="{ textAlign: 'center', background: 'var(--color-background-primary, #fff)', borderRadius: '6px', padding: '7px 4px' }">
                <div :style="{ fontSize: '16px', fontWeight: 700 }">{{ cA0.toFixed(1) }}</div>
                <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">Hz measured A0</div>
              </div>
              <div :style="{ textAlign: 'center', background: 'var(--color-background-primary, #fff)', borderRadius: '6px', padding: '7px 4px' }">
                <div :style="{ fontSize: '16px', fontWeight: 700, color: '#0F6E56' }">{{ r2(calFit.alpha) }}</div>
                <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">fitted α</div>
              </div>
              <div :style="{ textAlign: 'center', background: 'var(--color-background-primary, #fff)', borderRadius: '6px', padding: '7px 4px' }">
                <div :style="{ fontSize: '16px', fontWeight: 700 }">{{ r1(calFit.leff * 1000) }}</div>
                <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">mm Leff</div>
              </div>
            </div>
            <div :style="{ fontSize: '11px', color: 'var(--color-text-secondary, #555)' }">
              {{ interpAlpha(calFit.alpha) }}
            </div>
          </div>

          <button @click="saveEntry" :style="{
            width: '100%', padding: '9px', fontSize: '13px', fontWeight: 600,
            borderRadius: '8px', border: '0.5px solid var(--color-border-secondary, #ccc)',
            background: 'var(--color-background-primary, #fff)', cursor: 'pointer'
          }">
            Save to calibration log
          </button>
          <div v-if="saveMsg" :style="{ fontSize: '11px', color: '#0F6E56', marginTop: '5px' }">{{ saveMsg }}</div>
        </div>

        <!-- Log -->
        <div :style="cardStyle">
          <div :style="{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' }">
            <div :style="{ fontSize: '13px', fontWeight: 600 }">Calibration log</div>
            <span :style="{ fontSize: '11px', color: 'var(--color-text-secondary, #666)' }">
              {{ log.length }} {{ log.length === 1 ? 'entry' : 'entries' }}
            </span>
          </div>

          <div v-if="logStats" :style="{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '10px' }">
            <div :style="{ textAlign: 'center', background: 'var(--color-background-secondary, #f5f5f5)', borderRadius: '6px', padding: '6px 4px' }">
              <div :style="{ fontSize: '14px', fontWeight: 700 }">{{ logStats.min }}</div>
              <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">α min</div>
            </div>
            <div :style="{ textAlign: 'center', background: 'var(--color-background-secondary, #f5f5f5)', borderRadius: '6px', padding: '6px 4px' }">
              <div :style="{ fontSize: '14px', fontWeight: 700 }">{{ logStats.mean }}</div>
              <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">α mean</div>
            </div>
            <div :style="{ textAlign: 'center', background: 'var(--color-background-secondary, #f5f5f5)', borderRadius: '6px', padding: '6px 4px' }">
              <div :style="{ fontSize: '14px', fontWeight: 700 }">{{ logStats.max }}</div>
              <div :style="{ fontSize: '10px', color: 'var(--color-text-secondary, #666)' }">α max</div>
            </div>
          </div>

          <div :style="{ maxHeight: '480px', overflowY: 'auto' }">
            <div v-if="log.length === 0" :style="{ textAlign: 'center', padding: '32px', color: 'var(--color-text-tertiary, #aaa)', fontSize: '12px' }">
              No entries yet. Record your first build on the left.
            </div>
            <template v-else>
              <LogEntry
                v-for="entry in [...log].reverse()"
                :key="entry.ts"
                :entry="entry"
                @use="useLogEntry"
                @delete="deleteEntry"
              />
            </template>
          </div>

          <button v-if="log.length > 0" @click="clearLog" :style="{
            marginTop: '10px', fontSize: '11px', color: '#A32D2D',
            background: 'none', border: 'none', cursor: 'pointer', padding: 0
          }">
            Clear all entries
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * SoundholeCalculator.vue
 * Guitar Soundhole Helmholtz + P:A Ratio Calculator with Builder Calibration Log
 *
 * Physics sources:
 *   Gore & Gilet, Contemporary Acoustic Guitar (2011)
 *   Williams, M. (2019), mwguitars.com.au Parts 7-8
 *   Nia et al., Royal Society Proc. A (2015)
 *   Rayleigh, Theory of Sound (1877)
 *   Ingard (1953), JASA 25(6)
 *
 * Two modes:
 *   Design — explore geometry using Gore priors or your own measured priors
 *   Calibration — tap-test a completed instrument, fit α, save to log
 *
 * α (Gore end-correction factor) is a dimensionless system property.
 * It is NOT a material constant. It must be measured per instrument.
 * Leff = top_thickness + α × r_eff
 *
 * Storage: localStorage key "soundhole_cal_log"
 */

import { ref, computed, watch, onMounted } from 'vue'

// ─── Physics constants ────────────────────────────────────────────────────────

const C = 343       // speed of sound m/s at 20°C
const I2M = 0.0254  // inches to metres
const L2M = 0.001   // litres to m³
const PA_THRESHOLD_HI = 0.10  // Williams 2019 significant gain threshold
const PA_THRESHOLD_LO = 0.08  // Williams 2019 approaching threshold

// ─── Gore published priors ────────────────────────────────────────────────────

const GORE_PRIORS = [
  { label: "Dreadnought", alpha: 1.63, vol: 24, diam: 4.00, range: "90–105 Hz", note: "Gore & Gilet measured" },
  { label: "OM / 000", alpha: 1.70, vol: 17, diam: 3.875, range: "100–115 Hz", note: "Gore & Gilet" },
  { label: "Jumbo", alpha: 1.65, vol: 28, diam: 4.25, range: "85–100 Hz", note: "Gore & Gilet" },
  { label: "Parlour", alpha: 1.75, vol: 13, diam: 3.50, range: "110–125 Hz", note: "Gore & Gilet" },
  { label: "Classical", alpha: 1.78, vol: 15, diam: 3.50, range: "115–130 Hz", note: "Gore & Gilet" },
  { label: "Rayleigh", alpha: 1.70, vol: 24, diam: 4.00, range: "varies", note: "Rigid baffle theory" },
]

// P:A table data
const paTableData = [
  ["Round R45", "—", "0.044", "baseline"],
  ["S3 rect", "150×43", "0.060", "~same"],
  ["S6 rect", "210×31", "0.074", "slight"],
  ["S6B C-slot", "300×21.7", "0.096", "~+30%"],
  ["S7 C-slot", "341×19", "0.112", "+60%"],
  ["S8 C-slot", "386×17", "0.123", "+60%"],
  ["DS1 S-slot", "2×380×17", "0.126", "+80%"],
]

// ─── Utility functions ────────────────────────────────────────────────────────

const r1 = (n: number) => Math.round(n * 10) / 10
const r2 = (n: number) => Math.round(n * 100) / 100
const r3 = (n: number) => Math.round(n * 1000) / 1000
const ri = (n: number) => Math.round(n)

function helmholtz(area: number, vol: number, leff: number) {
  if (area <= 0 || vol <= 0 || leff <= 0) return 0
  return (C / (2 * Math.PI)) * Math.sqrt(area / (vol * leff))
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

function getMainGeometry({ shape, diamIn, slotLenMm, slotWidMm, fholeLenMm, fholeWidMm, topThickMm, alpha }: GeoParams) {
  const tT = topThickMm / 1000
  const al = alpha
  let area = 0, perim = 0, leff = 0, model = "", eff = 1.0, tone = ""

  if (shape === "round" || shape === "oval") {
    const r = (diamIn * I2M) / 2
    area = Math.PI * r * r
    perim = 2 * Math.PI * r
    leff = tT + al * r
    model = "Area model (Helmholtz, round/oval)"
    eff = 1.0
    tone = "Balanced bass/treble — round baseline"
  } else if (shape === "slot" || shape === "cslot") {
    const L = slotLenMm / 1000, W = slotWidMm / 1000
    area = L * W
    perim = 2 * (L + W)
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE
    model = "Perimeter model (slot)"
    const pa = area > 0 ? perim / area : 0
    eff = pa > PA_THRESHOLD_HI ? 1.6 : pa > PA_THRESHOLD_LO ? 1.25 : 1.0
    tone = pa > PA_THRESHOLD_HI
      ? "Treble gain, bass reduction vs round (Williams 2019)"
      : "Similar to round below P:A threshold"
  } else if (shape === "dslot") {
    const L = slotLenMm / 1000, W = slotWidMm / 1000
    area = L * W * 2
    perim = 2 * (L + W) * 2
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE
    model = "Perimeter model (double slot)"
    const pa = area > 0 ? perim / area : 0
    eff = pa > PA_THRESHOLD_HI ? 1.8 : pa > PA_THRESHOLD_LO ? 1.3 : 1.0
    tone = pa > PA_THRESHOLD_HI
      ? "Strong treble gain; upper bout freed as live soundboard area"
      : "Approaching threshold — lengthen or narrow slot"
  } else if (shape === "fhole") {
    const Lf = fholeLenMm / 1000, Wf = fholeWidMm / 1000
    const pH = 2 * (Lf + Wf) * 0.88
    area = pH * Wf * 0.95 * 2
    perim = pH * 2
    const rE = Math.sqrt(area / Math.PI)
    leff = tT + al * rE * 0.78
    model = "Nia et al. perimeter model (f-hole pair)"
    eff = 1.35
    tone = "Higher treble efficiency vs equal-area round (Nia et al. 2015)"
  }

  const pa = area > 0 ? perim / area : 0
  return { area, perim, leff, model, eff, tone, pa }
}

interface FitParams {
  area: number
  topThickMm: number
  measuredA0Hz: number
  volL: number
}

function fitAlpha({ area, topThickMm, measuredA0Hz, volL }: FitParams) {
  const vol = volL * L2M
  const tT = topThickMm / 1000
  if (area <= 0 || measuredA0Hz <= 0 || vol <= 0) return null
  const fLeff = (C * C * area) / (4 * Math.PI * Math.PI * measuredA0Hz * measuredA0Hz * vol)
  const rEff = Math.sqrt(area / Math.PI)
  const fAlpha = rEff > 0 ? fLeff / rEff : 1.7
  return { leff: fLeff, alpha: fAlpha, ext: fLeff - tT }
}

function interpAlpha(alpha: number) {
  if (alpha < 1.40) return "Low — stiffer than typical or check measurement"
  if (alpha < 1.60) return "Below Gore range — heavy bracing or stiff top"
  if (alpha <= 1.80) return "Within Gore typical range (1.6–1.8)"
  if (alpha <= 1.95) return "Above Gore range — compliant top or light bracing"
  return "Unusually high — verify measurement"
}

interface GeoResult {
  area: number
  leff: number
  pa: number
  perim: number
  model: string
  eff: number
  tone: string
}

function buildCurve(geo: GeoResult, sideArea: number, sideLeff: number, volM3: number) {
  const pts = []
  for (let m = 0.7; m <= 1.3; m += 0.01) {
    const sa = sideArea * m
    const tot = geo.area + sa
    const lf = tot > 0 ? (geo.area * geo.leff + sa * sideLeff) / tot : geo.leff
    pts.push({ scale: r2(m), pct: ri(m * 100), hz: r1(helmholtz(tot, volM3, lf)) })
  }
  return pts
}

// ─── LocalStorage calibration log ────────────────────────────────────────────

const LOG_KEY = "soundhole_cal_log"

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
  try { return JSON.parse(localStorage.getItem(LOG_KEY) || "[]") }
  catch { return [] }
}

function saveLog(entries: LogEntryData[]) {
  localStorage.setItem(LOG_KEY, JSON.stringify(entries))
}

// ─── Reactive state ───────────────────────────────────────────────────────────

// Mode
const mode = ref<'design' | 'cal'>('design')

// Design inputs
const alpha = ref(1.70)
const alphaSource = ref("Gore — OM / default prior")
const volL = ref(24)
const targetHz = ref(100)
const shape = ref("round")
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
const dTab = ref('alpha')

// Calibration inputs
const cId = ref("")
const cDate = ref(new Date().toISOString().slice(0, 10))
const cBtype = ref("dread")
const cVolL = ref(24)
const cWood = ref("")
const cBrace = ref("")
const cShape = ref("round")
const cDimMm = ref(101.6)
const cTopT = ref(3.0)
const cA0 = ref(98)
const cNotes = ref("")
const saveMsg = ref("")

// Calibration log
const log = ref<LogEntryData[]>([])

onMounted(() => {
  log.value = loadLog()
})

watch(log, (newLog) => {
  saveLog(newLog)
}, { deep: true })

// ── Design calculations ─────────────────────────────────────────────────────

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

// ── Calibration calculations ────────────────────────────────────────────────

const calArea = computed(() => {
  const d = cDimMm.value / 1000
  if (cShape.value === "round") return Math.PI * (d / 2) * (d / 2)
  if (cShape.value === "slot") return d * 0.04
  if (cShape.value === "dslot") return d * 0.035 * 2
  if (cShape.value === "fhole") return d * 0.006 * 2
  return 0
})

const calFit = computed(() => fitAlpha({
  area: calArea.value,
  topThickMm: cTopT.value,
  measuredA0Hz: cA0.value,
  volL: cVolL.value
}))

// ── User priors from log ────────────────────────────────────────────────────

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

// ── Handlers ────────────────────────────────────────────────────────────────

function applyGore(prior: typeof GORE_PRIORS[0]) {
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
  setTimeout(() => { saveMsg.value = "" }, 3000)
}

function deleteEntry(ts: number) {
  log.value = log.value.filter(e => e.ts !== ts)
}

function clearLog() {
  if (window.confirm("Clear all calibration entries?")) {
    log.value = []
  }
}

function handleBodyTypeChange(e: Event) {
  const target = e.target as HTMLSelectElement
  const p = GORE_PRIORS.find(g => g.vol === parseFloat(target.value))
  if (p) {
    volL.value = p.vol
    diamIn.value = p.diam
  } else {
    volL.value = parseFloat(target.value)
  }
}

function handleCalBodyTypeChange() {
  const p = GORE_PRIORS.find(g => g.label.toLowerCase().includes(cBtype.value))
  if (p) cVolL.value = p.vol
}

// ── Derived display strings ─────────────────────────────────────────────────

const paLabel = computed(() =>
  geo.value.pa > PA_THRESHOLD_HI ? "above threshold"
    : geo.value.pa > PA_THRESHOLD_LO ? "approaching 0.10" : "below threshold"
)

const verdictText = computed(() => {
  let v = combHz.value < 85 ? "Very low A0 — warm, loose bass."
    : combHz.value < 95 ? "Low A0 — rich bass, large-body character."
    : combHz.value <= 110 ? "Typical dreadnought/OM zone — balanced voicing."
    : combHz.value <= 120 ? "Moderate-high A0 — tighter, quicker response."
    : "High A0 — lean low end, typical parlour or classical."
  if (geo.value.pa > PA_THRESHOLD_HI) v += " High P:A slot: +60–80% radiated power vs round (Williams 2019)."
  v += ` α = ${alpha.value.toFixed(2)} (${alphaSource.value.slice(0, 40)}).`
  return v
})

// ── Shared styles ───────────────────────────────────────────────────────────

const cardStyle = {
  background: 'var(--color-background-primary, #fff)',
  border: '0.5px solid var(--color-border-tertiary, #ddd)',
  borderRadius: '12px',
  padding: '14px 16px'
}

const tabStyle = (active: boolean) => ({
  fontSize: '12px',
  padding: '4px 10px',
  border: 'none',
  cursor: 'pointer',
  borderRadius: '5px 5px 0 0',
  background: active ? 'var(--color-background-secondary, #f0f0f0)' : 'none',
  color: active ? 'var(--color-text-primary, #111)' : 'var(--color-text-secondary, #666)',
  fontWeight: active ? 600 : 400
})

const modeBtn = (active: boolean) => ({
  flex: 1,
  padding: '9px',
  border: '0.5px solid var(--color-border-secondary, #ccc)',
  borderRadius: '8px',
  fontSize: '13px',
  fontWeight: 600,
  cursor: 'pointer',
  background: active ? 'var(--color-background-primary, #fff)' : 'var(--color-background-secondary, #f5f5f5)',
  color: active ? 'var(--color-text-primary, #111)' : 'var(--color-text-secondary, #666)'
})

const priorBadge = (color: { background: string; color: string }) => ({
  fontSize: '10px',
  padding: '3px 8px',
  borderRadius: '5px',
  fontWeight: 600,
  cursor: 'pointer',
  border: 'none',
  ...color
})

const priNote = {
  fontSize: '11px',
  color: 'var(--color-text-secondary, #555)',
  background: 'var(--color-background-secondary, #f5f5f5)',
  padding: '8px 10px',
  borderRadius: '6px',
  borderLeft: '3px solid #185FA5',
  lineHeight: 1.5,
  marginBottom: '10px'
}

const fieldGroup = { marginBottom: '9px' }
const fieldLabel = { display: 'block', fontSize: '11px', color: 'var(--color-text-secondary, #555)', marginBottom: '3px' }
const textInput = {
  fontSize: '12px',
  padding: '5px 8px',
  border: '0.5px solid var(--color-border-secondary, #ccc)',
  borderRadius: '6px',
  width: '100%',
  background: 'var(--color-background-primary, #fff)',
  color: 'var(--color-text-primary, #111)'
}
</script>

<script lang="ts">
// ─── Sub-components (inline) ───────────────────────────────────────────────────

import { defineComponent, h, PropType } from 'vue'

const MetricCard = defineComponent({
  name: 'MetricCard',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    sub: { type: String, default: '' },
    accent: { type: String, default: undefined }
  },
  setup(props) {
    return () => h('div', {
      style: {
        background: 'var(--color-background-secondary, #f5f5f5)',
        borderRadius: '8px',
        padding: '10px 13px'
      }
    }, [
      h('div', { style: { fontSize: '11px', color: 'var(--color-text-secondary, #666)', marginBottom: '3px' } }, props.label),
      h('div', { style: { fontSize: '20px', fontWeight: 600, color: props.accent || 'inherit' } }, props.value),
      props.sub && h('div', { style: { fontSize: '10px', color: 'var(--color-text-tertiary, #999)', marginTop: '2px' } }, props.sub)
    ])
  }
})

const SliderRow = defineComponent({
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
  setup(props, { emit }) {
    return () => h('div', {
      style: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }
    }, [
      h('label', {
        for: props.id,
        style: { fontSize: '12px', color: 'var(--color-text-secondary, #555)', minWidth: '148px' }
      }, props.label),
      h('input', {
        type: 'range',
        id: props.id,
        min: props.min,
        max: props.max,
        step: props.step,
        value: props.value,
        onInput: (e: Event) => emit('update', parseFloat((e.target as HTMLInputElement).value)),
        style: { flex: 1 }
      }),
      h('span', {
        style: { fontSize: '12px', fontWeight: 600, minWidth: '64px', textAlign: 'right' }
      }, props.display)
    ])
  }
})

const InfoRow = defineComponent({
  name: 'InfoRow',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    mono: { type: Boolean, default: false }
  },
  setup(props) {
    return () => h('div', {
      style: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '12px',
        padding: '4px 0',
        borderBottom: '0.5px solid var(--color-border-tertiary, #e0e0e0)'
      }
    }, [
      h('span', { style: { color: 'var(--color-text-secondary, #555)' } }, props.label),
      h('span', { style: { fontFamily: props.mono ? 'monospace' : 'inherit', fontWeight: props.mono ? 600 : 400 } }, props.value)
    ])
  }
})

const PAGauge = defineComponent({
  name: 'PAGauge',
  props: {
    pa: { type: Number, required: true }
  },
  setup(props) {
    return () => {
      const PA_THRESHOLD_HI = 0.10
      const PA_THRESHOLD_LO = 0.08
      const pct = Math.min(100, props.pa / 0.13 * 100)
      const color = props.pa > PA_THRESHOLD_HI ? '#0F6E56' : props.pa > PA_THRESHOLD_LO ? '#BA7517' : '#888780'
      const label = props.pa > PA_THRESHOLD_HI ? 'above threshold' : props.pa > PA_THRESHOLD_LO ? 'approaching 0.10' : 'below threshold'

      return h('div', {}, [
        h('div', {
          style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }
        }, [
          h('span', { style: { fontSize: '13px', fontWeight: 600 } }, 'P:A efficiency'),
          h('span', {
            style: {
              fontSize: '10px',
              padding: '2px 7px',
              borderRadius: '5px',
              fontWeight: 600,
              background: props.pa > PA_THRESHOLD_HI ? '#E1F5EE' : props.pa > PA_THRESHOLD_LO ? '#FAEEDA' : '#F1EFE8',
              color
            }
          }, label)
        ]),
        h('div', {
          style: { height: '7px', background: 'var(--color-background-secondary, #eee)', borderRadius: '4px', overflow: 'hidden' }
        }, [
          h('div', {
            style: { width: `${pct}%`, height: '100%', background: color, borderRadius: '4px', transition: 'width 0.3s' }
          })
        ]),
        h('div', {
          style: { display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#999', marginTop: '3px' }
        }, [
          h('span', {}, '0'),
          h('span', { style: { color: '#BA7517' } }, '0.08'),
          h('span', { style: { color: '#0F6E56', fontWeight: 700 } }, '0.10'),
          h('span', {}, '0.13')
        ]),
        h('div', {
          style: { fontSize: '11px', color: 'var(--color-text-secondary, #555)', marginTop: '6px', lineHeight: 1.5 }
        }, props.pa > PA_THRESHOLD_HI
          ? 'Above 0.10: Williams 2019 measured +60% (single slot) to +80% (double slot) vs equal-area round. Gains mainly in 165–330 Hz band.'
          : props.pa > PA_THRESHOLD_LO
            ? 'Approaching threshold. Lengthen or narrow the slot to push P:A above 0.10.'
            : 'Below 0.08: perimeter effect not dominant. Little efficiency advantage over round.')
      ])
    }
  }
})

const CurveChart = defineComponent({
  name: 'CurveChart',
  props: {
    data: { type: Array as PropType<{ pct: number; hz: number }[]>, required: true },
    target: { type: Number, required: true }
  },
  setup(props) {
    return () => {
      // Simple SVG chart since recharts is not available in Vue
      const width = 300
      const height = 130
      const padding = { top: 10, right: 10, bottom: 25, left: 40 }
      const chartW = width - padding.left - padding.right
      const chartH = height - padding.top - padding.bottom

      const hzValues = props.data.map(d => d.hz)
      const minHz = Math.min(...hzValues, props.target) - 5
      const maxHz = Math.max(...hzValues, props.target) + 5

      const xScale = (pct: number) => padding.left + ((pct - 70) / 60) * chartW
      const yScale = (hz: number) => padding.top + chartH - ((hz - minHz) / (maxHz - minHz)) * chartH

      const pathD = props.data.map((d, i) =>
        `${i === 0 ? 'M' : 'L'} ${xScale(d.pct)} ${yScale(d.hz)}`
      ).join(' ')

      return h('svg', {
        width: '100%',
        height: height,
        viewBox: `0 0 ${width} ${height}`,
        style: { fontFamily: 'system-ui' }
      }, [
        // Grid lines
        ...([70, 85, 100, 115, 130].map(pct =>
          h('line', {
            x1: xScale(pct),
            y1: padding.top,
            x2: xScale(pct),
            y2: padding.top + chartH,
            stroke: '#eee',
            'stroke-dasharray': '3 3'
          })
        )),
        // Target reference line
        props.target > 0 && h('line', {
          x1: padding.left,
          y1: yScale(props.target),
          x2: padding.left + chartW,
          y2: yScale(props.target),
          stroke: '#BA7517',
          'stroke-dasharray': '5 4'
        }),
        // Data line
        h('path', {
          d: pathD,
          fill: 'none',
          stroke: '#0F6E56',
          'stroke-width': 2
        }),
        // X axis labels
        ...([70, 100, 130].map(pct =>
          h('text', {
            x: xScale(pct),
            y: height - 5,
            'text-anchor': 'middle',
            'font-size': 10,
            fill: '#666'
          }, `${pct}%`)
        )),
        // Y axis labels
        h('text', {
          x: padding.left - 5,
          y: yScale(minHz),
          'text-anchor': 'end',
          'font-size': 10,
          fill: '#666'
        }, Math.round(minHz).toString()),
        h('text', {
          x: padding.left - 5,
          y: yScale(maxHz),
          'text-anchor': 'end',
          'font-size': 10,
          fill: '#666'
        }, Math.round(maxHz).toString())
      ])
    }
  }
})

interface LogEntryDataLocal {
  id: string
  date: string
  btype: string
  wood?: string
  brace?: string
  a0: number
  leff: number
  shape: string
  alpha: number
  notes?: string
  ts: number
}

const LogEntry = defineComponent({
  name: 'LogEntry',
  props: {
    entry: { type: Object as PropType<LogEntryDataLocal>, required: true }
  },
  emits: ['use', 'delete'],
  setup(props, { emit }) {
    return () => h('div', {
      style: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        padding: '8px 10px',
        borderBottom: '0.5px solid var(--color-border-tertiary, #eee)',
        fontSize: '12px'
      }
    }, [
      h('div', {}, [
        h('div', { style: { fontWeight: 600 } }, props.entry.id),
        h('div', {
          style: { color: 'var(--color-text-secondary, #666)', fontSize: '11px', marginTop: '1px' }
        }, `${props.entry.date} · ${props.entry.btype} · ${props.entry.wood || '—'} · ${props.entry.brace || '—'}`),
        h('div', {
          style: { color: 'var(--color-text-secondary, #666)', fontSize: '11px' }
        }, `A0 = ${props.entry.a0} Hz · Leff = ${props.entry.leff} mm · ${props.entry.shape}`),
        props.entry.notes && h('div', {
          style: { color: 'var(--color-text-tertiary, #999)', fontSize: '11px', marginTop: '2px' }
        }, props.entry.notes)
      ]),
      h('div', { style: { textAlign: 'right', flexShrink: 0, marginLeft: '12px' } }, [
        h('div', { style: { fontSize: '16px', fontWeight: 700, color: '#0F6E56' } }, `α ${props.entry.alpha}`),
        h('button', {
          onClick: () => emit('use', props.entry),
          style: {
            fontSize: '10px',
            marginTop: '3px',
            padding: '2px 7px',
            border: '0.5px solid var(--color-border-secondary, #ccc)',
            borderRadius: '4px',
            background: 'none',
            cursor: 'pointer',
            color: '#185FA5',
            display: 'block'
          }
        }, 'use in design'),
        h('button', {
          onClick: () => emit('delete', props.entry.ts),
          style: {
            fontSize: '10px',
            marginTop: '2px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            color: 'var(--color-text-tertiary, #aaa)',
            padding: 0
          }
        }, 'delete')
      ])
    ])
  }
})

export default {
  components: {
    MetricCard,
    SliderRow,
    InfoRow,
    PAGauge,
    CurveChart,
    LogEntry
  }
}
</script>

<style scoped>
.soundhole-calculator {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
