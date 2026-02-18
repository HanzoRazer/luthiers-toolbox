<script setup lang="ts">
/**
 * DxfUploadZone - Drag and drop zone for DXF file upload
 * Extracted from DxfToGcodeView.vue
 */
import { ref } from 'vue'

const props = defineProps<{
  file: File | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:file': [file: File | null]
  'error': [message: string]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    setFile(target.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    setFile(event.dataTransfer.files[0])
  }
}

function setFile(file: File) {
  if (!file.name.toLowerCase().endsWith('.dxf')) {
    emit('error', 'Please select a DXF file')
    return
  }
  emit('update:file', file)
}

function clearFile() {
  emit('update:file', null)
  if (fileInput.value) fileInput.value.value = ''
}

function openFileBrowser() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="upload-zone"
    :class="{ 'drag-over': isDragOver, 'has-file': !!file, 'disabled': disabled }"
    @drop.prevent="handleDrop"
    @dragover.prevent="isDragOver = true"
    @dragleave="isDragOver = false"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".dxf"
      style="display: none"
      :disabled="disabled"
      @change="handleFileSelect"
    >

    <div v-if="!file" class="upload-prompt">
      <p>
        <strong>Drop DXF here</strong> or
        <button class="link-btn" :disabled="disabled" @click="openFileBrowser">
          browse
        </button>
      </p>
      <p class="hint">DXF R12/R2000 format</p>
    </div>

    <div v-else class="file-info">
      <span class="filename">{{ file.name }}</span>
      <span class="filesize">({{ (file.size / 1024).toFixed(1) }} KB)</span>
      <button class="clear-btn" :disabled="disabled" @click="clearFile">×</button>
    </div>
  </div>
</template>

<style scoped>
.upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  transition: all 0.2s;
}

.upload-zone.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.upload-zone.drag-over {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-zone.has-file {
  border-color: #10b981;
  background: #f0fdf4;
}

.upload-prompt p {
  margin: 0.5rem 0;
}

.link-btn {
  background: none;
  border: none;
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit;
}

.link-btn:disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

.hint {
  color: #9ca3af;
  font-size: 0.875rem;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.filename {
  font-weight: 600;
  color: #059669;
}

.filesize {
  color: #6b7280;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 0.25rem;
}

.clear-btn:hover:not(:disabled) {
  color: #dc2626;
}

.clear-btn:disabled {
  cursor: not-allowed;
}
</style>
