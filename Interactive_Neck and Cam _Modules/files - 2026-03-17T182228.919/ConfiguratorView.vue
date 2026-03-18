<script setup lang="ts">
/**
 * ConfiguratorView.vue — Customer Configurator
 *
 * Public-facing, permission-bounded version of the workspace.
 * Customer can:
 *   1. Pick a headstock model
 *   2. Choose a wood species (visual grain preview only)
 *   3. Place one inlay element (no DXF, no CAM, no parametric)
 *   4. Enter their name + optional note
 *   5. Submit → creates a variant with status 'queued' in the ERP
 *
 * What is deliberately absent:
 *   - DXF / SVG export
 *   - CAM spec (truss rod, pitch, tool paths)
 *   - Parametric shape controls
 *   - Neck suite
 *   - Import path
 *   - Variant library browser
 *   - Undo / history
 */

import { ref, watch, onMounted, computed } from 'vue'
import Konva from 'konva'
import { useKonvaCanvas }    from '@/composables/useKonvaCanvas'
import { useWoodGrain, WOOD_SPECIES } from '@/composables/useWoodGrain'
import { useVariantStore }   from '@/stores/variants'
import { HS_MODELS, MM }     from '@/assets/data/headstockData'
import type { InlayType }    from '@/types/headstock'
import {
  drawBackground,
  drawHeadstock,
  createInlayGroup,
} from '@/composables/useHeadstock'

const emit = defineEmits<{ toast: [msg: string] }>()

// ── Composables ───────────────────────────────────────────────────────────────
const grain        = useWoodGrain()
const variantStore = useVariantStore()

// ── Canvas ────────────────────────────────────────────────────────────────────
const containerRef = ref<HTMLElement | null>(null)
const canvas       = useKonvaCanvas(containerRef)

let bgLayer: Konva.Layer
let hsLayer: Konva.Layer
let inlayLayer: Konva.Layer

// ── Customer state ────────────────────────────────────────────────────────────
const modelKey       = ref<keyof typeof HS_MODELS>('Les Paul')
const placedInlay    = ref<{ id: string; type: InlayType; node: Konva.Group } | null>(null)
const selectedInlay  = ref<Konva.Group | null>(null)
const selIndicator   = ref<Konva.Rect | null>(null)

// Order form
const customerName  = ref('')
const customerNote  = ref('')
const quantity      = ref(1)
const submitting    = ref(false)
const submitted     = ref(false)
const orderId       = ref('')

// Step tracker: 0=model, 1=wood, 2=inlay, 3=review
const step = ref(0)

// ── HS_MODELS filtered to customer-facing selection ───────────────────────────
// Only the five clean production models — no Custom
const CUSTOMER_MODELS = Object.keys(HS_MODELS).filter(
  k => k !== 'Custom'
) as (keyof typeof HS_MODELS)[]

// ── Wood species list ─────────────────────────────────────────────────────────
const SPECIES_LIST = Object.keys(WOOD_SPECIES)

// Inlay palette — customer gets a curated 6
const INLAY_OPTS: { type: InlayType; label: string; desc: string }[] = [
  { type: 'dot',     label: 'Dot',     desc: 'Classic position marker' },
  { type: 'diamond', label: 'Diamond', desc: 'Vintage style' },
  { type: 'block',   label: 'Block',   desc: 'Jazz / archtop' },
  { type: 'crown',   label: 'Crown',   desc: 'Gibson signature' },
  { type: 'oval',    label: 'Oval',    desc: 'Subtle organic' },
  { type: 'star',    label: 'Star',    desc: 'Bold decorative' },
]

// ── Canvas setup ──────────────────────────────────────────────────────────────
onMounted(() => {
  bgLayer    = canvas.addLayer()
  hsLayer    = canvas.addLayer()
  inlayLayer = canvas.addLayer()

  canvas.stage.value?.on('click', e => {
    if ([bgLayer, hsLayer].includes(e.target.getLayer() as Konva.Layer)) deselect()
  })

  redraw()
})

