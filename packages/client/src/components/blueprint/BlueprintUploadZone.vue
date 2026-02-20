<template>
  <div
    class="upload-zone"
    :class="{ 'drag-over': isDragOver }"
    @drop.prevent="handleDrop"
    @dragover.prevent="isDragOver = true"
    @dragleave="isDragOver = false"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.png,.jpg,.jpeg"
      style="display: none"
      @change="handleFileSelect"
    >

    <div class="upload-prompt">
      <svg
        class="upload-icon"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
      <p class="upload-text">
        <strong>Drop blueprint here</strong> or <button
          class="browse-btn"
          @click="fileInput?.click()"
        >
          browse
        </button>
      </p>
      <p class="upload-hint">
        Supports PDF, PNG, JPG (max 20MB)
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Emits
const emit = defineEmits<{
  'file-selected': [file: File]
  'error': [message: string]
}>()

// Local state
const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)

// Handlers
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    validateAndEmit(target.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    validateAndEmit(event.dataTransfer.files[0])
  }
}

function validateAndEmit(file: File) {
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    emit('error', `Unsupported file type: ${file.type}. Use PDF, PNG, or JPG.`)
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    emit('error', 'File too large. Maximum size: 20MB')
    return
  }

  emit('file-selected', file)
}
</script>

<style scoped>
.upload-zone {
  border: 3px dashed #d1d5db;
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  background: #f9fafb;
  transition: all 0.3s;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone.drag-over {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.upload-text {
  font-size: 1.125rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.browse-btn {
  color: #3b82f6;
  text-decoration: underline;
  background: none;
  border: none;
  cursor: pointer;
  font-size: inherit;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.875rem;
}
</style>
