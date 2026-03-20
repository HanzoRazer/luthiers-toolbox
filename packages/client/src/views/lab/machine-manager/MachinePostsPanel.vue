<script setup lang="ts">
/**
 * Post-processors listing (read-only from API).
 */
import { ref, onMounted } from 'vue'
import { POSTS_API, type Post } from './machineManagerTypes'

const emit = defineEmits<{
  error: [message: string]
}>()

const posts = ref<Post[]>([])
const isLoadingPosts = ref(false)

onMounted(() => {
  void loadPosts()
})

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

</script>

<template>
  <section class="panel posts-panel">
    <h2>Post-Processors</h2>
    <div v-if="isLoadingPosts" class="loading">Loading posts...</div>
    <div v-else class="post-list">
      <div v-for="post in posts" :key="post.id" class="post-item">
        <span class="post-name">{{ post.name }}</span>
        <span v-if="post.builtin" class="post-badge">Built-in</span>
        <span v-else class="post-badge custom">Custom</span>
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
  margin-bottom: 1rem;
}

.loading {
  color: #64748b;
  padding: 2rem;
  text-align: center;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.post-item {
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

.post-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
  background: #e2e8f0;
  color: #64748b;
  border-radius: 1rem;
  text-transform: uppercase;
}

.post-badge.custom {
  background: #dbeafe;
  color: #2563eb;
}
</style>
