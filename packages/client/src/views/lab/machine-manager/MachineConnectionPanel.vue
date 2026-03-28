<script setup lang="ts">
/**
 * CAM pipeline link: default post-processor for the selected machine.
 */
import { ref, onMounted } from 'vue'
import { POSTS_API, type MachineProfile, type Post } from './machineManagerTypes'

defineProps<{
  modelValue: MachineProfile | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: MachineProfile | null]
  error: [message: string]
}>()

const posts = ref<Post[]>([])
const isLoadingPosts = ref(false)

async function loadPosts() {
  isLoadingPosts.value = true
  try {
    const response = await fetch(`${POSTS_API}/`)
    if (response.ok) {
      const data = await response.json()
      posts.value = data.posts || []
    }
  } catch (e: unknown) {
    console.error('Failed to load posts:', e)
    emit('error', 'Failed to load post-processors')
  } finally {
    isLoadingPosts.value = false
  }
}

onMounted(() => {
  void loadPosts()
})
</script>

<template>
  <section class="panel connection-panel">
    <h2>CAM Connection</h2>
    <p class="panel-hint">
      Choose the default post-processor used when this machine is selected in CAM flows.
    </p>
    <div v-if="!modelValue" class="empty-state">
      <p>Select a machine to set its default post</p>
    </div>
    <div v-else>
      <div v-if="isLoadingPosts" class="loading">
        Loading posts...
      </div>
      <div v-else class="form-group">
        <label>Default post-processor</label>
        <select
          :value="modelValue.post_id_default ?? ''"
          @change="emit('update:modelValue', {
            ...modelValue,
            post_id_default: ($event.target as HTMLSelectElement).value || undefined,
          })"
        >
          <option value="">— None —</option>
          <option v-for="p in posts" :key="p.id" :value="p.id">
            {{ p.name }}{{ p.builtin ? ' (built-in)' : '' }}
          </option>
        </select>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.panel-hint {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.loading {
  color: #64748b;
  padding: 1rem 0;
  text-align: center;
  font-size: 0.875rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #94a3b8;
  font-size: 0.875rem;
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

.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}
</style>
