<template>
  <div class="cam-settings-view">
    <div class="header">
      <h2>CAM Settings Hub</h2>
      <p>Export and import complete CAM configuration (machines, posts, presets)</p>
    </div>

    <!-- Summary Cards -->
    <div class="summary-grid">
      <div class="summary-card">
        <h3>{{ summary.machines_count || 0 }}</h3>
        <p>Machines</p>
      </div>
      <div class="summary-card">
        <h3>{{ summary.posts_count || 0 }}</h3>
        <p>Posts</p>
      </div>
      <div class="summary-card">
        <h3>{{ summary.pipeline_presets_count || 0 }}</h3>
        <p>Presets</p>
      </div>
    </div>

    <!-- Export Section -->
    <div class="section">
      <h3>Export Settings</h3>
      <p>Export all CAM configuration to JSON file for backup or sharing.</p>
      <button
        :disabled="loading"
        @click="exportSettings"
      >
        {{ loading ? 'Exporting...' : 'Export to JSON' }}
      </button>
    </div>

    <!-- Import Section -->
    <div class="section">
      <h3>Import Settings</h3>
      <p>Restore CAM configuration from JSON backup file.</p>
      
      <div class="import-controls">
        <input 
          ref="fileInput" 
          type="file" 
          accept=".json" 
          @change="handleFileSelect"
        >
        
        <label class="checkbox-label">
          <input
            v-model="overwriteMode"
            type="checkbox"
          >
          Overwrite existing (if unchecked, skip duplicates)
        </label>
        
        <button
          :disabled="!selectedFile || loading"
          @click="importSettings"
        >
          {{ loading ? 'Importing...' : 'Import from JSON' }}
        </button>
      </div>

      <!-- Import Results -->
      <div
        v-if="importResults"
        class="import-results"
      >
        <h4>Import Results</h4>
        <div class="result-grid">
          <div class="result-item">
            <strong>Imported:</strong>
            <ul>
              <li>Machines: {{ importResults.imported.machines || 0 }}</li>
              <li>Posts: {{ importResults.imported.posts || 0 }}</li>
              <li>Presets: {{ importResults.imported.pipeline_presets || 0 }}</li>
            </ul>
          </div>
          <div class="result-item">
            <strong>Skipped:</strong>
            <ul>
              <li>Machines: {{ importResults.skipped.machines || 0 }}</li>
              <li>Posts: {{ importResults.skipped.posts || 0 }}</li>
              <li>Presets: {{ importResults.skipped.pipeline_presets || 0 }}</li>
            </ul>
          </div>
        </div>
        
        <div
          v-if="importResults.errors && importResults.errors.length > 0"
          class="errors"
        >
          <strong>Errors ({{ importResults.errors.length }}):</strong>
          <ul>
            <li
              v-for="(err, idx) in importResults.errors"
              :key="idx"
            >
              {{ err }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted } from 'vue'

const summary = ref<{machines_count: number; posts_count: number; pipeline_presets_count: number}>({
  machines_count: 0,
  posts_count: 0,
  pipeline_presets_count: 0
})

const loading = ref(false)
const selectedFile = ref<File | null>(null)
const overwriteMode = ref(false)
const importResults = ref<any>(null)
const fileInput = ref<HTMLInputElement | null>(null)

// Load summary on mount
onMounted(async () => {
  try {
    const res = await api('/api/cam/settings/summary')
    if (res.ok) {
      summary.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load summary:', err)
  }
})

async function exportSettings() {
  loading.value = true
  try {
    const res = await api('/api/cam/settings/export')
    if (!res.ok) throw new Error('Export failed')
    
    const data = await res.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cam_settings_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    alert('Export failed: ' + err)
  } finally {
    loading.value = false
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
  importResults.value = null
}

async function importSettings() {
  if (!selectedFile.value) return
  
  loading.value = true
  importResults.value = null
  
  try {
    const text = await selectedFile.value.text()
    const payload = JSON.parse(text)
    
    const res = await api(`/api/cam/settings/import?overwrite=${overwriteMode.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    if (!res.ok) throw new Error('Import failed')
    
    importResults.value = await res.json()
    
    // Reload summary
    const summaryRes = await api('/api/cam/settings/summary')
    if (summaryRes.ok) {
      summary.value = await summaryRes.json()
    }
    
    // Reset file input
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    
  } catch (err) {
    alert('Import failed: ' + err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.cam-settings-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h2 {
  margin: 0 0 10px 0;
}

.header p {
  margin: 0;
  color: #666;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.summary-card {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.summary-card h3 {
  margin: 0 0 10px 0;
  font-size: 32px;
  color: #333;
}

.summary-card p {
  margin: 0;
  color: #666;
}

.section {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.section h3 {
  margin: 0 0 10px 0;
}

.section p {
  margin: 0 0 20px 0;
  color: #666;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.import-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.import-results {
  margin-top: 20px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin: 15px 0;
}

.result-item ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.errors {
  margin-top: 15px;
  padding: 10px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
}

.errors ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
