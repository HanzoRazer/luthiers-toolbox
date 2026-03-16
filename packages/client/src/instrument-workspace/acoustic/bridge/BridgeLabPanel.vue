<!--
  BridgeLabPanel.vue (BRIDGE-002/003/004/005)

  Bridge Lab — first bounded design workspace.
  Template for Neck Lab, Body Lab, and Bracing Lab.

  Bounded workspace contract (from PLATFORM_ARCHITECTURE.md):
    ✅ Loads project BridgeState on entry (BRIDGE-002)
    ✅ Edits local state only — never auto-commits (BRIDGE-003)
    ✅ Derives break angle from Geometry Engine API, not inline formula (BRIDGE-004)
    ✅ Uses v2 corrected break angle model — Carruth 6° empirical minimum (BRIDGE-005)
    ✅ Commits to project on explicit "Apply Bridge Geometry" action (BRIDGE-003)

  BridgeCalculatorPanel (existing) handles:
    DXF geometry export, SVG preview, preset loading from /api/cam/bridge/presets
    It is embedded as Stage 0 in BridgeLabView.vue and emits dxf-generated.

  This panel handles:
    Project-aware geometry editing (project load/save)
    Break angle derived from engine
    String tension context (reads from project when in context mode)

  Props:
    projectId — UUID of the active project. Required for project context.

  Emits:
    committed  — when bridge geometry is committed to project
    open-dxf   — request to navigate to DXF workflow (Stage 1 of BridgeLabView)
-->

