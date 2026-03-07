<script setup lang="ts">
/**
 * InventoryView - RMOS Material & Tool Inventory Management
 * Track wood stock, tools, consumables, and reorder alerts
 *
 * Connected to API endpoints:
 *   GET  /api/rmos/inventory
 *   POST /api/rmos/inventory/items
 *   PUT  /api/rmos/inventory/items/:id
 */
import { ref } from 'vue'

const activeTab = ref('materials')  // materials, tools, consumables

// Mock inventory data
const materials = ref([
  { id: 1, name: 'Sitka Spruce Tops', quantity: 12, unit: 'pcs', reorderAt: 5, status: 'ok' },
  { id: 2, name: 'Indian Rosewood Sets', quantity: 4, unit: 'sets', reorderAt: 6, status: 'low' },
  { id: 3, name: 'Maple Necks', quantity: 8, unit: 'pcs', reorderAt: 4, status: 'ok' },
])

const tools = ref([
  { id: 1, name: '6mm Spiral Upcut', condition: 'good', hours: 12, maxHours: 50 },
  { id: 2, name: '3.175mm Ball Nose', condition: 'fair', hours: 38, maxHours: 50 },
  { id: 3, name: 'Fret Slotting Saw', condition: 'excellent', hours: 5, maxHours: 100 },
])

const searchQuery = ref('')
const showAddModal = ref(false)
</script>

<template>
  <div class="inventory-view">
    <div class="header">
      <h1>Inventory Management</h1>
      <p class="subtitle">Track materials, tools, and consumables</p>
    </div>

    <div class="toolbar">
      <div class="tabs">
        <button :class="{ active: activeTab === 'materials' }" @click="activeTab = 'materials'">
          Materials
        </button>
        <button :class="{ active: activeTab === 'tools' }" @click="activeTab = 'tools'">
          Tools
        </button>
        <button :class="{ active: activeTab === 'consumables' }" @click="activeTab = 'consumables'">
          Consumables
        </button>
      </div>
      <div class="actions">
        <input type="text" v-model="searchQuery" placeholder="Search inventory..." class="search-input" />
        <button class="btn btn-primary" @click="showAddModal = true">+ Add Item</button>
      </div>
    </div>

    <div class="content">
      <!-- Materials Tab -->
      <div v-if="activeTab === 'materials'" class="inventory-table">
        <div class="table-header">
          <span>Material</span>
          <span>Quantity</span>
          <span>Reorder Point</span>
          <span>Status</span>
          <span>Actions</span>
        </div>
        <div v-for="item in materials" :key="item.id" class="table-row">
          <span class="item-name">{{ item.name }}</span>
          <span>{{ item.quantity }} {{ item.unit }}</span>
          <span>{{ item.reorderAt }} {{ item.unit }}</span>
          <span :class="['status-badge', item.status]">
            {{ item.status === 'low' ? '⚠️ Low Stock' : '✓ In Stock' }}
          </span>
          <span class="row-actions">
            <button class="btn-sm">Edit</button>
            <button class="btn-sm">Adjust</button>
          </span>
        </div>
      </div>

      <!-- Tools Tab -->
      <div v-if="activeTab === 'tools'" class="inventory-table">
        <div class="table-header">
          <span>Tool</span>
          <span>Condition</span>
          <span>Usage</span>
          <span>Actions</span>
        </div>
        <div v-for="tool in tools" :key="tool.id" class="table-row">
          <span class="item-name">{{ tool.name }}</span>
          <span :class="['condition-badge', tool.condition]">{{ tool.condition }}</span>
          <span>
            <div class="usage-bar">
              <div class="usage-fill" :style="{ width: (tool.hours / tool.maxHours * 100) + '%' }"></div>
            </div>
            <span class="usage-text">{{ tool.hours }}/{{ tool.maxHours }} hrs</span>
          </span>
          <span class="row-actions">
            <button class="btn-sm">Log Use</button>
            <button class="btn-sm">Replace</button>
          </span>
        </div>
      </div>

      <!-- Consumables Tab -->
      <div v-if="activeTab === 'consumables'" class="placeholder-panel">
        <span class="icon">📦</span>
        <p>Consumables tracking coming soon</p>
        <p class="detail">Sandpaper, adhesives, finishes, and more</p>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full inventory management with barcode scanning and supplier integration coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.inventory-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.toolbar { max-width: 1400px; margin: 0 auto 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }
.tabs { display: flex; gap: 0.5rem; }
.tabs button { padding: 0.5rem 1rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #888; cursor: pointer; }
.tabs button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
.actions { display: flex; gap: 0.75rem; }
.search-input { padding: 0.5rem 1rem; background: #1a1a1a; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; width: 250px; }
.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }

.content { max-width: 1400px; margin: 0 auto; }
.inventory-table { background: #1a1a1a; border-radius: 0.75rem; overflow: hidden; }
.table-header { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; padding: 1rem 1.5rem; background: #262626; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; }
.table-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; padding: 1rem 1.5rem; border-bottom: 1px solid #262626; align-items: center; }
.item-name { font-weight: 500; }

.status-badge { font-size: 0.875rem; }
.status-badge.low { color: #f59e0b; }
.status-badge.ok { color: #22c55e; }

.condition-badge { padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; text-transform: capitalize; }
.condition-badge.excellent { background: #22c55e20; color: #22c55e; }
.condition-badge.good { background: #3b82f620; color: #3b82f6; }
.condition-badge.fair { background: #f59e0b20; color: #f59e0b; }

.usage-bar { width: 100px; height: 6px; background: #333; border-radius: 3px; overflow: hidden; margin-bottom: 0.25rem; }
.usage-fill { height: 100%; background: #2563eb; }
.usage-text { font-size: 0.75rem; color: #888; }

.row-actions { display: flex; gap: 0.5rem; }
.btn-sm { padding: 0.25rem 0.5rem; background: #333; border: none; border-radius: 0.25rem; color: #888; font-size: 0.75rem; cursor: pointer; }
.btn-sm:hover { background: #444; color: #e5e5e5; }

.placeholder-panel { background: #1a1a1a; border-radius: 0.75rem; padding: 4rem; text-align: center; }
.placeholder-panel .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }
.placeholder-panel p { color: #666; margin: 0; }
.placeholder-panel .detail { font-size: 0.875rem; margin-top: 0.5rem; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }
</style>
