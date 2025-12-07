<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

interface DesignCard {
  title: string
  description: string
  icon: string
  path: string
  status: 'Production' | 'Beta' | 'Coming Soon'
  version: string
  badge?: string
}

const designTools: DesignCard[] = [
  {
    title: 'Blueprint Lab',
    description: 'AI-powered guitar photo analysis → vectorization → DXF export',
    icon: '📐',
    path: '/blueprint-lab',
    status: 'Production',
    version: 'Phase 2',
    badge: 'AI'
  },
  {
    title: 'Relief Mapper',
    description: 'SVG to 3D relief carving with depth control and grayscale preview',
    icon: '🗿',
    path: '/art/relief',
    status: 'Production',
    version: 'v16.0'
  },
  {
    title: 'Rosette Designer',
    description: 'Parametric acoustic guitar rosettes with DXF/G-code export',
    icon: '🌺',
    path: '/art-studio',
    status: 'Production',
    version: 'v16.0'
  },
  {
    title: 'Headstock Logo',
    description: 'Logo and inlay design with v-carve toolpath generation',
    icon: '🎸',
    path: '/art/headstock',
    status: 'Production',
    version: 'v15.5'
  },
  {
    title: 'V-Carve Editor',
    description: 'Centerline art to decorative V-grooves with adaptive depth',
    icon: '✏️',
    path: '#',
    status: 'Coming Soon',
    version: 'v16.2'
  },
  {
    title: 'Inlay Designer',
    description: 'Multi-material inlay planning with pocket and insert geometry',
    icon: '💎',
    path: '#',
    status: 'Coming Soon',
    version: 'v16.3'
  }
]

const camIntegrations: DesignCard[] = [
  {
    title: 'CAM Toolbox',
    description: 'N15-N18 production modules: G-code backplot, adaptive benchmarking, polygon processing',
    icon: '🔧',
    path: '/art-studio/cam',
    status: 'Production',
    version: 'N15-N18',
    badge: 'NEW'
  },
  {
    title: 'Helical Ramping',
    description: 'Smooth spiral entry for hardwood plunging (pocket milling)',
    icon: '🌊',
    path: '/lab/helical',
    status: 'Production',
    version: 'v16.1'
  },
  {
    title: 'Polygon Offset',
    description: 'Robust offsetting with pyclipper and arc linkers for smooth profiles',
    icon: '🔺',
    path: '/lab/polygon-offset',
    status: 'Production',
    version: 'N17'
  },
  {
    title: 'CAM Operations',
    description: 'Full production toolpath suite (pocketing, drilling, benchmarking)',
    icon: '⚙️',
    path: '/cam/dashboard',
    status: 'Production',
    version: 'Module L-N'
  }
]

// Flatten for rendering
const designs = [...designTools, ...camIntegrations]

function navigateTo(path: string) {
  if (path === '#') {
    alert('This feature is coming soon! Check the Re-Forestation Plan for integration timeline.')
    return
  }
  router.push(path)
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'Production': return '#16a34a' // green
    case 'Beta': return '#ea580c' // orange
    case 'Coming Soon': return '#6b7280' // gray
    default: return '#6b7280'
  }
}
</script>

<template>
  <div class="art-studio-dashboard">
    <header class="dashboard-header">
      <h1>🎨 Art Studio</h1>
      <p>Decorative lutherie design tools for CNC machining</p>
    </header>

    <div class="design-grid">
      <div
        v-for="design in designs"
        :key="design.title"
        class="design-card"
        @click="navigateTo(design.path)"
        :class="{ disabled: design.status === 'Coming Soon' }"
      >
        <div class="card-header">
          <span class="icon">{{ design.icon }}</span>
          <span
            class="status-badge"
            :style="{ backgroundColor: getStatusColor(design.status) }"
          >
            {{ design.status }}
          </span>
        </div>
        <h3>{{ design.title }}</h3>
        <p>{{ design.description }}</p>
        <div class="card-footer">
          <span class="version">{{ design.version }}</span>
          <span v-if="design.badge" class="new-badge">{{ design.badge }}</span>
        </div>
      </div>
    </div>

    <section class="feature-highlights">
      <h2>✨ Feature Highlights</h2>
      <div class="highlights-grid">
        <div class="highlight">
          <h4>🎨 Design-First Workflow</h4>
          <p>Create decorative elements visually before generating toolpaths</p>
        </div>
        <div class="highlight">
          <h4>📐 Parametric Control</h4>
          <p>Adjust designs with sliders and inputs for instant updates</p>
        </div>
        <div class="highlight">
          <h4>🔧 Integrated CAM</h4>
          <p>Access production toolpath operations directly from Art Studio</p>
        </div>
        <div class="highlight">
          <h4>🌊 Advanced Operations</h4>
          <p>Helical ramping, polygon offsetting, and adaptive pocketing</p>
        </div>
      </div>
    </section>

    <footer class="dashboard-footer">
      <p>
        <strong>💡 Tip:</strong> Art Studio tools focus on <em>decorative design</em>. For production milling, click the <strong>CAM Operations</strong> card to access the full toolpath suite.
        <br>
        <strong>📚 Documentation:</strong> See <code>ART_STUDIO_V16_1_HELICAL_INTEGRATION.md</code> for v16.1 features and <code>N16_N18_FRONTEND_DEVELOPER_HANDOFF.md</code> for N15-N18 backend integration.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.art-studio-dashboard {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 2rem;
  text-align: center;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #1e293b;
}

.dashboard-header p {
  font-size: 1.125rem;
  color: #64748b;
}

.design-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.design-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.design-card:hover:not(.disabled) {
  border-color: #ec4899;
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.15);
  transform: translateY(-2px);
}

.design-card.disabled {
  cursor: not-allowed;
  opacity: 0.6;
  background: #f8fafc;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.icon {
  font-size: 2rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.design-card h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #1e293b;
}

.design-card p {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 1rem;
  min-height: 3rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #94a3b8;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
}

.version {
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.new-badge {
  background: #fbbf24;
  color: #78350f;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-weight: 700;
  text-transform: uppercase;
}

.feature-highlights {
  margin-bottom: 2rem;
}

.feature-highlights h2 {
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
  color: #1e293b;
  text-align: center;
}

.highlights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.highlight {
  background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
  border: 2px solid #f9a8d4;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.highlight h4 {
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
  color: #831843;
}

.highlight p {
  font-size: 0.875rem;
  color: #9f1239;
  margin: 0;
  line-height: 1.6;
}

.dashboard-footer {
  background: #fef3c7;
  border: 2px solid #fde047;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.dashboard-footer p {
  margin: 0;
  color: #78350f;
  line-height: 1.8;
}

.dashboard-footer code {
  background: #fef08a;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: 'Courier New', monospace;
  color: #713f12;
}
</style>
