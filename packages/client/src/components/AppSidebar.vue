<template>
  <nav class="app-sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">The Production Shop</span>
      <span class="sidebar-subtitle">CAM / LAB</span>
    </div>

    <!-- MODULE 1: CAM -->
    <div class="sidebar-module">
      <button
        class="module-header"
        :class="{ active: isModuleActive('cam') }"
        @click="toggleModule('cam')"
      >
        <span class="module-icon">&#9881;</span>
        <span class="module-name">CAM</span>
        <span class="module-chevron" :class="{ expanded: expandedModules.cam }">&#9662;</span>
      </button>
      <div v-show="expandedModules.cam" class="module-items">
        <RouterLink to="/quick-cut" class="sidebar-item" active-class="active">
          Quick Cut
        </RouterLink>
        <RouterLink to="/lab/pipeline" class="sidebar-item" active-class="active">
          Pipeline Lab
        </RouterLink>
        <RouterLink to="/settings/cam" class="sidebar-item" active-class="active">
          CAM Settings
        </RouterLink>
      </div>
    </div>

    <!-- MODULE 2: Labs -->
    <div class="sidebar-module">
      <button
        class="module-header"
        :class="{ active: isModuleActive('labs') }"
        @click="toggleModule('labs')"
      >
        <span class="module-icon">&#9879;</span>
        <span class="module-name">Labs</span>
        <span class="module-chevron" :class="{ expanded: expandedModules.labs }">&#9662;</span>
      </button>
      <div v-show="expandedModules.labs" class="module-items">
        <RouterLink to="/lab/bridge" class="sidebar-item" active-class="active">
          Bridge Lab
        </RouterLink>
        <RouterLink to="/lab/adaptive" class="sidebar-item" active-class="active">
          Adaptive Lab
        </RouterLink>
        <div class="sidebar-subgroup">
          <span class="subgroup-label">Saw Lab</span>
          <RouterLink to="/lab/saw/slice" class="sidebar-item sub" active-class="active">
            Slice
          </RouterLink>
          <RouterLink to="/lab/saw/batch" class="sidebar-item sub" active-class="active">
            Batch
          </RouterLink>
          <RouterLink to="/lab/saw/contour" class="sidebar-item sub" active-class="active">
            Contour
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- MODULE 3: Tools -->
    <div class="sidebar-module">
      <button
        class="module-header"
        :class="{ active: isModuleActive('tools') }"
        @click="toggleModule('tools')"
      >
        <span class="module-icon">&#128296;</span>
        <span class="module-name">Tools</span>
        <span class="module-chevron" :class="{ expanded: expandedModules.tools }">&#9662;</span>
      </button>
      <div v-show="expandedModules.tools" class="module-items">
        <RouterLink to="/calculators" class="sidebar-item" active-class="active">
          Calculators
        </RouterLink>
        <RouterLink to="/lab/risk-timeline" class="sidebar-item" active-class="active">
          Risk Timeline
        </RouterLink>
      </div>
    </div>

    <!-- MODULE 4: Creative -->
    <div class="sidebar-module">
      <button
        class="module-header"
        :class="{ active: isModuleActive('creative') }"
        @click="toggleModule('creative')"
      >
        <span class="module-icon">&#127912;</span>
        <span class="module-name">Creative</span>
        <span class="module-chevron" :class="{ expanded: expandedModules.creative }">&#9662;</span>
      </button>
      <div v-show="expandedModules.creative" class="module-items">
        <RouterLink to="/ai-images" class="sidebar-item" active-class="active">
          AI Images
        </RouterLink>
        <div class="sidebar-subgroup">
          <span class="subgroup-label">Acoustics</span>
          <RouterLink to="/tools/audio-analyzer/library" class="sidebar-item sub" active-class="active">
            Library
          </RouterLink>
          <RouterLink to="/tools/audio-analyzer/runs" class="sidebar-item sub" active-class="active">
            Runs Browser
          </RouterLink>
          <RouterLink to="/tools/audio-analyzer/ingest" class="sidebar-item sub" active-class="active">
            Ingest Log
          </RouterLink>
          <RouterLink to="/tools/audio-analyzer" class="sidebar-item sub" active-class="active">
            Viewer
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- MODULE 5: Business -->
    <div class="sidebar-module">
      <button
        class="module-header"
        :class="{ active: isModuleActive('business') }"
        @click="toggleModule('business')"
      >
        <span class="module-icon">&#128200;</span>
        <span class="module-name">Business</span>
        <span class="module-chevron" :class="{ expanded: expandedModules.business }">&#9662;</span>
      </button>
      <div v-show="expandedModules.business" class="module-items">
        <RouterLink to="/business/estimator" class="sidebar-item" active-class="active">
          <span>Estimator</span>
          <span class="pro-badge">PRO</span>
        </RouterLink>
      </div>
    </div>

    <!-- User Menu at bottom -->
    <div class="sidebar-footer">
      <UserMenu />
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { UserMenu } from '@/components/auth'