watch([modelKey], redraw)
watch([() => grain.speciesKey.value], redrawGrain)

function currentHS() {
  return HS_MODELS[modelKey.value]
}

function redraw() {
  if (!bgLayer) return
  drawBackground(bgLayer, canvas, false)
  redrawGrain()
}

function redrawGrain() {
  if (!hsLayer) return
  drawHeadstock(hsLayer, null, canvas, currentHS(), false, false)
  // Re-apply grain texture over the headstock fill
  if (grain.speciesKey.value && hsLayer.children) {
    const pathNode = hsLayer.findOne('Path') as Konva.Path | null
    if (pathNode) {
      const sc = canvas.SC.value
      grain.applyToPath(pathNode, hsLayer, canvas.OX.value, canvas.OY.value, sc)
    }
  }
  hsLayer.draw()
}

// ── Inlay placement ───────────────────────────────────────────────────────────
function placeInlay(type: InlayType) {
  // Customer gets exactly one inlay — clear any previous
  if (placedInlay.value) {
    inlayLayer.findOne(`#${placedInlay.value.id}`)?.destroy()
    inlayLayer.draw()
    placedInlay.value = null
  }
  deselect()

  const hs = currentHS()
  const cx = canvas.p2cx(hs.cx)
  const cy = canvas.p2cy(hs.nutY - 60)

  const layer = createInlayGroup(
    type, cx, cy, inlayLayer, canvas,
    false,  // no CL snap in configurator
    true,   // boundary lock on — keeps inlay inside headstock
    hs,
    (g, sel) => doSelect(g, sel),
    () => {},  // no history
  )

  placedInlay.value = { id: layer.id, type, node: layer.node }
  inlayLayer.draw()
  step.value = Math.max(step.value, 2)
}

function doSelect(g: Konva.Group, sel: Konva.Rect) {
  if (selIndicator.value) selIndicator.value.visible(false)
  selIndicator.value = sel; sel.visible(true); inlayLayer.draw()
  selectedInlay.value = g
}

function deselect() {
  if (selIndicator.value) { selIndicator.value.visible(false); inlayLayer.draw() }
  selIndicator.value = null; selectedInlay.value = null
}

function removeInlay() {
  if (!placedInlay.value) return
  deselect()
  inlayLayer.findOne(`#${placedInlay.value.id}`)?.destroy()
  inlayLayer.draw()
  placedInlay.value = null
}

// ── Derived order summary ─────────────────────────────────────────────────────
const orderSummary = computed(() => ({
  model:   modelKey.value,
  wood:    grain.speciesKey.value || 'Unselected',
  inlay:   placedInlay.value?.type ?? 'None',
  qty:     quantity.value,
}))

// ── Submit to order queue ─────────────────────────────────────────────────────
async function submitOrder() {
  if (!customerName.value.trim()) {
    emit('toast', 'Please enter your name before submitting')
    return
  }
  submitting.value = true

  // Build the headstock snapshot payload
  const payload = {
    modelKey:  modelKey.value,
    woodSpec:  grain.speciesKey.value,
    inlay:     placedInlay.value?.type ?? null,
    quantity:  quantity.value,
    source:    'configurator',
  }

  const note = [
    customerNote.value.trim(),
    `Model: ${modelKey.value}`,
    `Wood: ${grain.speciesKey.value || 'unspecified'}`,
    `Inlay: ${placedInlay.value?.type ?? 'none'}`,
  ].filter(Boolean).join('\n')

  const variant = variantStore.createVariant(
    `${customerName.value.trim()} — ${modelKey.value}`,
    payload,
    null,  // no neck payload from configurator
    note,
  )

  // Advance immediately to queued (customer orders skip draft)
  variantStore.setStatus(variant.id, 'queued')
  variantStore.updateVariant(variant.id, {
    quantity: quantity.value,
    orderId:  `CFG-${variant.id.slice(0, 6).toUpperCase()}`,
  })

  orderId.value = variantStore.variants.find(v => v.id === variant.id)?.orderId ?? variant.id
  submitting.value = false
  submitted.value  = true
  emit('toast', `Order ${orderId.value} submitted — check the Workspace Variants panel`)
}

