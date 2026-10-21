<script setup lang="ts">
import { computed, reactive, ref } from "vue"
import {
  HEADSTOCK_OUTLINE_DEFAULTS,
  HEADSTOCK_OUTLINE_PARAMETER_DEFS,
  buildHeadstockOutlinePath,
  validateHeadstockOutlineParams,
  type HeadstockOutlineParams,
  type HeadstockTipStyle,
} from "@/design-utilities/lutherie/headstock/parametricOutline"

const TIP_OPTIONS: { id: HeadstockTipStyle; label: string }[] = [
  { id: "rounded", label: "Rounded" },
  { id: "squared", label: "Squared" },
  { id: "pointed", label: "Pointed" },
  { id: "scroll", label: "Scroll" },
]

const tipStyle = ref<HeadstockTipStyle>("rounded")
const draft = reactive<Record<keyof HeadstockOutlineParams, string>>({
  nutWidth: String(HEADSTOCK_OUTLINE_DEFAULTS.nutWidth),
  length: String(HEADSTOCK_OUTLINE_DEFAULTS.length),
  tipWidth: String(HEADSTOCK_OUTLINE_DEFAULTS.tipWidth),
  asymmetry: String(HEADSTOCK_OUTLINE_DEFAULTS.asymmetry),
  taper: String(HEADSTOCK_OUTLINE_DEFAULTS.taper),
  waistDepth: String(HEADSTOCK_OUTLINE_DEFAULTS.waistDepth),
  waistPos: String(HEADSTOCK_OUTLINE_DEFAULTS.waistPos),
  bassShoulder: String(HEADSTOCK_OUTLINE_DEFAULTS.bassShoulder),
  trebleShoulder: String(HEADSTOCK_OUTLINE_DEFAULTS.trebleShoulder),
  tipRounding: String(HEADSTOCK_OUTLINE_DEFAULTS.tipRounding),
})

const bodyDefs = HEADSTOCK_OUTLINE_PARAMETER_DEFS.filter((def) => def.group === "BODY")
const shoulderDefs = HEADSTOCK_OUTLINE_PARAMETER_DEFS.filter((def) => def.group === "SHOULDER")

const parsed = computed<HeadstockOutlineParams>(() => {
  const params = {} as HeadstockOutlineParams
  for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
    const raw = draft[def.id].trim()
    params[def.id] = raw === "" ? Number.NaN : Number(raw)
  }
  return params
})

const validation = computed(() => validateHeadstockOutlineParams(parsed.value))

const outlinePath = computed(() => {
  if (!validation.value.valid) return ""
  return buildHeadstockOutlinePath(parsed.value, tipStyle.value)
})

function resetOutline() {
  tipStyle.value = "rounded"
  for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
    draft[def.id] = String(HEADSTOCK_OUTLINE_DEFAULTS[def.id])
  }
}
</script>

<template>
  <section
    class="parametric-outline"
    aria-labelledby="parametric-outline-title"
  >
    <header class="parametric-outline-header">
      <h2 id="parametric-outline-title">
        Parametric outline preview
      </h2>
      <p class="qualifier">
        Recovered design model
      </p>
      <p class="notice">
        Design preview only. This outline is not a manufacturing drawing.
      </p>
      <p class="notice">
        Controls use recovered model-space outline units, not millimeters.
      </p>
    </header>

    <label
      class="field"
      for="headstock-tip-style"
    >
      Tip style
      <select
        id="headstock-tip-style"
        v-model="tipStyle"
      >
        <option
          v-for="option in TIP_OPTIONS"
          :key="option.id"
          :value="option.id"
        >
          {{ option.label }}
        </option>
      </select>
    </label>

    <fieldset>
      <legend>
        BODY
      </legend>
      <label
        v-for="def in bodyDefs"
        :key="def.id"
        class="field"
        :for="`outline-${def.id}`"
      >
        {{ def.label }} (outline units)
        <input
          :id="`outline-${def.id}`"
          v-model="draft[def.id]"
          type="text"
          inputmode="decimal"
          autocomplete="off"
        >
      </label>
    </fieldset>

    <fieldset>
      <legend>
        SHOULDER
      </legend>
      <label
        v-for="def in shoulderDefs"
        :key="def.id"
        class="field"
        :for="`outline-${def.id}`"
      >
        {{ def.label }} (outline units)
        <input
          :id="`outline-${def.id}`"
          v-model="draft[def.id]"
          type="text"
          inputmode="decimal"
          autocomplete="off"
        >
      </label>
    </fieldset>

    <button
      type="button"
      @click="resetOutline"
    >
      Reset to recovered defaults
    </button>

    <p
      v-if="!validation.valid"
      class="validation"
      role="alert"
    >
      <span
        v-for="error in validation.errors"
        :key="error"
      >{{ error }}</span>
    </p>

    <svg
      viewBox="0 0 200 320"
      role="img"
      aria-label="Parametric headstock outline"
    >
      <path
        v-if="outlinePath"
        :d="outlinePath"
        fill="none"
        stroke="currentColor"
      />
    </svg>
  </section>
</template>

<style scoped>
.parametric-outline {
  margin-top: 1.5rem;
  padding: 1.5rem;
  border: 1px solid #334155;
  border-radius: 0.75rem;
  background: #111827;
  color: #e5e7eb;
}

.parametric-outline-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.qualifier,
.notice {
  margin: 0.35rem 0 0;
}

.notice {
  color: #fbbf24;
}

fieldset {
  border: 1px solid #374151;
  margin: 1rem 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

input,
select,
button {
  font: inherit;
}

svg {
  width: 12rem;
  height: auto;
  margin-top: 1rem;
  background: #0f172a;
}

.validation {
  color: #fca5a5;
}
</style>
