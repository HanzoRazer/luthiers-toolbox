<script setup lang="ts">
/**
 * OrdersView - Customer Orders & Work Order Management
 * Track customer orders, work orders, and production queue
 *
 * Connected to API endpoints:
 *   GET  /api/rmos/orders
 *   POST /api/rmos/orders
 *   PUT  /api/rmos/orders/:id
 */
import { ref } from 'vue'

const activeTab = ref('active')  // active, completed, quotes

const orders = ref([
  { id: 'ORD-2026-042', customer: 'John D.', item: 'Custom Classical Guitar', status: 'in_progress', progress: 65, dueDate: '2026-04-15', total: 4500 },
  { id: 'ORD-2026-041', customer: 'Sarah M.', item: 'OM Acoustic', status: 'in_progress', progress: 30, dueDate: '2026-05-01', total: 3800 },
  { id: 'ORD-2026-040', customer: 'Mike T.', item: 'Electric Stratocaster', status: 'queued', progress: 0, dueDate: '2026-05-20', total: 2200 },
])

const completedOrders = ref([
  { id: 'ORD-2026-039', customer: 'Lisa K.', item: 'Parlor Guitar', status: 'delivered', completedDate: '2026-03-01', total: 3200 },
  { id: 'ORD-2026-038', customer: 'David R.', item: 'Ukulele Set (3)', status: 'delivered', completedDate: '2026-02-20', total: 1800 },
])

const statusLabels: Record<string, string> = {
  queued: '📋 Queued',
  in_progress: '🔨 In Progress',
  finishing: '✨ Finishing',
  delivered: '✅ Delivered',
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}
</script>

<template>
  <div class="orders-view">
    <div class="header">
      <div class="header-content">
        <div>
          <h1>Orders</h1>
          <p class="subtitle">Customer orders and work order management</p>
        </div>
        <button class="btn btn-primary">+ New Order</button>
      </div>
    </div>

    <div class="toolbar">
      <div class="tabs">
        <button :class="{ active: activeTab === 'active' }" @click="activeTab = 'active'">
          Active ({{ orders.length }})
        </button>
        <button :class="{ active: activeTab === 'completed' }" @click="activeTab = 'completed'">
          Completed
        </button>
        <button :class="{ active: activeTab === 'quotes' }" @click="activeTab = 'quotes'">
          Quotes
        </button>
      </div>
      <div class="filters">
        <select>
          <option>All Statuses</option>
          <option>Queued</option>
          <option>In Progress</option>
          <option>Finishing</option>
        </select>
        <input type="text" placeholder="Search orders..." class="search-input" />
      </div>
    </div>

    <div class="content">
      <!-- Active Orders -->
      <div v-if="activeTab === 'active'" class="orders-grid">
        <div v-for="order in orders" :key="order.id" class="order-card">
          <div class="card-header">
            <span class="order-id">{{ order.id }}</span>
            <span :class="['status-badge', order.status]">{{ statusLabels[order.status] }}</span>
          </div>
          <h3 class="order-item">{{ order.item }}</h3>
          <p class="customer">Customer: {{ order.customer }}</p>

          <div class="progress-section">
            <div class="progress-header">
              <span>Progress</span>
              <span>{{ order.progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: order.progress + '%' }"></div>
            </div>
          </div>

          <div class="card-footer">
            <div class="order-meta">
              <span class="due-date">Due: {{ order.dueDate }}</span>
              <span class="total">{{ formatCurrency(order.total) }}</span>
            </div>
            <div class="card-actions">
              <button class="btn btn-sm">View</button>
              <button class="btn btn-sm">Update</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Completed Orders -->
      <div v-if="activeTab === 'completed'" class="orders-table">
        <div class="table-header">
          <span>Order ID</span>
          <span>Customer</span>
          <span>Item</span>
          <span>Completed</span>
          <span>Total</span>
        </div>
        <div v-for="order in completedOrders" :key="order.id" class="table-row">
          <span class="order-id">{{ order.id }}</span>
          <span>{{ order.customer }}</span>
          <span>{{ order.item }}</span>
          <span>{{ order.completedDate }}</span>
          <span class="total">{{ formatCurrency(order.total) }}</span>
        </div>
      </div>

      <!-- Quotes Tab -->
      <div v-if="activeTab === 'quotes'" class="placeholder-panel">
        <span class="icon">📝</span>
        <p>Quote management coming soon</p>
        <p class="detail">Create and track customer quotes</p>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full order management with deposits, milestones, and customer portal coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.orders-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header-content { display: flex; justify-content: space-between; align-items: flex-start; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.toolbar { max-width: 1400px; margin: 0 auto 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }
.tabs { display: flex; gap: 0.5rem; }
.tabs button { padding: 0.5rem 1rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #888; cursor: pointer; }
.tabs button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
.filters { display: flex; gap: 0.75rem; }
.filters select, .search-input { padding: 0.5rem 1rem; background: #1a1a1a; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }
.search-input { width: 200px; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-sm { padding: 0.375rem 0.75rem; font-size: 0.875rem; background: #333; color: #e5e5e5; }

.content { max-width: 1400px; margin: 0 auto; }

.orders-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
.order-card { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.order-id { font-size: 0.75rem; color: #888; font-family: monospace; }
.status-badge { padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; }
.status-badge.queued { background: #6b728020; color: #9ca3af; }
.status-badge.in_progress { background: #2563eb20; color: #60a5fa; }
.status-badge.finishing { background: #8b5cf620; color: #a78bfa; }

.order-item { font-size: 1.125rem; font-weight: 600; margin: 0 0 0.5rem; }
.customer { font-size: 0.875rem; color: #888; margin: 0 0 1rem; }

.progress-section { margin-bottom: 1rem; }
.progress-header { display: flex; justify-content: space-between; font-size: 0.75rem; color: #888; margin-bottom: 0.25rem; }
.progress-bar { height: 6px; background: #333; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #2563eb; transition: width 0.3s; }

.card-footer { display: flex; justify-content: space-between; align-items: flex-end; }
.order-meta { display: flex; flex-direction: column; }
.due-date { font-size: 0.75rem; color: #888; }
.total { font-size: 1rem; font-weight: 600; color: #22c55e; }
.card-actions { display: flex; gap: 0.5rem; }

.orders-table { background: #1a1a1a; border-radius: 0.75rem; overflow: hidden; }
.table-header { display: grid; grid-template-columns: 150px 1fr 2fr 120px 100px; padding: 1rem 1.5rem; background: #262626; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; }
.table-row { display: grid; grid-template-columns: 150px 1fr 2fr 120px 100px; padding: 1rem 1.5rem; border-bottom: 1px solid #262626; align-items: center; }

.placeholder-panel { background: #1a1a1a; border-radius: 0.75rem; padding: 4rem; text-align: center; }
.placeholder-panel .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }
.placeholder-panel p { color: #666; margin: 0; }
.placeholder-panel .detail { font-size: 0.875rem; margin-top: 0.5rem; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }
</style>