function resetConfigurator() {
  submitted.value    = false
  customerName.value = ''
  customerNote.value = ''
  quantity.value     = 1
  orderId.value      = ''
  step.value         = 0
  removeInlay()
}
</script>

<template>
  <div class="cfg-layout" @keydown.escape="deselect" tabindex="0">

    <!-- Left: step-by-step configurator panel -->
    <aside class="cfg-left">

      <!-- Header -->
      <div class="cfg-header">
        <div class="cfg-brand">Production<em>Shop</em></div>
        <div class="cfg-sub">Custom Headstock Configurator</div>
      </div>

      <!-- Step progress -->
      <div class="cfg-steps">
        <div v-for="(lbl, i) in ['Model','Wood','Inlay','Order']" :key="i"
          class="cfg-step" :class="{ done: step > i, active: step === i }"
          @click="step = i">
          <div class="step-dot">{{ step > i ? '✓' : i + 1 }}</div>
          <div class="step-lbl">{{ lbl }}</div>
        </div>
      </div>

      <!-- Step 0: Model selection -->
      <div v-show="step === 0" class="step-body">
        <div class="step-title">Choose a headstock model</div>
        <div class="model-grid">
          <div v-for="name in CUSTOMER_MODELS" :key="name"
            class="model-card" :class="{ on: modelKey === name }"
            @click="modelKey = name; step = 1">
            <div class="model-swatch" :style="{ background: HS_MODELS[name].col }"></div>
            <div class="model-name">{{ name }}</div>
          </div>
        </div>
        <button class="cfg-next" @click="step = 1">Next →</button>
      </div>

      <!-- Step 1: Wood species -->
      <div v-show="step === 1" class="step-body">
        <div class="step-title">Choose a wood species</div>
        <div class="wood-grid">
          <div v-for="sp in SPECIES_LIST" :key="sp"
            class="wood-card" :class="{ on: grain.speciesKey.value === sp }"
            @click="grain.setSpecies(sp); step = 2">
            <div class="wood-swatch" :style="{
              background: `rgb(${WOOD_SPECIES[sp].base.join(',')})`,
              borderLeft: `4px solid rgb(${WOOD_SPECIES[sp].dark.join(',')})`,
            }"></div>
            <div class="wood-name">{{ sp }}</div>
            <div class="wood-sub">{{ sp === 'Maple' ? 'Bright, tight grain' :
              sp === 'Mahogany' ? 'Warm, open grain' :
              sp === 'Rosewood' ? 'Dark, rich grain' :
              sp === 'Walnut' ? 'Medium, wavy grain' :
              sp === 'Ebony' ? 'Near-black, dense' :
              'Curly, exotic' }}</div>
          </div>
        </div>
        <div class="step-nav">
          <button class="cfg-back" @click="step = 0">← Back</button>
          <button class="cfg-next" @click="step = 2">Next →</button>
        </div>
      </div>

      <!-- Step 2: Inlay selection -->
      <div v-show="step === 2" class="step-body">
        <div class="step-title">Add an inlay</div>
        <div class="step-hint">Click an inlay type to place it on the headstock.<br>Drag to reposition. One inlay per order.</div>
        <div class="inlay-grid">
          <div v-for="opt in INLAY_OPTS" :key="opt.type"
            class="inlay-card"
            :class="{ on: placedInlay?.type === opt.type }"
            @click="placeInlay(opt.type)">
            <div class="inlay-icon">
              <svg viewBox="0 0 20 20" width="20" height="20">
                <circle v-if="opt.type === 'dot'"     cx="10" cy="10" r="5" fill="currentColor"/>
                <polygon v-if="opt.type === 'diamond'" points="10,3 17,10 10,17 3,10" fill="currentColor"/>
                <rect    v-if="opt.type === 'block'"   x="3" y="6" width="14" height="8" rx="1" fill="currentColor"/>
                <polygon v-if="opt.type === 'crown'"  points="10,3 6,8 3,6 5,14 15,14 17,6 14,8" fill="currentColor"/>
                <ellipse v-if="opt.type === 'oval'"   cx="10" cy="10" rx="7" ry="4" fill="currentColor"/>
                <polygon v-if="opt.type === 'star'"   points="10,2 12.4,7.6 18.5,7.6 13.8,11.5 15.6,17.5 10,13.8 4.4,17.5 6.2,11.5 1.5,7.6 7.6,7.6" fill="currentColor"/>
              </svg>
            </div>
            <div class="inlay-name">{{ opt.label }}</div>
            <div class="inlay-desc">{{ opt.desc }}</div>
          </div>
        </div>

        <!-- Placed inlay controls -->
        <div v-if="placedInlay" class="placed-controls">
          <div class="placed-badge">{{ placedInlay.type }} placed</div>
          <div class="placed-actions">
            <template v-if="selectedInlay">
              <button class="cfg-btn-sm"
                @click="selectedInlay?.scaleX(selectedInlay.scaleX() * 1.1); inlayLayer?.draw()">＋</button>
              <button class="cfg-btn-sm"
                @click="selectedInlay?.scaleX(Math.max(0.2, selectedInlay.scaleX() * 0.9)); inlayLayer?.draw()">−</button>
              <button class="cfg-btn-sm"
                @click="selectedInlay?.rotation((selectedInlay.rotation() + 15) % 360); inlayLayer?.draw()">↻</button>
            </template>
            <button class="cfg-btn-sm danger" @click="removeInlay">✕ Remove</button>
          </div>
        </div>

        <div class="step-hint" style="margin-top:6px">No inlay is also fine — skip to review.</div>
        <div class="step-nav">
          <button class="cfg-back" @click="step = 1">← Back</button>
          <button class="cfg-next" @click="step = 3">Review →</button>
        </div>
      </div>

      <!-- Step 3: Order review + submit -->
      <div v-show="step === 3" class="step-body">

        <!-- Success state -->
        <template v-if="submitted">
          <div class="submit-success">
            <div class="success-icon">✓</div>
            <div class="success-title">Order submitted!</div>
            <div class="success-id">Reference: <strong>{{ orderId }}</strong></div>
            <div class="success-sub">
              Your order has been added to the production queue.<br>
              The shop will be in touch to confirm details.
            </div>
            <button class="cfg-next" style="margin-top:14px" @click="resetConfigurator">
              Start another
            </button>
          </div>
        </template>

        <template v-else>
          <div class="step-title">Review &amp; submit</div>

          <!-- Summary card -->
          <div class="summary-card">
            <div class="summary-row">
              <span class="sum-k">Model</span>
              <span class="sum-v">{{ orderSummary.model }}</span>
            </div>
            <div class="summary-row">
              <span class="sum-k">Wood</span>
              <span class="sum-v">{{ orderSummary.wood }}</span>
            </div>
            <div class="summary-row">
              <span class="sum-k">Inlay</span>
              <span class="sum-v">{{ orderSummary.inlay }}</span>
            </div>
            <div class="summary-row">
              <span class="sum-k">Quantity</span>
              <span class="sum-v">
                <input class="qty-input" type="number" min="1" max="99" v-model.number="quantity" />
              </span>
            </div>
          </div>

          <!-- Customer details -->
          <div class="order-form">
            <label class="field-label">Your name *</label>
            <input class="field-input" v-model="customerName"
              placeholder="Full name" @keydown.enter="step === 3 && submitOrder()" />

            <label class="field-label" style="margin-top:8px">Notes (optional)</label>
            <textarea class="field-input" v-model="customerNote" rows="2"
              placeholder="Finish preference, special requests…" />
          </div>

          <!-- Error hint -->
          <div v-if="!customerName.trim()" class="form-hint">
            ↑ Name required to submit
          </div>

          <div class="step-nav">
            <button class="cfg-back" @click="step = 2">← Back</button>
            <button class="cfg-submit"
              :disabled="submitting || !customerName.trim()"
              @click="submitOrder">
              {{ submitting ? 'Submitting…' : 'Submit order →' }}
            </button>
          </div>
        </template>
      </div>

    </aside>

    <!-- Canvas -->
    <div class="cfg-canvas" ref="containerRef"
      @click="deselect"
      @keydown.delete="removeInlay" tabindex="0">
    </div>

    <!-- Right: mini spec panel (read-only summary visible at all times) -->
    <aside class="cfg-right">
      <div class="spec-section">
        <div class="spec-lbl">Selection</div>
        <div class="spec-row">
          <span class="spec-k">Model</span>
          <span class="spec-v">{{ modelKey }}</span>
        </div>
        <div class="spec-row">
          <span class="spec-k">Wood</span>
          <span class="spec-v">{{ grain.speciesKey.value || '—' }}</span>
        </div>
        <div class="spec-row">
          <span class="spec-k">Inlay</span>
          <span class="spec-v">{{ placedInlay?.type ?? '—' }}</span>
        </div>
        <div class="spec-row">
          <span class="spec-k">Nut width</span>
          <span class="spec-v">{{ (currentHS().nw * MM).toFixed(1) }} mm</span>
        </div>
      </div>

      <!-- Wood colour swatch preview -->
      <div v-if="grain.speciesKey.value" class="spec-section">
        <div class="spec-lbl">Wood grain</div>
        <div class="wood-preview-swatch"
          :style="{ background: `rgb(${WOOD_SPECIES[grain.speciesKey.value].base.join(',')})` }">
          <div class="grain-lines" v-for="i in 8" :key="i"
            :style="{
              top: `${i * 12}%`,
              opacity: 0.15 + (i % 3) * 0.08,
              background: `rgb(${WOOD_SPECIES[grain.speciesKey.value].dark.join(',')})`,
            }">
          </div>
        </div>
        <div class="spec-row" style="margin-top:4px">
          <span class="spec-k">Species</span>
          <span class="spec-v">{{ grain.speciesKey.value }}</span>
        </div>
      </div>

      <!-- Quick model switcher shortcut -->
      <div class="spec-section">
        <div class="spec-lbl">Quick switch</div>
        <div v-for="name in CUSTOMER_MODELS" :key="name"
          class="qs-item" :class="{ on: modelKey === name }"
          @click="modelKey = name; redraw()">
          <span class="qs-dot" :style="{ background: HS_MODELS[name].col }"></span>
          {{ name }}
        </div>
      </div>
    </aside>

  </div>
