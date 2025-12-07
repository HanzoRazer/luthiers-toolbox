<template>
  <div class="labs-index">
    <header class="labs-header">
      <h1>🧪 Labs - Advanced Features</h1>
      <p>Experimental and advanced prototyping tools for power users</p>
    </header>

    <div class="search-filter">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="🔍 Search labs..." 
        class="search-input"
      />
      <div class="filter-tags">
        <button 
          v-for="tag in tags" 
          :key="tag"
          :class="{ active: activeTag === tag }"
          @click="activeTag = activeTag === tag ? '' : tag"
        >
          {{ tag }}
        </button>
      </div>
    </div>

    <div class="labs-grid">
      <div 
        v-for="lab in filteredLabs" 
        :key="lab.id" 
        class="lab-card"
        @click="$router.push(lab.route)"
      >
        <div class="lab-icon">{{ lab.icon }}</div>
        <h3>{{ lab.name }}</h3>
        <p>{{ lab.description }}</p>
        <div class="lab-meta">
          <span v-for="tag in lab.tags" :key="tag" class="tag">{{ tag }}</span>
          <span class="module-badge">{{ lab.module }}</span>
        </div>
      </div>
    </div>

    <footer class="labs-footer">
      <p>💡 <strong>What are Labs?</strong> Labs are advanced features that give you more control over CAM operations, geometry processing, and CNC workflows. Perfect for power users and CNC professionals.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const searchQuery = ref('')
const activeTag = ref('')

const tags = ['All', 'CAM', 'Geometry', 'Analysis', 'Beginner', 'Advanced']

const labs = [
  {
    id: 'adaptive-kernel',
    name: 'Adaptive Kernel Lab',
    icon: '🔬',
    description: 'Test adaptive pocketing algorithms with real-time visualization. Module L.1-L.3 features with island handling and spiralizer.',
    route: '/lab/adaptive-kernel',
    tags: ['CAM', 'Advanced'],
    module: 'Module L'
  },
  {
    id: 'helical',
    name: 'Helical Ramp Lab',
    icon: '🌀',
    description: 'Generate smooth helical Z-axis ramping for hardwood machining. Art Studio v16.1 integration.',
    route: '/lab/helical',
    tags: ['CAM', 'Beginner'],
    module: 'v16.1'
  },
  {
    id: 'cam-essentials',
    name: 'CAM Essentials Lab',
    icon: '⚙️',
    description: 'Roughing, drilling, retract patterns, and probe operations. N0-N10 feature suite.',
    route: '/lab/cam-essentials',
    tags: ['CAM', 'Beginner'],
    module: 'Module N'
  },
  {
    id: 'drilling',
    name: 'Drilling Lab',
    icon: '🔩',
    description: 'Advanced drilling UI with G81/G83 canned cycles, grid/circle/line patterns, and preview.',
    route: '/lab/drilling',
    tags: ['CAM', 'Beginner'],
    module: 'N.07'
  },
  {
    id: 'polygon-offset',
    name: 'Polygon Offset Lab',
    icon: '📐',
    description: 'Pyclipper-based polygon offsetting with arc linkers and min-engagement control. N17 features.',
    route: '/lab/polygon-offset',
    tags: ['Geometry', 'Advanced'],
    module: 'N.17'
  },
  {
    id: 'adaptive-benchmark',
    name: 'Adaptive Benchmark Lab',
    icon: '📊',
    description: 'Performance profiling for adaptive pocketing algorithms. Compare L.0, L.1, L.2, L.3 versions.',
    route: '/lab/adaptive-benchmark',
    tags: ['Analysis', 'Advanced'],
    module: 'N.16'
  },
  {
    id: 'relief',
    name: 'Relief Kernel Lab',
    icon: '🗻',
    description: 'Interactive relief carving prototyping with heightmap visualization and toolpath preview.',
    route: '/lab/relief',
    tags: ['CAM', 'Advanced'],
    module: 'Phase 24.2'
  },
  {
    id: 'offset',
    name: 'Offset Lab',
    icon: '🔄',
    description: 'Pyclipper visualizer for debugging polygon offset operations. Real-time arc tolerance control.',
    route: '/lab/offset',
    tags: ['Geometry', 'Advanced'],
    module: 'N.17a'
  },
  {
    id: 'compare',
    name: 'Compare Lab',
    icon: '⚖️',
    description: 'A/B test different CAM strategies side-by-side. Compare toolpaths, statistics, and G-code.',
    route: '/lab/compare',
    tags: ['Analysis', 'Beginner'],
    module: 'Phase 27'
  },
  {
    id: 'pipeline',
    name: 'Pipeline Lab',
    icon: '🔗',
    description: 'Context bridge for multi-operation CAM workflows. Chain operations and manage toolpath sequences.',
    route: '/lab/pipeline',
    tags: ['CAM', 'Advanced'],
    module: 'Bundle 13'
  },
  {
    id: 'saw-dashboard',
    name: 'Saw Lab Dashboard',
    icon: '🪚',
    description: 'Real-time CNC saw monitoring with risk classification, telemetry metrics, and job log integration. CP-S61/62 features.',
    route: '/lab/saw-dashboard',
    tags: ['CAM', 'Analysis', 'Beginner'],
    module: 'CP-S61/62'
  }
]