const route = useRoute()

// Track which modules are expanded
const expandedModules = reactive({
  cam: true,
  labs: true,
  tools: false,
  creative: false,
  business: false,
})

// Module route prefixes for highlighting
const moduleRoutes = {
  cam: ['/quick-cut', '/lab/pipeline', '/settings/cam'],
  labs: ['/lab/bridge', '/lab/adaptive', '/lab/saw'],
  tools: ['/calculators', '/lab/risk-timeline'],
  creative: ['/ai-images', '/tools/audio-analyzer'],
  business: ['/business'],
}

// Check if a module has active routes
function isModuleActive(module: keyof typeof moduleRoutes): boolean {
  const prefixes = moduleRoutes[module]
  return prefixes.some(prefix => route.path.startsWith(prefix))
}

// Toggle module expansion
function toggleModule(module: keyof typeof expandedModules) {
  expandedModules[module] = !expandedModules[module]
}

// Auto-expand module when navigating to its routes
watch(() => route.path, (newPath) => {
  for (const [module, prefixes] of Object.entries(moduleRoutes)) {
    if (prefixes.some(prefix => newPath.startsWith(prefix))) {
      expandedModules[module as keyof typeof expandedModules] = true
    }
  }
}, { immediate: true })
</script>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
  color: #e0e0e0;
  font-size: 13px;
  user-select: none;
}

.sidebar-header {
  padding: 16px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.sidebar-title {
  display: block;
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

.sidebar-subtitle {
  display: block;
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 2px;
}

.sidebar-module {
  border-bottom: 1px solid #2a2a4a;
}

.module-header {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: #c0c0c0;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.module-header:hover {
  background: #252540;
}

.module-header.active {
  background: #1e3a5f;
  color: #fff;
}

.module-icon {
  width: 20px;
  text-align: center;
  margin-right: 8px;
  font-size: 14px;
}

.module-name {
  flex: 1;
  font-weight: 500;
}

.module-chevron {
  font-size: 10px;
  transition: transform 0.2s;
}

.module-chevron.expanded {
  transform: rotate(180deg);
}

.module-items {
  padding: 4px 0;
  background: #16162a;
}

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 8px 40px;
  color: #a0a0a0;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.sidebar-item:hover {
  background: #252540;
  color: #fff;
}

.sidebar-item.active {
  background: #2563eb;
  color: #fff;
}

.sidebar-item.sub {
  padding-left: 52px;
  font-size: 12px;
}

.sidebar-subgroup {
  margin-top: 4px;
}

.subgroup-label {
  display: block;
  padding: 6px 12px 4px 40px;
  font-size: 10px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pro-badge {
  font-size: 9px;
  padding: 2px 6px;
  background: #d97706;
  color: #fff;
  border-radius: 3px;
  font-weight: 600;
}

.sidebar-footer {
  margin-top: auto;
  padding: 12px;
  border-top: 1px solid #2a2a4a;
}
</style>