<template>
  <div class="blp">

    <!-- Header -->
    <div class="blp-header">
      <div class="blp-title-row">
        <span class="blp-icon">🌉</span>
        <div>
          <h2 class="blp-title">Bridge Geometry</h2>
          <p class="blp-subtitle">Saddle placement, compensation, and string geometry</p>
        </div>
      </div>
      <div class="blp-status-row">
        <span v-if="isDirty && !isSaving" class="blp-badge blp-badge--dirty">● Unsaved</span>
        <span v-if="isSaving" class="blp-badge blp-badge--saving">Saving…</span>
        <span v-if="hasProjectBridgeState && !isDirty && !isSaving"
              class="blp-badge blp-badge--saved">✓ Committed</span>
      </div>
    </div>

    <!-- Save error -->
    <div v-if="saveError" class="blp-error">⚠️ {{ saveError }}</div>

    <!-- Two-column editing layout -->
    <div class="blp-body">

      <!-- LEFT: Saddle geometry fields -->
      <div class="blp-section">
        <div class="blp-section-title">Saddle geometry</div>

        <!-- Saddle line -->
        <div class="blp-field">
          <label class="blp-label">
            Saddle line from nut (mm)
            <span class="blp-label-hint">theoretical = scale + avg. compensation</span>
          </label>
          <input
            :value="local.saddle_line_from_nut_mm ?? ''"
            type="number" step="0.1" min="200" max="900"
            class="blp-input blp-mono"
            placeholder="e.g. 648.0"
            @input="update('saddle_line_from_nut_mm', parseFloat(($event.target as HTMLInputElement).value) || null)"
          />
          <div v-if="saddleLineLabel !== '—'" class="blp-field-display blp-mono">
            {{ saddleLineLabel }}
          </div>
          <div v-if="spec?.scale_length_mm && !hasSaddleLine" class="blp-field-hint">
            Project scale: {{ spec.scale_length_mm.toFixed(1) }} mm →
            typical saddle ~{{ (spec.scale_length_mm + 3).toFixed(1) }} mm
          </div>
        </div>

        <!-- String spread -->
        <div class="blp-field">
          <label class="blp-label">String spread at saddle (mm)
            <span class="blp-label-hint">treble E to bass E</span>
          </label>
          <input
            v-model.number="local.string_spread_mm"
            type="number" step="0.5" min="30" max="80"
            class="blp-input blp-mono"
            @input="markDirtyLocal"
          />
        </div>

        <!-- Compensation -->
        <div class="blp-field-pair">
          <div class="blp-field">
            <label class="blp-label">Comp. treble (mm)</label>
            <input v-model.number="local.compensation_treble_mm"
                   type="number" step="0.1" min="0" max="15"
                   class="blp-input blp-mono" @input="markDirtyLocal" />
          </div>
          <div class="blp-field">
            <label class="blp-label">Comp. bass (mm)</label>
            <input v-model.number="local.compensation_bass_mm"
                   type="number" step="0.1" min="0" max="15"
                   class="blp-input blp-mono" @input="markDirtyLocal" />
          </div>
        </div>

        <!-- Saddle slot -->
        <div class="blp-field-pair">
          <div class="blp-field">
            <label class="blp-label">Slot width (mm)</label>
            <input v-model.number="local.saddle_slot_width_mm"
                   type="number" step="0.1" min="1" max="10"
                   class="blp-input blp-mono" @input="markDirtyLocal" />
          </div>
          <div class="blp-field">
            <label class="blp-label">Slot depth (mm)</label>
            <input v-model.number="local.saddle_slot_depth_mm"
                   type="number" step="0.5" min="5" max="20"
                   class="blp-input blp-mono" @input="markDirtyLocal" />
          </div>
        </div>
      </div>

      <!-- RIGHT: Break angle inputs + live result -->
      <div class="blp-section">
        <div class="blp-section-title">
          Break angle geometry
          <a class="blp-doc-link" href="/docs/BRIDGE_BREAK_ANGLE_DERIVATION.md" target="_blank">
            v2 derivation ↗
          </a>
        </div>

        <!-- Saddle projection -->
        <div class="blp-field">
          <label class="blp-label">
            Saddle projection (mm)
            <span class="blp-label-hint">above bridge top surface — NOT above plate</span>
          </label>
          <input
            v-model.number="local.saddle_projection_mm"
            type="number" step="0.1" min="0.5" max="12"
            class="blp-input blp-mono"
          />
          <div v-if="local.saddle_projection_mm < 1.6" class="blp-field-warn">
            ⚠️ Below 1.6 mm (1/16") practical minimum
          </div>
        </div>

        <!-- Pin-to-saddle distance -->
        <div class="blp-field">
          <label class="blp-label">
            Pin center → saddle center (mm)
            <span class="blp-label-hint">horizontal distance</span>
          </label>
          <input
            v-model.number="local.pin_to_saddle_center_mm"
            type="number" step="0.1" min="3" max="15"
            class="blp-input blp-mono"
          />
          <div class="blp-field-hint">Martin ~5.5 mm · Gibson ~6.5 mm</div>
        </div>

        <!-- Slot offset -->
        <div class="blp-field">
          <label class="blp-label">
            Pin slot offset (mm)
            <span class="blp-label-hint">string exit point shift from slotted hole</span>
          </label>
          <input
            v-model.number="local.slot_offset_mm"
            type="number" step="0.1" min="0" max="3"
            class="blp-input blp-mono"
          />
          <div class="blp-field-hint">
            Effective distance: {{ effectiveDistanceMm.toFixed(2) }} mm
            ({{ local.pin_to_saddle_center_mm }} − {{ local.slot_offset_mm }})
          </div>
        </div>

        <!-- Live break angle result -->
        <div class="blp-angle-result" :class="`blp-angle-result--${breakAngleRating ?? 'unknown'}`">
          <div class="blp-angle-header">
            <span class="blp-angle-label">Break angle</span>
            <span v-if="isComputingAngle" class="blp-angle-computing">computing…</span>
          </div>
          <div class="blp-angle-value" :style="{ color: breakAngleColor }">
            <span v-if="breakAngleDeg !== null">
              {{ breakAngleDeg.toFixed(2) }}°
            </span>
            <span v-else class="blp-angle-empty">—</span>
          </div>
          <div class="blp-angle-rating" v-if="breakAngleRating">
            <span :style="{ color: breakAngleColor }">
              {{ ratingLabel }}
            </span>
            <span class="blp-angle-min">Minimum: 6° (Carruth empirical)</span>
          </div>
          <div v-if="breakAngleResult?.recommendation" class="blp-angle-rec">
            {{ breakAngleResult.recommendation }}
          </div>
          <div v-if="breakAngleResult?.risk_flags?.length" class="blp-angle-flags">
            <div
              v-for="flag in breakAngleResult.risk_flags"
              :key="flag.code"
              class="blp-angle-flag"
              :class="`blp-flag--${flag.severity}`"
            >
              {{ flag.message }}
            </div>
          </div>
          <div v-if="angleError" class="blp-angle-error">{{ angleError }}</div>
        </div>
      </div>
    </div>

    <!-- Action bar -->
    <div class="blp-actions">
      <button
        class="blp-btn blp-btn--primary"
        :disabled="isSaving || !isDirty"
        @click="handleApply"
      >
        <span v-if="isSaving">Saving…</span>
        <span v-else>Apply Bridge Geometry</span>
      </button>

      <button
        class="blp-btn blp-btn--ghost"
        :disabled="isSaving || !isDirty"
        @click="discardChanges"
      >
        Discard changes
      </button>

      <button
        class="blp-btn blp-btn--secondary"
        @click="$emit('open-dxf')"
      >
        DXF / CAM →
      </button>
    </div>

    <!-- Committed state summary (shown after save) -->
    <div v-if="hasProjectBridgeState && !isDirty" class="blp-committed">
      <div class="blp-committed-title">Committed to project</div>
      <div class="blp-committed-row">
        <span>Saddle line</span>
        <span class="blp-mono">{{ saddleLineLabel }}</span>
      </div>
      <div class="blp-committed-row">
        <span>String spread</span>
        <span class="blp-mono">{{ local.string_spread_mm }} mm</span>
      </div>
      <div class="blp-committed-row" v-if="breakAngleDeg !== null">
        <span>Break angle</span>
        <span class="blp-mono" :style="{ color: breakAngleColor }">
          {{ breakAngleDeg.toFixed(2) }}° — {{ ratingLabel }}
        </span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useBridgeWorkspace } from './useBridgeWorkspace'