const filteredLabs = computed(() => {
  let results = [...labs]

  // Filter by active tag first
  if (activeTag.value && activeTag.value !== 'All') {
    results = results.filter(lab => lab.tags.includes(activeTag.value))
  }

  // Then filter by search query
  if (searchQuery.value && searchQuery.value.trim() !== '') {
    const query = searchQuery.value.toLowerCase().trim()
    results = results.filter(lab => 
      lab.name.toLowerCase().includes(query) ||
      lab.description.toLowerCase().includes(query) ||
      lab.tags.some(tag => tag.toLowerCase().includes(query)) ||
      lab.module.toLowerCase().includes(query)
    )
  }

  return results
})
</script>

<style scoped>
.labs-index {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.labs-header {
  text-align: center;
  margin-bottom: 3rem;
}

.labs-header h1 {
  font-size: 2.5rem;
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.labs-header p {
  font-size: 1.2rem;
  color: #718096;
}

.search-filter {
  margin-bottom: 2rem;
}

.search-input {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 1rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.filter-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.filter-tags button {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tags button:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.filter-tags button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.labs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.lab-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s;
}

.lab-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(102, 126, 234, 0.2);
  border-color: #667eea;
}

.lab-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.lab-card h3 {
  font-size: 1.5rem;
  color: #2d3748;
  margin-bottom: 0.75rem;
}

.lab-card p {
  color: #718096;
  line-height: 1.6;
  margin-bottom: 1rem;
  min-height: 60px;
}

.lab-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.tag {
  padding: 0.25rem 0.75rem;
  background: #edf2f7;
  color: #4a5568;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.module-badge {
  padding: 0.25rem 0.75rem;
  background: #667eea;
  color: white;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-left: auto;
}

.labs-footer {
  text-align: center;
  padding: 2rem;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.labs-footer p {
  color: #4a5568;
  line-height: 1.6;
  font-size: 1.05rem;
}

@media (prefers-color-scheme: dark) {
  .labs-header h1 {
    color: #f7fafc;
  }

  .labs-header p {
    color: #cbd5e0;
  }

  .search-input {
    background: #2d3748;
    border-color: #4a5568;
    color: #f7fafc;
  }

  .filter-tags button {
    background: #2d3748;
    border-color: #4a5568;
    color: #cbd5e0;
  }

  .filter-tags button.active {
    background: #667eea;
    color: white;
  }

  .lab-card {
    background: #2d3748;
    border-color: #4a5568;
  }

  .lab-card h3 {
    color: #f7fafc;
  }

  .lab-card p {
    color: #cbd5e0;
  }

  .tag {
    background: #4a5568;
    color: #cbd5e0;
  }

  .labs-footer {
    background: #2d3748;
  }

  .labs-footer p {
    color: #cbd5e0;
  }
}
</style>