</template>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.cfg-layout {
  display: grid;
  grid-template-columns: 280px 1fr 200px;
  height: 100%;
  background: var(--w0);
  outline: none;
}
.cfg-left {
  background: var(--w1);
  border-right: 1px solid var(--w3);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.cfg-canvas { overflow: hidden; cursor: default; }
.cfg-right {
  background: var(--w1);
  border-left: 1px solid var(--w3);
  overflow-y: auto;
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
.cfg-header { padding: 14px 16px 10px; border-bottom: 1px solid var(--w3); }
.cfg-brand  { font-family: var(--serif); font-size: 15px; font-style: italic; color: var(--v1); }
.cfg-brand em { color: var(--br2); font-style: normal; }
.cfg-sub    { font-size: 8px; color: var(--dim3); letter-spacing: 1.2px; text-transform: uppercase; margin-top: 2px; }

/* ── Step progress ──────────────────────────────────────────────────────────── */
.cfg-steps {
  display: flex;
  border-bottom: 1px solid var(--w3);
  padding: 0;
}
.cfg-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px 6px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .12s;
  gap: 3px;
}
.cfg-step:hover { background: var(--w2); }
.cfg-step.active { border-bottom-color: var(--br); }
.cfg-step.done { opacity: .7; }
.step-dot {
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--w3); display: flex; align-items: center; justify-content: center;
  font-size: 8px; color: var(--dim); font-family: var(--mono);
}
.cfg-step.active .step-dot { background: var(--br); color: #0f0d0a; }
.cfg-step.done  .step-dot  { background: var(--green2); color: #0f0d0a; }
.step-lbl { font-size: 8px; letter-spacing: .8px; text-transform: uppercase; color: var(--dim3); }
.cfg-step.active .step-lbl { color: var(--br2); }

/* ── Step body ──────────────────────────────────────────────────────────────── */
.step-body  { padding: 14px 14px 12px; flex: 1; display: flex; flex-direction: column; gap: 10px; }
.step-title { font-family: var(--serif); font-size: 12px; font-style: italic; color: var(--v1); }
.step-hint  { font-size: 8px; color: var(--dim3); line-height: 1.6; }
.step-nav   { display: flex; gap: 6px; margin-top: auto; padding-top: 8px; }

/* ── Model grid ─────────────────────────────────────────────────────────────── */
.model-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.model-card {
  padding: 8px; background: var(--w2); border: 1px solid var(--w3); border-radius: 4px;
  cursor: pointer; transition: all .1s; display: flex; align-items: center; gap: 7px;
}
.model-card:hover { border-color: var(--w4); }
.model-card.on    { border-color: var(--br); background: rgba(184,150,46,.07); }
.model-swatch { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.model-name   { font-size: 9px; color: var(--dim); }
.model-card.on .model-name { color: var(--br2); }

/* ── Wood grid ──────────────────────────────────────────────────────────────── */
.wood-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.wood-card {
  padding: 0; overflow: hidden; background: var(--w2); border: 1px solid var(--w3);
  border-radius: 4px; cursor: pointer; transition: all .1s;
}
.wood-card:hover { border-color: var(--w4); }
.wood-card.on    { border-color: var(--br); box-shadow: 0 0 0 1px var(--br3); }
.wood-swatch { height: 20px; width: 100%; }
.wood-name { font-size: 9px; color: var(--dim); padding: 3px 7px 0; }
.wood-sub  { font-size: 7px; color: var(--dim3); padding: 0 7px 5px; line-height: 1.4; }
.wood-card.on .wood-name { color: var(--br2); }

/* ── Inlay grid ─────────────────────────────────────────────────────────────── */
.inlay-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.inlay-card {
  padding: 8px 7px; background: var(--w2); border: 1px solid var(--w3); border-radius: 4px;
  cursor: pointer; transition: all .1s; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.inlay-card:hover { border-color: var(--w4); }
.inlay-card.on    { border-color: var(--br); background: rgba(184,150,46,.07); }
.inlay-icon { color: var(--dim); }
.inlay-card.on .inlay-icon { color: var(--br2); }
.inlay-name { font-size: 9px; color: var(--dim); }
.inlay-card.on .inlay-name { color: var(--br2); }
.inlay-desc { font-size: 7px; color: var(--dim3); text-align: center; line-height: 1.4; }

/* ── Placed inlay controls ──────────────────────────────────────────────────── */
.placed-controls {
  background: rgba(184,150,46,.06);
  border: 1px solid var(--br3); border-radius: 3px;
  padding: 7px 9px; display: flex; align-items: center; justify-content: space-between;
}
.placed-badge { font-size: 8px; color: var(--br2); letter-spacing: .4px; text-transform: capitalize; }
.placed-actions { display: flex; gap: 3px; }
.cfg-btn-sm {
  padding: 2px 6px; background: var(--w2); border: 1px solid var(--w3); border-radius: 2px;
  font-size: 10px; color: var(--dim); cursor: pointer; transition: all .1s; font-family: var(--mono);
}
.cfg-btn-sm:hover { border-color: var(--br3); color: var(--v1); }
.cfg-btn-sm.danger:hover { border-color: var(--red); color: var(--red); }

/* ── Order form ─────────────────────────────────────────────────────────────── */
.summary-card {
  background: var(--w2); border: 1px solid var(--w3); border-radius: 4px; padding: 9px 11px;
}
.summary-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
.summary-row:last-child { margin-bottom: 0; }
.sum-k { font-size: 9px; color: var(--dim); }
.sum-v { font-size: 9px; color: var(--v1); }
.qty-input {
  width: 40px; text-align: center; background: var(--w1); border: 1px solid var(--w3);
  border-radius: 2px; color: var(--v1); font-size: 9px; font-family: var(--mono); padding: 1px 4px;
}
.order-form { display: flex; flex-direction: column; }
.field-label { font-size: 8px; color: var(--dim3); letter-spacing: .8px; text-transform: uppercase; margin-bottom: 3px; }
.field-input {
  padding: 6px 8px; background: var(--w2); border: 1px solid var(--w3); border-radius: 3px;
  color: var(--v1); font-size: 10px; font-family: var(--mono); outline: none; resize: none;
}
.field-input:focus { border-color: var(--br3); }
.form-hint { font-size: 8px; color: var(--amber); }

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.cfg-next {
  flex: 1; padding: 8px 0; background: none; border: 1px solid var(--br3); border-radius: 3px;
  color: var(--br2); font-family: var(--mono); font-size: 9px; letter-spacing: .5px;
  text-transform: uppercase; cursor: pointer; transition: all .12s;
}
.cfg-next:hover { background: var(--br); color: #0f0d0a; }
.cfg-back {
  padding: 8px 12px; background: none; border: 1px solid var(--w3); border-radius: 3px;
  color: var(--dim); font-family: var(--mono); font-size: 9px; cursor: pointer; transition: all .12s;
}
.cfg-back:hover { border-color: var(--w4); color: var(--v1); }
.cfg-submit {
  flex: 1; padding: 8px 0; background: var(--br); border: 1px solid var(--br);
  border-radius: 3px; color: #0f0d0a; font-family: var(--mono); font-size: 9px;
  letter-spacing: .5px; text-transform: uppercase; cursor: pointer; transition: all .12s;
  font-weight: 600;
}
.cfg-submit:hover:not(:disabled) { background: var(--br2); }
.cfg-submit:disabled { opacity: .4; cursor: not-allowed; }

/* ── Success state ──────────────────────────────────────────────────────────── */
.submit-success {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 20px 0; text-align: center;
}
.success-icon  { font-size: 32px; color: var(--green2); }
.success-title { font-family: var(--serif); font-size: 14px; font-style: italic; color: var(--v1); }
.success-id    { font-size: 9px; color: var(--br2); font-family: var(--mono); }
.success-id strong { letter-spacing: .8px; }
.success-sub   { font-size: 9px; color: var(--dim3); line-height: 1.7; }

/* ── Right spec panel ───────────────────────────────────────────────────────── */
.spec-section { padding: 10px 12px; border-bottom: 1px solid var(--w3); }
.spec-lbl     { font-size: 7px; letter-spacing: 1.4px; text-transform: uppercase; color: var(--br3); margin-bottom: 6px; }
.spec-row     { display: flex; justify-content: space-between; margin-bottom: 3px; }
.spec-k       { font-size: 9px; color: var(--dim); }
.spec-v       { font-size: 9px; color: var(--v1); }

.wood-preview-swatch {
  height: 40px; border-radius: 3px; position: relative; overflow: hidden;
  border: 1px solid var(--w3);
}
.grain-lines {
  position: absolute; left: 0; right: 0; height: 1px;
}

/* Quick switch */
.qs-item {
  display: flex; align-items: center; gap: 6px; padding: 5px 0;
  font-size: 9px; color: var(--dim); cursor: pointer; transition: color .1s;
  border-bottom: 1px solid var(--w2);
}
.qs-item:hover { color: var(--v1); }
.qs-item.on    { color: var(--br2); }
.qs-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
</style>
