<template>
  <div class="p-3 border rounded space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-base font-semibold">
        Post-Processors
      </h3>
      <button
        class="px-3 py-1 border rounded"
        @click="resetToDefaults"
      >
        Reset
      </button>
    </div>

    <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-2">
      <label
        v-for="p in posts"
        :key="p.id"
        class="flex items-center gap-2 border rounded px-2 py-1"
      >
        <input
          v-model="selectedIds"
          type="checkbox"
          :value="p.id"
          @change="persist"
        >
        <span class="font-medium">{{ p.id }}</span>
        <span class="text-xs text-gray-500 truncate">· {{ p.title || p.id }}</span>
        <button
          class="ml-auto text-xs underline"
          @click.prevent="$emit('preview', p.id)"
        >Preview</button>
      </label>
    </div>

    <div class="text-sm text-gray-600">
      Selected: <b>{{ selectedIds.join(', ') || '—' }}</b>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

type PostInfo = { id: string; title?: string }

const STORAGE_KEY = 'toolbox.selectedPosts'
const posts = ref<PostInfo[]>([])
const selectedIds = ref<string[]>([])

async function loadPosts(){
  // Expecting `/tooling/posts` → [{id,title,header,footer}, ...]
  const r = await fetch('/api/tooling/posts')
  const arr = await r.json() as any[]
  posts.value = (arr || []).map(x => ({ id: x.id || x.name || 'POST', title: x.title || x.id }))
  // seed from storage
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) selectedIds.value = JSON.parse(saved)
  else selectedIds.value = posts.value.slice(0, 1).map(p => p.id) // pick first by default
}

function persist(){
  localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedIds.value))
  // inform parent
  emit('update:modelValue', selectedIds.value)
}

function resetToDefaults(){
  selectedIds.value = posts.value.slice(0, 1).map(p => p.id)
  persist()
}

const emit = defineEmits<{
  (e: 'update:modelValue', v: string[]): void
  (e: 'preview', id: string): void
}>()

onMounted(loadPosts)
watch(selectedIds, persist, { deep: true })
</script>
