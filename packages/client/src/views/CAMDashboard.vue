<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

interface OperationCard {
  title: string
  description: string
  icon: string
  path: string
  status: 'Production' | 'Beta' | 'Coming Soon'
  version?: string
  badge?: string
}

// Group operations by category for better organization
const coreOperations: OperationCard[] = [
  {
    title: 'Adaptive Pocketing',
    description: 'Spiral and lane-based pocket milling with trochoidal insertion',
    icon: '🌀',
    path: '/cam',
    status: 'Production',
    version: 'Module L.3'
  },
  {
    title: 'Helical Ramping',
    description: 'Smooth spiral entry for plunge operations in hardwood',
    icon: '🌊',
    path: '/lab/helical',
    status: 'Production',
    version: 'v16.1'
  },
  {
    title: 'Polygon Offset',
    description: 'Robust offsetting with pyclipper and arc linkers (G2/G3)',
    icon: '🔺',
    path: '/lab/polygon-offset',
    status: 'Production',
    version: 'N17',
    badge: 'NEW'
  }
]

const analysisOperations: OperationCard[] = [
  {
    title: 'G-code Backplot',
    description: 'Visualize toolpaths and estimate cycle time from G-code',
    icon: '📊',
    path: '#',
    status: 'Coming Soon',
    version: 'N15',
    badge: 'PLANNED'
  },
  {
    title: 'Adaptive Benchmark',
    description: 'Performance profiling for spiral algorithms and trochoids',
    icon: '⚡',
    path: '/lab/adaptive-benchmark',
    status: 'Production',
    version: 'N16'
  },
  {
    title: 'Toolpath Simulation',
    description: 'Real-time visualization with arc support and heatmaps',
    icon: '🎬',
    path: '#',
    status: 'Coming Soon',
    version: 'I.1.2'
  },
  {
    title: 'Risk Analytics',
    description: 'Historical CAM operation risk timeline',
    icon: '⚠️',
    path: '/lab/risk-timeline',
    status: 'Production',
    version: 'Phase 18'
  }
]

const riskOperations: OperationCard[] = [
  {
    title: 'Enhanced Risk Timeline',
    description: 'Interactive timeline with sparklines, effect filters, and trends',
    icon: '📈',
    path: '/cam/risk/timeline-enhanced',
    status: 'Production',
    version: 'Phase 28.2',
    badge: 'NEW'
  },
  {
    title: 'Cross-Lab Risk Dashboard',
    description: 'Aggregated risk metrics across all operations',
    icon: '🎯',
    path: '/lab/risk-dashboard',
    status: 'Production',
    version: 'Phase 28.1'
  },
  {
    title: 'Risk Timeline (Classic)',
    description: 'Historical CAM operation risk reports',
    icon: '⚠️',
    path: '/lab/risk-timeline',
    status: 'Production',
    version: 'Phase 18'
  },
  {
    title: 'Relief Risk Timeline',
    description: 'Relief-specific risk tracking with preset filters',
    icon: '🎨',
    path: '/cam/risk/timeline',
    status: 'Production',
    version: 'Phase 26.2'
  },
  {
    title: 'Risk Preset Compare',
    description: 'A/B comparison of preset risk profiles',
    icon: '⚖️',
    path: '/cam/risk/compare',
    status: 'Production',
    version: 'Phase 26.3'
  }
]

const drillingOperations: OperationCard[] = [
  {
    title: 'Drilling Patterns',
    description: 'Modal cycles (G81-G89) for hole arrays',
    icon: '🔩',
    path: '/lab/drilling',
    status: 'Production',
    version: 'N.07'
  },
  {
    title: 'CAM Essentials',
    description: 'Roughing, drilling, and pattern operations',
    icon: '🔧',
    path: '/lab/cam-essentials',
    status: 'Production',
    version: 'N10'
  },
  {
    title: 'Probing Patterns',
    description: 'Work coordinate system probing and verification',
    icon: '📍',
    path: '#',
    status: 'Coming Soon',
    version: 'N.09'
  }
]

const workflowOperations: OperationCard[] = [
  {
    title: 'Blueprint to CAM',
    description: 'Convert guitar blueprint images to CNC toolpaths',
    icon: '📐',
    path: '/blueprint-lab',
    status: 'Production',
    version: 'Phase 2'
  },
  {
    title: 'Pipeline Presets',
    description: 'Run saved CAM pipeline configurations',
    icon: '💾',
    path: '/lab/pipeline-preset',
    status: 'Production',
    version: 'Phase 25'
  },
  {
    title: 'Machine Profiles',
    description: 'CNC controller configuration and capabilities',
    icon: '🤖',
    path: '/lab/machines',
    status: 'Production',
    version: 'Module M.4'
  },
  {
    title: 'Post Processors',
    description: 'Custom CNC post-processor configurations',
    icon: '📝',
    path: '/lab/posts',
    status: 'Production',
    version: 'N.0',
    badge: 'NEW'
  },
  {
    title: 'CAM Settings',
    description: 'Unified configuration dashboard',
    icon: '🎛️',
    path: '/settings/cam',
    status: 'Production',
    version: 'Phase 25'
  }
]

// Flatten for backward compatibility
const operations = [
  ...coreOperations,
  ...analysisOperations,
  ...riskOperations,
  ...drillingOperations,
  ...workflowOperations
]

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
  <div class="cam-dashboard">
    <header class="dashboard-header">
      <h1>🔧 CAM Operations</h1>
      <p>Unified CNC toolpath generation hub for lutherie machining</p>
    </header>

    <div class="operation-grid">
      <div
        v-for="op in operations"
        :key="op.title"
        class="operation-card"
        :class="{ disabled: op.status === 'Coming Soon' }"
        @click="navigateTo(op.path)"
      >
        <div class="card-header">
          <span class="icon">{{ op.icon }}</span>
          <span
            class="status-badge"
            :style="{ backgroundColor: getStatusColor(op.status) }"
          >
            {{ op.status }}
          </span>
        </div>
        <h3>{{ op.title }}</h3>
        <p>{{ op.description }}</p>
        <div class="card-footer">
          <span class="version">{{ op.version }}</span>
          <span
            v-if="op.badge"
            class="new-badge"
          >{{ op.badge }}</span>
        </div>
      </div>
    </div>

    <footer class="dashboard-footer">
      <p>
        <strong>💡 Tip:</strong> Start with Adaptive Pocketing or Helical Ramping for production lutherie work.
        <br>
        <strong>📚 Documentation:</strong> See <code>REFORESTATION_PLAN.md</code> for upcoming features and integration timeline.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.cam-dashboard {
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

.operation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.operation-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.operation-card:hover:not(.disabled) {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.operation-card.disabled {
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

.operation-card h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #1e293b;
}

.operation-card p {
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

.dashboard-footer {
  background: #f1f5f9;
  border: 2px solid #cbd5e1;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.dashboard-footer p {
  margin: 0;
  color: #475569;
  line-height: 1.8;
}

.dashboard-footer code {
  background: #e2e8f0;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: 'Courier New', monospace;
}
</style>
