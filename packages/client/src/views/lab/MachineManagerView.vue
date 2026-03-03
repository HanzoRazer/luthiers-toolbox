<script setup lang="ts">
/**
 * MachineManagerView - CNC Machine Manager
 * Configure, monitor, and manage CNC machine profiles
 * and their associated post-processors.
 */
import { ref } from 'vue'

const machines = ref([
  { id: 1, name: 'Shapeoko Pro XL', controller: 'Carbide Motion', status: 'active', workArea: '840 x 840 mm' },
  { id: 2, name: 'Avid CNC Pro', controller: 'Mach4', status: 'idle', workArea: '1220 x 610 mm' },
  { id: 3, name: 'Onefinity Woodworker', controller: 'OnefinityOS', status: 'offline', workArea: '816 x 816 mm' },
])

const selectedMachine = ref<number | null>(null)
</script>

<template>
  <div class="machine-manager-view">
    <header class="view-header">
      <h1>Machine Manager</h1>
      <p class="subtitle">Configure and manage your CNC machines and post-processors</p>
    </header>

    <div class="content-grid">
      <section class="panel machines-panel">
        <div class="panel-header">
          <h2>My Machines</h2>
          <button class="btn-primary btn-sm">+ Add Machine</button>
        </div>
        <div class="machine-list">
          <div
            v-for="machine in machines"
            :key="machine.id"
            class="machine-card"
            :class="{ selected: selectedMachine === machine.id }"
            @click="selectedMachine = machine.id"
          >
            <div class="machine-icon">
              <span>CNC</span>
            </div>
            <div class="machine-info">
              <h3>{{ machine.name }}</h3>
              <div class="machine-meta">
                <span>{{ machine.controller }}</span>
                <span class="separator">|</span>
                <span>{{ machine.workArea }}</span>
              </div>
            </div>
            <div class="machine-status" :class="machine.status">
              <span class="status-dot"></span>
              <span>{{ machine.status }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel config-panel">
        <h2>Machine Configuration</h2>
        <div v-if="!selectedMachine" class="empty-state">
          <p>Select a machine to configure</p>
        </div>
        <div v-else class="config-form">
          <div class="form-section">
            <h3>Basic Settings</h3>
            <div class="form-group">
              <label>Machine Name</label>
              <input type="text" value="Shapeoko Pro XL" />
            </div>
            <div class="form-group">
              <label>Controller Type</label>
              <select>
                <option>Carbide Motion</option>
                <option>Mach3</option>
                <option>Mach4</option>
                <option>GRBL</option>
                <option>LinuxCNC</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h3>Work Envelope</h3>
            <div class="form-row">
              <div class="form-group">
                <label>X Travel (mm)</label>
                <input type="number" value="840" />
              </div>
              <div class="form-group">
                <label>Y Travel (mm)</label>
                <input type="number" value="840" />
              </div>
              <div class="form-group">
                <label>Z Travel (mm)</label>
                <input type="number" value="100" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>Spindle</h3>
            <div class="form-row">
              <div class="form-group">
                <label>Max RPM</label>
                <input type="number" value="24000" />
              </div>
              <div class="form-group">
                <label>Min RPM</label>
                <input type="number" value="5000" />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-secondary">Reset</button>
            <button class="btn-primary">Save Changes</button>
          </div>
        </div>
      </section>

      <section class="panel posts-panel">
        <h2>Post-Processors</h2>
        <div class="post-list">
          <div class="post-item">
            <span class="post-name">Carbide3D (Grbl)</span>
            <span class="post-ext">.nc</span>
            <button class="btn-icon" title="Configure">...</button>
          </div>
          <div class="post-item">
            <span class="post-name">Mach3/4</span>
            <span class="post-ext">.tap</span>
            <button class="btn-icon" title="Configure">...</button>
          </div>
          <div class="post-item">
            <span class="post-name">LinuxCNC</span>
            <span class="post-ext">.ngc</span>
            <button class="btn-icon" title="Configure">...</button>
          </div>
        </div>
        <button class="btn-secondary btn-full">+ Add Post-Processor</button>
      </section>

      <section class="panel tools-panel">
        <h2>Tool Library</h2>
        <div class="tool-list">
          <div class="tool-item">
            <span class="tool-num">#1</span>
            <span class="tool-desc">6mm Flat Endmill</span>
          </div>
          <div class="tool-item">
            <span class="tool-num">#2</span>
            <span class="tool-desc">3mm Ball Nose</span>
          </div>
          <div class="tool-item">
            <span class="tool-num">#3</span>
            <span class="tool-desc">1mm Engraving V-bit 60°</span>
          </div>
          <div class="tool-item">
            <span class="tool-num">#4</span>
            <span class="tool-desc">0.8mm Slot Cutter</span>
          </div>
        </div>
        <button class="btn-secondary btn-full">Manage Tools</button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.machine-manager-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.panel-header h2 {
  margin-bottom: 0;
}

.machine-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.machine-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.machine-card:hover {
  border-color: #2563eb;
}

.machine-card.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.machine-icon {
  width: 48px;
  height: 48px;
  background: #f1f5f9;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.machine-info h3 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.machine-meta {
  font-size: 0.75rem;
  color: #64748b;
}

.machine-meta .separator {
  margin: 0 0.5rem;
}

.machine-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.machine-status.active .status-dot {
  background: #10b981;
}

.machine-status.active {
  color: #10b981;
}

.machine-status.idle .status-dot {
  background: #f59e0b;
}

.machine-status.idle {
  color: #f59e0b;
}

.machine-status.offline .status-dot {
  background: #94a3b8;
}

.machine-status.offline {
  color: #94a3b8;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #94a3b8;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.75rem;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-full {
  width: 100%;
  margin-top: 1rem;
}

.btn-icon {
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  background: #fff;
  cursor: pointer;
}

.post-list,
.tool-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.post-item,
.tool-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.post-name {
  flex: 1;
  color: #1e293b;
}

.post-ext {
  color: #64748b;
  font-family: monospace;
}

.tool-num {
  font-weight: 600;
  color: #2563eb;
  min-width: 2rem;
}

.tool-desc {
  color: #475569;
}
</style>
