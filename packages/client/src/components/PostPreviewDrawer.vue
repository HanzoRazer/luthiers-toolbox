<template>
  <div
    v-if="open"
    class="fixed inset-0 z-40"
  >
    <div
      class="absolute inset-0 bg-black/30"
      @click="close"
    />

    <div class="absolute right-0 top-0 h-full w-full sm:w-[28rem] bg-white shadow-xl p-4 overflow-auto">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-lg font-semibold">
          Post Preview — {{ postId }}
        </h3>
        <button
          class="px-3 py-1 border rounded"
          @click="close"
        >
          Close
        </button>
      </div>

      <div class="space-y-3">
        <div>
          <div class="text-sm font-semibold mb-1">
            Header
          </div>
          <pre class="text-xs bg-slate-50 p-2 rounded">{{ header.join('\n') || '—' }}</pre>
        </div>
        <div>
          <div class="text-sm font-semibold mb-1">
            Footer
          </div>
          <pre class="text-xs bg-slate-50 p-2 rounded">{{ footer.join('\n') || '—' }}</pre>
        </div>
        <div>
          <div class="text-sm font-semibold mb-1">
            Program Preview (first 20 lines)
          </div>
          <pre class="text-xs bg-slate-50 p-2 rounded">{{ previewText }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  postId: string | null
  gcode: string
  units: 'mm' | 'inch'
}>()
const emit = defineEmits<{ (e:'update:modelValue', v:boolean): void }>()

const open = ref(false)
const header = ref<string[]>([])
const footer = ref<string[]>([])
const previewText = ref('')

function close(){ emit('update:modelValue', false) }

watch(() => props.modelValue, v => { open.value = v; if (v) refresh() }, { immediate: true })

async function refresh(){
  header.value = []; footer.value = []; previewText.value = ''
  if (!props.postId) return

  // fetch post catalog (assumes /tooling/posts returns headers/footers)
  const cat = await api('/api/tooling/posts').then(r => r.json()) as any[]
  const post = (cat || []).find(x => (x.id || x.name) === props.postId)
  header.value = (post?.header || []).slice(0, 20)
  footer.value = (post?.footer || []).slice(0, 20)

  // render sample NC via export_gcode (uses current gcode + units + post)
  const body = JSON.stringify({
    gcode: props.gcode || 'G90\nM30\n',
    units: props.units === 'inch' ? 'inch' : 'mm',
    post_id: props.postId
  })
  const nc = await api('/api/geometry/export_gcode', { method:'POST', headers:{'Content-Type':'application/json'}, body })
                .then(r => r.text())
  previewText.value = (nc.split('\n').slice(0, 20)).join('\n')
}
</script>
