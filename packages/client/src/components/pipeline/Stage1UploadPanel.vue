<template>
  <div class="stage-panel">
    <h2>📁 Stage 1: Upload DXF Blueprint</h2>

    <div
      class="drop-zone"
      :class="{ dragging: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div v-if="!modelValue">
        <div class="upload-icon">
          📄
        </div>
        <p>Drag & drop DXF file here</p>
        <p class="or-text">
          or
        </p>
        <label class="upload-button">
          Browse Files
          <input
            type="file"
            accept=".dxf"
            hidden
            @change="handleFileSelect"
          >
        </label>
      </div>
      <div
        v-else
        class="file-info"
      >
        <div class="file-icon">
          ✅
        </div>
        <div>
          <h3>{{ modelValue.name }}</h3>
          <p>{{ formatFileSize(modelValue.size) }}</p>
        </div>
        <button
          class="clear-button"
          @click="clearFile"
        >
          ✕
        </button>
      </div>
    </div>

    <div
      v-if="modelValue"
      class="action-buttons"
    >
      <button
        class="btn btn-primary"
        :disabled="loading"
        @click="emit('submit')"
      >
        {{ loading ? '⏳ Checking...' : '🔍 Run Preflight Check' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Props
interface Props {
  modelValue: File | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [file: File | null]
  'submit': []
  'clear': []
}>()

// Local state
const isDragging = ref(false)

// Handlers
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    emit('update:modelValue', target.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0]
    if (file.name.toLowerCase().endsWith('.dxf')) {
      emit('update:modelValue', file)
    } else {
      alert('Please upload a .dxf file')
    }
  }
}

function clearFile() {
  emit('update:modelValue', null)
  emit('clear')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.stage-panel {
  animation: fadeIn 0.3s;
}

.drop-zone {
  border: 3px dashed #ccc;
  border-radius: 12px;
  padding: 60px;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
}

.drop-zone.dragging {
  border-color: #2196F3;
  background: #e3f2fd;
}

.upload-icon {
  font-size: 4em;
  margin-bottom: 20px;
}

.or-text {
  color: #999;
  margin: 20px 0;
}

.upload-button {
  display: inline-block;
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #1976D2;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.file-icon {
  font-size: 3em;
}

.clear-button {
  margin-left: auto;
  padding: 10px 15px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2em;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin: 30px 0;
  justify-content: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