import { useInstrumentProject } from '@/instrument-workspace/shared-state/useInstrumentProject'

const props = defineProps<{
  projectId?: string | null
}>()

const emit = defineEmits<{
  (e: 'committed'): void
  (e: 'open-dxf'): void
}>()

const { spec } = useInstrumentProject()

const {
  local, isDirty, isSaving, saveError,
  breakAngleDeg, breakAngleRating, breakAngleIsAdequate,
  breakAngleColor, breakAngleResult, isComputingAngle, angleError,
  saddleLineLabel, effectiveDistanceMm,
  hasProjectBridgeState, hasSaddleLine,
  update, markDirty,
  applyBridgeGeometry, discardChanges,
} = useBridgeWorkspace()

const ratingLabel = computed(() => {
  switch (breakAngleRating.value) {
    case 'adequate':    return 'Adequate ✓'
    case 'too_shallow': return 'Too shallow ✗'
    case 'too_steep':   return 'Too steep ⚠'
    default:            return ''
  }
})

function markDirtyLocal() {
  markDirty()
  // isDirty is reactive in workspace composable via update()
}

async function handleApply() {
  const ok = await applyBridgeGeometry()
  if (ok) emit('committed')
}
</script>

<style scoped>
.blp { display: flex; flex-direction: column; gap: 1.25rem; padding: 1.25rem; font-family: var(--font-sans, system-ui); }

