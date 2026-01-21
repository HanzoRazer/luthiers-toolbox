<template>
  <nav
    class="breadcrumbs"
    aria-label="Breadcrumb"
  >
    <ol>
      <li>
        <router-link to="/">
          🏠 Home
        </router-link>
      </li>
      <li
        v-for="(crumb, index) in breadcrumbs"
        :key="index"
      >
        <span class="separator">/</span>
        <router-link
          v-if="crumb.to && index < breadcrumbs.length - 1"
          :to="crumb.to"
        >
          {{ crumb.label }}
        </router-link>
        <span
          v-else
          class="current"
        >{{ crumb.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

interface Breadcrumb {
  label: string
  to?: string
}

const breadcrumbs = computed(() => {
  const crumbs: Breadcrumb[] = []
  const pathSegments = route.path.split('/').filter(segment => segment)
  
  // Build breadcrumbs from route meta or path segments
  let currentPath = ''
  
  for (const segment of pathSegments) {
    currentPath += `/${segment}`
    
    // Try to get label from route meta
    const matchedRoute = route.matched.find(r => r.path === currentPath)
    const label = matchedRoute?.meta?.title as string || formatSegment(segment)
    
    crumbs.push({
      label,
      to: currentPath
    })
  }
  
  return crumbs
})

function formatSegment(segment: string): string {
  // Convert kebab-case to Title Case
  return segment
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.breadcrumbs {
  padding: 0.75rem 1rem;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.95rem;
}

.breadcrumbs ol {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumbs li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumbs a {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumbs a:hover {
  color: #764ba2;
  text-decoration: underline;
}

.breadcrumbs .current {
  color: #2d3748;
  font-weight: 600;
}

.separator {
  color: #cbd5e0;
  user-select: none;
}

@media (prefers-color-scheme: dark) {
  .breadcrumbs {
    background: #2d3748;
    border-bottom-color: #4a5568;
  }

  .breadcrumbs a {
    color: #90cdf4;
  }

  .breadcrumbs a:hover {
    color: #63b3ed;
  }

  .breadcrumbs .current {
    color: #f7fafc;
  }

  .separator {
    color: #718096;
  }
}

@media (max-width: 768px) {
  .breadcrumbs {
    font-size: 0.85rem;
    padding: 0.5rem;
  }
}
</style>
