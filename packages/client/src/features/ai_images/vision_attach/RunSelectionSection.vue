<script setup lang="ts">
/**
 * RunSelectionSection - Run dropdown selector with search and create
 * Extracted from VisionAttachToRunWidget.vue
 */

defineProps<{
  runs: Array<{
    run_id: string
    event_type?: string
  }>
  selectedRunId: string | null
  runSearch: string
  runsHasMore: boolean
  isLoadingRuns: boolean
  styles: Record<string, string>
}>()

const emit = defineEmits<{
  'update:selectedRunId': [value: string | null]
  'update:runSearch': [value: string]
  'load-runs': []
  'load-more-runs': []
  'create-run': []
}>()
</script>

<template>
  <section :class="styles.section">
    <div :class="styles.stepHeader">
      <h4>3. Select Run</h4>
      <button
        :class="styles.btn"
        type="button"
        :disabled="isLoadingRuns"
        @click="emit('load-runs')"
      >
        Refresh
      </button>
    </div>

    <!-- Search + Create row -->
    <div :class="styles.runTools">
      <input
        :value="runSearch"
        :class="styles.runSearchInput"
        placeholder="Search runs (id / event_type)…"
        :disabled="isLoadingRuns"
        @input="emit('update:runSearch', ($event.target as HTMLInputElement).value)"
        @keydown.enter.prevent="emit('load-runs')"
      >
      <button
        :class="styles.btn"
        type="button"
        :disabled="isLoadingRuns"
        @click="emit('load-runs')"
      >
        Search
      </button>
      <button
        :class="styles.btnPrimary"
        type="button"
        :disabled="isLoadingRuns"
        @click="emit('create-run')"
      >
        + Create Run
      </button>
    </div>

    <!-- Empty state message -->
    <div
      v-if="runs.length === 0 && !isLoadingRuns"
      :class="styles.emptyHint"
    >
      No runs available.
      <div :class="styles.hintTip">
        Tip: click <strong>+ Create Run</strong> to start a <code>vision_image_review</code> run.
      </div>
    </div>

    <!-- Run dropdown selector -->
    <div
      v-else-if="runs.length > 0"
      :class="styles.runSelector"
    >
      <label :class="styles.formLabel">Recent runs</label>
      <select
        :value="selectedRunId"
        :class="styles.runSelect"
        @change="emit('update:selectedRunId', ($event.target as HTMLSelectElement).value || null)"
      >
        <option
          :value="null"
          disabled
        >
          Select a run...
        </option>
        <option
          v-for="run in runs"
          :key="run.run_id"
          :value="run.run_id"
        >
          {{ run.run_id.slice(0, 16) }}... {{ run.event_type ? `• ${run.event_type}` : "" }}
        </option>
      </select>

      <div :class="styles.runPickerFooter">
        <button
          v-if="runsHasMore"
          :class="styles.btn"
          type="button"
          :disabled="isLoadingRuns"
          @click="emit('load-more-runs')"
        >
          Load more
        </button>
        <div
          v-else
          :class="styles.runsCount"
        >
          Showing {{ runs.length }} run(s)
        </div>
      </div>
    </div>
  </section>
</template>
