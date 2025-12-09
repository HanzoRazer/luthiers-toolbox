<template>
  <div class="post-selector">
    <label class="post-label">Post-Processor</label>
    <select v-model="postId" class="post-select">
      <option value="grbl">GRBL (Arduino/Hobby CNC)</option>
      <option value="mach4">Mach4 (Industrial PC)</option>
      <option value="linuxcnc">LinuxCNC (Open Source)</option>
      <option value="pathpilot">PathPilot (Tormach)</option>
      <option value="masso">MASSO (G3 Touch)</option>
    </select>
    <button @click="applyToAll" class="apply-btn">
      Apply to all CAM exports
    </button>
    <span v-if="applied" class="applied-indicator">✓ Applied</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * PostSelector Component (Patch J2)
 * 
 * Global post-processor selector that broadcasts the selected controller
 * to all CAM export components via CustomEvent.
 * 
 * Features:
 * - One-click application to all CAM operations
 * - Event-based communication (post-selected)
 * - Visual feedback when applied
 * - Supports 5 CNC controllers
 * 
 * Usage:
 * 1. Add to CAM toolbar/sidebar
 * 2. Listen for 'post-selected' events in export components:
 *    window.addEventListener('post-selected', (e) => {
 *      this.postId = e.detail.post_id
 *    })
 */

// State
const postId = ref<string>('grbl')
const applied = ref<boolean>(false)

// Apply post-processor to all CAM exports
function applyToAll() {
  // Broadcast event to all listeners
  window.dispatchEvent(
    new CustomEvent('post-selected', {
      detail: { post_id: postId.value }
    })
  )
  
  // Show feedback
  applied.value = true
  setTimeout(() => {
    applied.value = false
  }, 2000)
}

// Auto-broadcast when selection changes (optional)
watch(postId, (newValue) => {
  // Uncomment to auto-apply on change:
  // window.dispatchEvent(
  //   new CustomEvent('post-selected', {
  //     detail: { post_id: newValue }
  //   })
  // )
})
</script>

<style scoped>
.post-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.post-label {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.post-select {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid #ccc;
  border-radius: 3px;
  background: white;
  cursor: pointer;
  min-width: 180px;
}

.post-select:hover {
  border-color: #999;
}

.post-select:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
}

.apply-btn {
  padding: 4px 12px;
  font-size: 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}

.apply-btn:hover {
  background: #45a049;
}

.apply-btn:active {
  background: #3d8b40;
}

.applied-indicator {
  font-size: 12px;
  color: #4CAF50;
  font-weight: 600;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(-5px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .post-selector {
    flex-wrap: wrap;
  }
  
  .post-select {
    min-width: 100%;
  }
  
  .apply-btn {
    flex: 1;
  }
}
</style>
