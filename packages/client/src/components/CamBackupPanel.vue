<template>
  <div class="cam-backup-panel">
    <div class="header">
      <h3>CAM Backups</h3>
      <button
        :disabled="loading"
        @click="snapshotNow"
      >
        {{ loading ? 'Creating...' : '📸 Snapshot Now' }}
      </button>
    </div>

    <p class="subtitle">
      Automatic daily backups (14-day retention)
    </p>

    <!-- Backup List -->
    <div
      v-if="backups.length > 0"
      class="backup-list"
    >
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Size</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="backup in backups"
            :key="backup.name"
          >
            <td>{{ formatDate(backup.name) }}</td>
            <td>{{ formatSize(backup.size_bytes) }}</td>
            <td>
              <a
                :href="`/api/cam/backup/download/${backup.name}`"
                download
              >
                💾 Download
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-else-if="!loading"
      class="empty-state"
    >
      <p>No backups found. Click "Snapshot Now" to create your first backup.</p>
    </div>

    <div
      v-if="loading"
      class="loading"
    >
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Backup {
  name: string
  size_bytes: number
}

const backups = ref<Backup[]>([])
const loading = ref(false)

onMounted(loadBackups)

async function loadBackups() {
  loading.value = true
  try {
    const res = await fetch('/api/cam/backup/list')
    if (res.ok) {
      const data = await res.json()
      backups.value = data.backups || []
    }
  } catch (err) {
    console.error('Failed to load backups:', err)
  } finally {
    loading.value = false
  }
}

async function snapshotNow() {
  loading.value = true
  try {
    const res = await fetch('/api/cam/backup/snapshot', { method: 'POST' })
    if (!res.ok) throw new Error('Snapshot failed')
    
    const data = await res.json()
    alert(`Backup created: ${data.filename}`)
    
    // Reload list
    await loadBackups()
  } catch (err) {
    alert('Snapshot failed: ' + err)
  } finally {
    loading.value = false
  }
}

function formatDate(name: string): string {
  // name format: YYYY-MM-DD.json
  const date = name.replace('.json', '')
  return date
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<style scoped>
.cam-backup-panel {
  padding: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.header h3 {
  margin: 0;
}

.subtitle {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

button {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #218838;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.backup-list table {
  width: 100%;
  border-collapse: collapse;
}

.backup-list th,
.backup-list td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.backup-list th {
  background: #f5f5f5;
  font-weight: 600;
}

.backup-list a {
  color: #007bff;
  text-decoration: none;
}

.backup-list a:hover {
  text-decoration: underline;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}
</style>
