<template>
  <div class="export-panel">
    <h3>Post-Processor Selection</h3>

    <div class="post-selector">
      <label>Select Post-Processor</label>
      <select
        :value="selectedPostId"
        @change="$emit('update:selectedPostId', ($event.target as HTMLSelectElement).value)"
      >
        <option
          v-for="post in availablePosts"
          :key="post.id"
          :value="post.id"
        >
          {{ post.name || post.id }}
        </option>
      </select>
    </div>

    <div class="post-mode-selector">
      <label>Export Mode</label>
      <select
        :value="postMode"
        @change="$emit('update:postMode', ($event.target as HTMLSelectElement).value)"
      >
        <option value="standard">
          Standard (Full G-code)
        </option>
        <option value="dry_run">
          Dry Run (Rapid only)
        </option>
      </select>
    </div>

    <button
      class="btn-primary"
      :disabled="exportRunning || !selectedPostId"
      @click="$emit('export')"
    >
      {{ exportRunning ? 'Exporting...' : '📤 Export G-code' }}
    </button>

    <p
      v-if="exportedFilename"
      class="success-message"
    >
      ✅ Exported: {{ exportedFilename }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Post {
  id: string
  name?: string
}

defineProps<{
  selectedPostId: string
  postMode: string
  availablePosts: Post[]
  exportRunning: boolean
  exportedFilename: string | null
}>()

defineEmits<{
  'update:selectedPostId': [value: string]
  'update:postMode': [value: string]
  'export': []
}>()
</script>

<style scoped>
.export-panel {
  padding: 1.5rem;
}

.export-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.post-selector,
.post-mode-selector {
  margin-bottom: 1rem;
}

.post-selector label,
.post-mode-selector label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.post-selector select,
.post-mode-selector select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.success-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>
