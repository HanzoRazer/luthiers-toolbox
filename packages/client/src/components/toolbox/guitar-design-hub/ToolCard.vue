<script setup lang="ts">
/**
 * ToolCard - Clickable tool card for Guitar Design Hub
 * Extracted from GuitarDesignHub.vue
 */
defineProps<{
  icon: string
  title: string
  description: string
  badge?: string
}>()

const emit = defineEmits<{
  select: []
}>()
</script>

<template>
  <div
    class="tool-card"
    @click="emit('select')"
  >
    <div class="tool-icon">
      {{ icon }}
    </div>
    <h4>{{ title }}</h4>
    <p>{{ description }}</p>
    <span
      v-if="badge"
      class="tool-badge"
    >
      {{ badge }}
    </span>
  </div>
</template>

<style scoped>
.tool-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.75rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 6px rgba(0,0,0,0.1);
  position: relative;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.2);
}

.tool-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  text-align: center;
}

.tool-card h4 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.tool-card p {
  font-size: 0.9rem;
  opacity: 0.9;
  text-align: center;
  line-height: 1.4;
  margin: 0;
}

.tool-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(255,255,255,0.3);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>
