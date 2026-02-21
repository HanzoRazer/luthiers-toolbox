<template>
  <div :class="styles.inputSection">
    <h3>Your Labor Rate</h3>
    <div :class="styles.inputGroup">
      <label>Hourly Rate ($/hr)</label>
      <input
        :value="hourlyRate"
        type="number"
        step="5"
        min="10"
        max="200"
        @input="emit('update:hourlyRate', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
    <div :class="styles.ratePresets">
      <button
        :class="styles.btnPreset"
        @click="emit('update:hourlyRate', 25)"
      >
        Hobbyist ($25)
      </button>
      <button
        :class="styles.btnPreset"
        @click="emit('update:hourlyRate', 50)"
      >
        Semi-Pro ($50)
      </button>
      <button
        :class="styles.btnPreset"
        @click="emit('update:hourlyRate', 75)"
      >
        Professional ($75)
      </button>
      <button
        :class="styles.btnPreset"
        @click="emit('update:hourlyRate', 100)"
      >
        Master ($100)
      </button>
    </div>

    <h3>Project Size</h3>
    <div :class="styles.inputGroup">
      <label>Instrument Type</label>
      <select
        :value="instrumentType"
        @change="emit('update:instrumentType', ($event.target as HTMLSelectElement).value)"
      >
        <option value="full-body">
          Full Body Electric (Strat/Les Paul)
        </option>
        <option value="neck">
          Neck Only
        </option>
        <option value="acoustic">
          Acoustic Guitar
        </option>
        <option value="classical">
          Classical Guitar
        </option>
        <option value="bass">
          Bass Guitar
        </option>
        <option value="violin">
          Violin
        </option>
      </select>
    </div>

    <div :class="styles.inputGroup">
      <label>Finish Type</label>
      <select
        :value="finishType"
        @change="emit('update:finishType', ($event.target as HTMLSelectElement).value)"
      >
        <option value="varnish">
          Simple Varnish
        </option>
        <option value="french">
          French Polish
        </option>
        <option value="nitro">
          Nitrocellulose
        </option>
        <option value="poly">
          Polyurethane
        </option>
        <option value="oil">
          Oil Finish
        </option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  hourlyRate: number
  instrumentType: string
  finishType: string
}>()

const emit = defineEmits<{
  'update:hourlyRate': [value: number]
  'update:instrumentType': [value: string]
  'update:finishType': [value: string]
}>()
</script>
