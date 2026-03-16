<!--
  StiffnessIndexPanel.vue
  ========================
  The Production Shop — Woodwork Calculator / Stiffness Index

  Acoustic quality indices for tonewood selection:
    • Radiation ratio (Schelleng c/ρ) — soundboard projecting quality
    • Specific MOE (E/ρ) — stiffness per unit mass
    • Ashby plate index (E^(1/3)/ρ) — minimum weight for plate stiffness
    • Acoustic impedance (ρ×c) — energy transfer at wood joints
    • Plate mass calculator — what does this blank weigh?

  Data: 26 hardcoded primary tonewoods from luthier_tonewood_reference.json.
  Extended by GET /api/registry/tonewoods (R-8) when available.
-->

<template>
  <div class="sip">

    <!-- Header / API status -->
    <div class="sip-header">
      <div class="sip-api-status">
        <span v-if="apiLoading" class="sip-badge sip-badge--loading">Loading full database…</span>
        <span v-else-if="apiLoaded" class="sip-badge sip-badge--ok">Full database ({{ allSpecies.length }} species)</span>
        <span v-else class="sip-badge sip-badge--fallback">Built-in set ({{ allSpecies.length }} species) · <button class="sip-link" @click="loadFromApi">Load full DB</button></span>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="sip-filters">
      <div class="sip-filter-group">
        <span class="sip-label">Part</span>
        <div class="sip-pills">
          <button
            :class="['sip-pill', { 'sip-pill--on': partFilter === 'all' }]"
            @click="partFilter = 'all'"
          >All</button>
          <button
            v-for="pg in partGroups"
            :key="pg.id"
            :class="['sip-pill', { 'sip-pill--on': partFilter === pg.id }]"
            @click="partFilter = pg.id"
          >{{ pg.label }}</button>
        </div>
      </div>
      <div class="sip-filter-group" style="margin-left:auto">
        <span class="sip-label">Sort</span>
        <select v-model="sortBy" class="sip-select">
          <option value="radiation_ratio">Radiation ratio ↓</option>
          <option value="ashby">Ashby index ↓</option>
          <option value="moe">MOE ↓</option>
          <option value="density">Density ↑</option>
          <option value="name">Name A–Z</option>
        </select>
        <label class="sip-check-label">
          <input v-model="showNoMoeSpecies" type="checkbox">
          <span>Show density-only</span>
        </label>
      </div>
    </div>

    <!-- Two-column body -->
    <div class="sip-body">

      <!-- Index table -->
      <div class="sip-table-wrap">
        <table class="sip-table">
          <thead>
            <tr>
              <th>Species</th>
              <th title="Density kg/m³">ρ</th>
              <th title="Modulus of Elasticity GPa">MOE</th>
              <th title="Speed of sound m/s">c (m/s)</th>
              <th title="Radiation ratio c/ρ × 1000 — Schelleng soundboard index">c/ρ ×10³</th>
              <th title="Ashby plate stiffness index E^(1/3)/ρ">Ashby</th>
              <th title="Acoustic impedance ρ×c MRayl">Z</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="idx in filteredIndices"
              :key="idx.entry.id"
              :class="[
                'sip-row',
                { 'sip-row--selected': selectedSpeciesId === idx.entry.id },
                { 'sip-row--compare': compareId === idx.entry.id },
              ]"
              @click="selectedSpeciesId = idx.entry.id"
            >
              <td>
                <div class="sip-species-name">{{ idx.entry.name }}</div>
                <div class="sip-species-sci">{{ idx.entry.scientificName }}</div>
              </td>
              <td class="sip-mono">{{ idx.entry.densityKgM3 }}</td>
              <td class="sip-mono">
                <span v-if="idx.entry.moeGpa">{{ idx.entry.moeGpa }}</span>
                <span v-else class="sip-na">—</span>
              </td>
              <td class="sip-mono">
                <span v-if="idx.speedMs">{{ idx.speedMs }}</span>
                <span v-else class="sip-na">—</span>
              </td>
              <td class="sip-mono">
                <span
                  v-if="idx.radiationRatio"
                  :style="{ color: rrColor(idx.radiationRatio) }"
                  class="sip-val"
                >{{ idx.radiationRatio.toFixed(2) }}</span>
                <span v-else class="sip-na">—</span>
              </td>
              <td class="sip-mono">
                <span v-if="idx.ashbyIndex" class="sip-val">{{ idx.ashbyIndex.toFixed(3) }}</span>
                <span v-else class="sip-na">—</span>
              </td>
              <td class="sip-mono">
                <span v-if="idx.acousticImpedance" class="sip-val">{{ idx.acousticImpedance.toFixed(2) }}</span>
                <span v-else class="sip-na">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Side panel: detail + plate calc + compare -->
      <div class="sip-side">

        <!-- Selected species detail -->
        <div v-if="selectedEntry" class="sip-card">
          <div class="sip-card-header">
            <div>
              <div class="sip-card-name">{{ selectedEntry.name }}</div>
              <div class="sip-card-sci">{{ selectedEntry.scientificName }}</div>
            </div>
            <div class="sip-source-badge" :class="`sip-source-badge--${selectedEntry.source}`">
              {{ selectedEntry.source.toUpperCase() }}
            </div>
          </div>

          <div class="sip-tone">{{ selectedEntry.toneCharacter }}</div>

          <div class="sip-indices-grid" v-if="selectedIndices">
            <div class="sip-idx-card">
              <div class="sip-idx-label">Radiation ratio</div>
              <div
                class="sip-idx-val"
                :style="{ color: selectedIndices.radiationRatio ? rrColor(selectedIndices.radiationRatio) : 'inherit' }"
              >{{ selectedIndices.radiationRatio?.toFixed(3) ?? '—' }}</div>
              <div class="sip-idx-unit">c/ρ ×10³</div>
            </div>
            <div class="sip-idx-card">
              <div class="sip-idx-label">Ashby plate</div>
              <div class="sip-idx-val">{{ selectedIndices.ashbyIndex?.toFixed(4) ?? '—' }}</div>
              <div class="sip-idx-unit">E^(1/3)/ρ</div>
            </div>
            <div class="sip-idx-card">
              <div class="sip-idx-label">Specific MOE</div>
              <div class="sip-idx-val">{{ selectedIndices.specificMoe?.toFixed(3) ?? '—' }}</div>
              <div class="sip-idx-unit">E/ρ ×10⁶</div>
            </div>
            <div class="sip-idx-card">
              <div class="sip-idx-label">Impedance Z</div>
              <div class="sip-idx-val">{{ selectedIndices.acousticImpedance?.toFixed(3) ?? '—' }}</div>
              <div class="sip-idx-unit">MRayl</div>
            </div>
          </div>

          <div
            v-if="selectedIndices?.soundboardRating"
            class="sip-soundboard-rating"
            :class="`sip-soundboard-rating--${selectedIndices.soundboardRating.toLowerCase().replace(' ', '-')}`"
          >
            Soundboard quality: {{ selectedIndices.soundboardRating }}
          </div>

          <div class="sip-sustainability" :class="sustainabilityClass(selectedEntry.sustainability)">
            {{ selectedEntry.sustainability }}
          </div>

          <div v-if="selectedEntry.sourceNote" class="sip-source-note">
            † {{ selectedEntry.sourceNote }}
          </div>
        </div>

        <!-- Plate mass calculator -->
        <div class="sip-card">
          <div class="sip-card-label">Plate mass calculator</div>
          <div class="sip-row">
            <span class="sip-label">Species</span>
            <select v-model="selectedSpeciesId" class="sip-select sip-select--full">
              <option v-for="s in allSpecies" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div class="sip-row">
            <span class="sip-label">Thickness (mm)</span>
            <input v-model.number="thicknessMm" type="number" step="0.1" min="0.5" class="sip-input sip-mono">
          </div>
          <div class="sip-row">
            <span class="sip-label">Width (mm)</span>
            <input v-model.number="widthMm" type="number" step="1" min="10" class="sip-input sip-mono">
          </div>
          <div class="sip-row">
            <span class="sip-label">Length (mm)</span>
            <input v-model.number="lengthMm" type="number" step="1" min="10" class="sip-input sip-mono">
          </div>
          <div v-if="plateMassGrams !== null" class="sip-mass-result">
            <span class="sip-mass-val">{{ plateMassGrams.toFixed(1) }} g</span>
            <span class="sip-mass-alt">{{ (plateMassGrams / 1000).toFixed(3) }} kg · {{ (plateMassGrams / 28.35).toFixed(2) }} oz</span>
          </div>
        </div>

        <!-- Comparison -->
        <div class="sip-card">
          <div class="sip-card-label">Compare</div>
          <div class="sip-compare-row">
            <div class="sip-compare-col">
              <div class="sip-compare-header sip-compare-header--a">Selected</div>
              <div class="sip-compare-species">{{ selectedEntry?.name ?? '—' }}</div>
            </div>
            <div class="sip-compare-col">
              <div class="sip-compare-header sip-compare-header--b">Compare to</div>
              <select v-model="compareId" class="sip-select">
                <option v-for="s in allSpecies" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>

          <table class="sip-compare-table" v-if="selectedIndices && compareIndices">
            <thead>
              <tr>
                <th>Index</th>
                <th>A</th>
                <th>B</th>
                <th>Δ</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>ρ (kg/m³)</td>
                <td class="sip-mono">{{ selectedEntry?.densityKgM3 }}</td>
                <td class="sip-mono">{{ compareEntry?.densityKgM3 }}</td>
                <td class="sip-mono" :class="deltaClass(selectedEntry?.densityKgM3, compareEntry?.densityKgM3, 'lower')">
                  {{ formatDelta(selectedEntry?.densityKgM3, compareEntry?.densityKgM3) }}
                </td>
              </tr>
              <tr>
                <td>MOE (GPa)</td>
                <td class="sip-mono">{{ selectedEntry?.moeGpa ?? '—' }}</td>
                <td class="sip-mono">{{ compareEntry?.moeGpa ?? '—' }}</td>
                <td class="sip-mono" :class="deltaClass(selectedEntry?.moeGpa, compareEntry?.moeGpa, 'higher')">
                  {{ formatDelta(selectedEntry?.moeGpa, compareEntry?.moeGpa) }}
                </td>
              </tr>
              <tr>
                <td>c/ρ ×10³</td>
                <td class="sip-mono">{{ selectedIndices.radiationRatio?.toFixed(2) ?? '—' }}</td>
                <td class="sip-mono">{{ compareIndices.radiationRatio?.toFixed(2) ?? '—' }}</td>
                <td class="sip-mono" :class="deltaClass(selectedIndices.radiationRatio, compareIndices.radiationRatio, 'higher')">
                  {{ formatDelta(selectedIndices.radiationRatio, compareIndices.radiationRatio) }}
                </td>
              </tr>
              <tr>
                <td>Ashby</td>
                <td class="sip-mono">{{ selectedIndices.ashbyIndex?.toFixed(3) ?? '—' }}</td>
                <td class="sip-mono">{{ compareIndices.ashbyIndex?.toFixed(3) ?? '—' }}</td>
                <td class="sip-mono" :class="deltaClass(selectedIndices.ashbyIndex, compareIndices.ashbyIndex, 'higher')">
                  {{ formatDelta(selectedIndices.ashbyIndex, compareIndices.ashbyIndex) }}
                </td>
              </tr>
              <tr>
                <td>Z (MRayl)</td>
                <td class="sip-mono">{{ selectedIndices.acousticImpedance?.toFixed(2) ?? '—' }}</td>
                <td class="sip-mono">{{ compareIndices.acousticImpedance?.toFixed(2) ?? '—' }}</td>
                <td class="sip-mono">
                  {{ formatDelta(selectedIndices.acousticImpedance, compareIndices.acousticImpedance) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>

    <!-- Footnotes -->
    <div class="sip-footnotes">
      c/ρ = Schelleng radiation ratio (soundboard projecting quality) ·
      E^(1/3)/ρ = Ashby plate stiffness index ·
      Z = ρ×c acoustic impedance (MRayl) ·
      Data: USDA FPL GTR-282, Wood Database (E. Meier), CIRAD ·
      † species with estimated MOE (see source badge)
    </div>

  </div>
</template>

<script setup lang="ts">
import { useStiffnessIndex } from '../composables/useStiffnessIndex'

const {
  allSpecies, apiLoaded, apiLoading, loadFromApi,
  partFilter, sortBy, showNoMoeSpecies, partGroups,
  filteredIndices,
  selectedSpeciesId, thicknessMm, widthMm, lengthMm,
  selectedEntry, selectedIndices, plateMassGrams,
  compareId, compareEntry, compareIndices,
} = useStiffnessIndex()

// ============================================================================
// DISPLAY HELPERS
// ============================================================================

function rrColor(rr: number): string {
  if (rr >= 12.0) return '#1D9E75'   // excellent
  if (rr >= 10.5) return '#BA7517'   // good
  if (rr >= 9.0)  return '#D85A30'   // acceptable
  return '#E24B4A'                    // below average
}

function sustainabilityClass(s: string): string {
  const l = s.toLowerCase()
  if (l.includes('cites appx i') || l.includes('endangered') || l.includes('pre-ban'))
    return 'sip-sustain--critical'
  if (l.includes('cites') || l.includes('restricted') || l.includes('vulnerable') || l.includes('declining'))
    return 'sip-sustain--warning'
  return 'sip-sustain--ok'
}

function formatDelta(a: number | null | undefined, b: number | null | undefined): string {
  if (a == null || b == null) return '—'
  const d = ((b - a) / Math.abs(a)) * 100
  return `${d > 0 ? '+' : ''}${d.toFixed(1)}%`
}

function deltaClass(
  a: number | null | undefined,
  b: number | null | undefined,
  prefer: 'higher' | 'lower'
): string {
  if (a == null || b == null) return ''
  const better = prefer === 'higher' ? b > a : b < a
  return better ? 'sip-delta--better' : b === a ? '' : 'sip-delta--worse'
}
</script>

<style scoped>
.sip { font-family: var(--font-sans, system-ui); padding: 4px 0; }

.sip-header { display: flex; align-items: center; margin-bottom: 8px; }
.sip-badge { font-size: 11px; padding: 2px 8px; border-radius: var(--border-radius-md); }
.sip-badge--loading { background: var(--color-background-warning); color: var(--color-text-warning); }
.sip-badge--ok { background: #E1F5EE; color: #085041; }
.sip-badge--fallback { background: var(--color-background-secondary); color: var(--color-text-tertiary); }
.sip-link { background: none; border: none; color: #1D9E75; cursor: pointer; font-size: 11px; text-decoration: underline; font-family: inherit; padding: 0; }

.sip-filters { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.sip-filter-group { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sip-label { font-size: 11px; color: var(--color-text-secondary); white-space: nowrap; }
.sip-pills { display: flex; gap: 4px; flex-wrap: wrap; }
.sip-pill { font-size: 11px; padding: 2px 8px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: transparent; color: var(--color-text-secondary); cursor: pointer; font-family: inherit; }
.sip-pill--on { background: var(--color-background-tertiary); color: var(--color-text-primary); border-color: var(--color-border-secondary); }
.sip-select { font-size: 11px; padding: 2px 5px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); font-family: inherit; }
.sip-select--full { width: 100%; }
.sip-check-label { font-size: 11px; color: var(--color-text-secondary); display: flex; align-items: center; gap: 4px; cursor: pointer; }

.sip-body { display: grid; grid-template-columns: 1fr 260px; gap: 12px; align-items: start; }
@media (max-width: 720px) { .sip-body { grid-template-columns: 1fr; } }

.sip-table-wrap { overflow-x: auto; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); }
.sip-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.sip-table th { font-size: 9px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; padding: 5px 7px; background: var(--color-background-secondary); border-bottom: 0.5px solid var(--color-border-tertiary); white-space: nowrap; cursor: default; }
.sip-table td { padding: 4px 7px; border-bottom: 0.5px solid var(--color-border-tertiary); vertical-align: middle; }
.sip-row:last-child td { border-bottom: none; }
.sip-row { cursor: pointer; }
.sip-row:hover td { background: var(--color-background-secondary); }
.sip-row--selected td { background: var(--color-background-warning) !important; }
.sip-row--compare td { outline: 1px solid #1D9E75; }
.sip-species-name { font-size: 12px; font-weight: 500; }
.sip-species-sci { font-size: 10px; color: var(--color-text-tertiary); font-style: italic; }
.sip-mono { font-family: var(--font-mono, monospace); font-size: 11px; }
.sip-val { font-weight: 500; }
.sip-na { color: var(--color-text-tertiary); }

.sip-side { display: flex; flex-direction: column; gap: 8px; }
.sip-card { background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 10px 12px; }
.sip-card-label { font-size: 10px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }
.sip-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.sip-card-name { font-size: 14px; font-weight: 500; }
.sip-card-sci { font-size: 10px; color: var(--color-text-tertiary); font-style: italic; }
.sip-tone { font-size: 11px; color: var(--color-text-secondary); margin-bottom: 8px; line-height: 1.5; }
.sip-indices-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-bottom: 6px; }
.sip-idx-card { background: var(--color-background-primary); border-radius: var(--border-radius-md); padding: 6px 8px; }
.sip-idx-label { font-size: 9px; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.03em; }
.sip-idx-val { font-family: var(--font-mono, monospace); font-size: 15px; font-weight: 500; margin: 1px 0; }
.sip-idx-unit { font-size: 9px; color: var(--color-text-tertiary); }
.sip-soundboard-rating { font-size: 11px; font-weight: 500; padding: 3px 8px; border-radius: var(--border-radius-md); margin-bottom: 5px; display: inline-block; }
.sip-soundboard-rating--excellent { background: #E1F5EE; color: #085041; }
.sip-soundboard-rating--good { background: var(--color-background-warning); color: var(--color-text-warning); }
.sip-soundboard-rating--acceptable { background: #FAECE7; color: #4A1B0C; }
.sip-soundboard-rating--below-average { background: var(--color-background-danger); color: var(--color-text-danger); }
.sip-sustainability { font-size: 10px; padding: 3px 7px; border-radius: var(--border-radius-md); margin-top: 4px; line-height: 1.4; }
.sip-sustain--ok { background: #E1F5EE; color: #085041; }
.sip-sustain--warning { background: var(--color-background-warning); color: var(--color-text-warning); }
.sip-sustain--critical { background: var(--color-background-danger); color: var(--color-text-danger); }
.sip-source-badge { font-size: 9px; padding: 1px 6px; border-radius: var(--border-radius-md); font-weight: 500; }
.sip-source-badge--repo { background: var(--color-background-info); color: var(--color-text-info); }
.sip-source-badge--fpl { background: #E1F5EE; color: #085041; }
.sip-source-badge--wdb { background: var(--color-background-warning); color: var(--color-text-warning); }
.sip-source-badge--estimated { background: var(--color-background-tertiary); color: var(--color-text-tertiary); }
.sip-source-note { font-size: 10px; color: var(--color-text-tertiary); margin-top: 5px; line-height: 1.5; font-style: italic; }
.sip-row { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
.sip-input { font-size: 11px; padding: 2px 5px; border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-primary); color: var(--color-text-primary); width: 80px; font-family: var(--font-mono, monospace); }
.sip-mass-result { margin-top: 6px; padding: 8px; background: var(--color-background-primary); border-radius: var(--border-radius-md); }
.sip-mass-val { font-family: var(--font-mono, monospace); font-size: 18px; font-weight: 500; color: #BA7517; display: block; }
.sip-mass-alt { font-size: 11px; color: var(--color-text-secondary); font-family: var(--font-mono, monospace); }
.sip-compare-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
.sip-compare-col { display: flex; flex-direction: column; gap: 3px; }
.sip-compare-header { font-size: 9px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; padding: 1px 5px; border-radius: var(--border-radius-md); }
.sip-compare-header--a { background: var(--color-background-warning); color: var(--color-text-warning); }
.sip-compare-header--b { background: #E1F5EE; color: #085041; }
.sip-compare-species { font-size: 11px; font-weight: 500; }
.sip-compare-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.sip-compare-table th { font-size: 9px; font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; padding: 3px 5px; border-bottom: 0.5px solid var(--color-border-tertiary); }
.sip-compare-table td { padding: 3px 5px; border-bottom: 0.5px solid var(--color-border-tertiary); font-family: var(--font-mono, monospace); }
.sip-compare-table tr:last-child td { border-bottom: none; }
.sip-delta--better { color: #1D9E75; }
.sip-delta--worse { color: #D85A30; }
.sip-footnotes { margin-top: 8px; font-size: 10px; color: var(--color-text-tertiary); font-family: var(--font-mono, monospace); line-height: 1.8; }
</style>