/* Header */
.blp-header { display: flex; justify-content: space-between; align-items: flex-start; }
.blp-title-row { display: flex; align-items: center; gap: 0.75rem; }
.blp-icon { font-size: 1.75rem; }
.blp-title { margin: 0 0 0.2rem; font-size: 1.15rem; font-weight: 600; }
.blp-subtitle { margin: 0; font-size: 0.82rem; color: var(--color-text-secondary); }
.blp-status-row { display: flex; gap: 0.5rem; }
.blp-badge { font-size: 0.72rem; padding: 0.2rem 0.6rem; border-radius: 1rem; font-weight: 500; }
.blp-badge--dirty  { background: #FFF3CD; color: #856404; }
.blp-badge--saving { background: #E3F2FD; color: #0D47A1; }
.blp-badge--saved  { background: #D1FAE5; color: #065F46; }

.blp-error { padding: 0.5rem 0.75rem; background: var(--color-background-danger); border-radius: 0.4rem; font-size: 0.82rem; color: var(--color-text-danger); }

/* Body layout */
.blp-body { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 680px) { .blp-body { grid-template-columns: 1fr; } }

/* Section */
.blp-section { display: flex; flex-direction: column; gap: 0.85rem; }
.blp-section-title { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-tertiary); display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.4rem; border-bottom: 0.5px solid var(--color-border-tertiary); }
.blp-doc-link { font-size: 0.7rem; color: #667eea; text-decoration: none; margin-left: auto; }

/* Fields */
.blp-field { display: flex; flex-direction: column; gap: 0.2rem; }
.blp-field-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.blp-label { font-size: 0.8rem; font-weight: 500; display: flex; flex-direction: column; gap: 0.1rem; }
.blp-label-hint { font-weight: 400; font-size: 0.7rem; color: var(--color-text-tertiary); }
.blp-input { padding: 0.38rem 0.55rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.35rem; background: var(--color-background-primary); font-size: 0.875rem; width: 100%; }
.blp-input:focus { outline: 1.5px solid #667eea; }
.blp-mono { font-family: var(--font-mono, monospace); }
.blp-field-display { font-size: 0.78rem; font-family: var(--font-mono, monospace); color: var(--color-text-secondary); }
.blp-field-hint { font-size: 0.72rem; color: var(--color-text-tertiary); }
.blp-field-warn { font-size: 0.75rem; color: #D85A30; font-weight: 500; }

/* Break angle result card */
.blp-angle-result { border-radius: 0.5rem; padding: 0.9rem 1rem; background: var(--color-background-secondary); display: flex; flex-direction: column; gap: 0.35rem; }
.blp-angle-result--adequate    { border-left: 3px solid #1D9E75; }
.blp-angle-result--too_shallow { border-left: 3px solid #D85A30; }
.blp-angle-result--too_steep   { border-left: 3px solid #BA7517; }
.blp-angle-result--unknown     { border-left: 3px solid var(--color-border-secondary); }
.blp-angle-header { display: flex; justify-content: space-between; align-items: center; }
.blp-angle-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-tertiary); }
.blp-angle-computing { font-size: 0.7rem; color: var(--color-text-tertiary); animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.blp-angle-value { font-size: 2rem; font-weight: 700; font-family: var(--font-mono, monospace); line-height: 1; }
.blp-angle-empty { font-size: 1.5rem; color: var(--color-text-tertiary); }
.blp-angle-rating { display: flex; justify-content: space-between; align-items: baseline; font-size: 0.82rem; }
.blp-angle-min { font-size: 0.7rem; color: var(--color-text-tertiary); }
.blp-angle-rec { font-size: 0.78rem; color: var(--color-text-secondary); font-style: italic; }
.blp-angle-flags { display: flex; flex-direction: column; gap: 0.2rem; }
.blp-angle-flag { font-size: 0.72rem; padding: 0.2rem 0.4rem; border-radius: 0.25rem; }
.blp-flag--warning  { background: #FFF3CD; color: #856404; }
.blp-flag--critical { background: #FEE2E2; color: #991B1B; }
.blp-flag--info     { background: #EFF6FF; color: #1D4ED8; }
.blp-angle-error { font-size: 0.75rem; color: #D85A30; }

/* Actions */
.blp-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; padding-top: 0.5rem; border-top: 0.5px solid var(--color-border-tertiary); }
.blp-btn { padding: 0.45rem 1.1rem; border-radius: 0.5rem; border: none; font-family: inherit; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: background 0.15s; }
.blp-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.blp-btn--primary   { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.blp-btn--primary:hover:not(:disabled) { filter: brightness(1.1); }
.blp-btn--secondary { background: #1D9E75; color: white; }
.blp-btn--secondary:hover { background: #17846A; }
.blp-btn--ghost     { background: var(--color-background-secondary); color: var(--color-text-primary); border: 0.5px solid var(--color-border-secondary); }

/* Committed summary */
.blp-committed { background: var(--color-background-secondary); border-radius: 0.5rem; padding: 0.75rem 1rem; }
.blp-committed-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #1D9E75; margin-bottom: 0.5rem; }
.blp-committed-row { display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.12rem 0; }
</style>
