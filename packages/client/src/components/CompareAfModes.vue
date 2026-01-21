<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50"
  >
    <div
      class="absolute inset-0 bg-black/40"
      @click="$emit('update:modelValue', false)"
    />
    <div class="absolute inset-0 sm:inset-y-6 sm:inset-x-6 bg-white rounded-xl shadow-xl flex flex-col">
      <div class="px-4 py-3 border-b flex items-center justify-between">
        <h3 class="text-lg font-semibold">
          Compare Adaptive-Feed Modes
        </h3>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 border rounded bg-orange-50"
            @click="batchExportFromModal"
          >
            Batch (ZIP)
          </button>
          <button
            class="px-3 py-1 border rounded"
            @click="$emit('update:modelValue', false)"
          >
            Close
          </button>
        </div>
      </div>

      <div class="grow grid md:grid-cols-3 gap-0">
        <PreviewPane
          title="FEED_HINT comments"
          mode="comment"
          :text="commentText"
          @make-default="makeDefault"
        />
        <PreviewPane
          title="Inline F overrides"
          mode="inline_f"
          :text="inlineText"
          @make-default="makeDefault"
        />
        <PreviewPane
          title="M-code wrapper"
          mode="mcode"
          :text="mcodeText"
          @make-default="makeDefault"
        />
      </div>

      <div class="px-4 py-2 text-xs text-gray-500 border-t flex items-center justify-between">
        <div>FEED_HINT regions are highlighted. Use Export after choosing your preferred mode.</div>
        <div class="text-right text-xs text-gray-400">
          Tip: Use Copy on any pane to copy NC to clipboard.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import PreviewPane from './PreviewPane.vue'

const props = defineProps<{
  modelValue: boolean,
  requestBody: any
}>()
const emit = defineEmits<{(e:'update:modelValue', v:boolean):void; (e:'make-default', mode:string):void}>()

const commentText = ref('')
const inlineText = ref('')
const mcodeText = ref('')

watch(()=>props.modelValue, (v: boolean) => { if (v) refresh() })

async function refresh(){
  commentText.value = inlineText.value = mcodeText.value = 'Loading…'
  const base = JSON.parse(JSON.stringify(props.requestBody || {}))
  async function fetchNC(mode:'comment'|'inline_f'|'mcode'){
    const body = { ...base, adaptive_feed_override: { mode } }
    const r = await fetch('/api/cam/pocket/adaptive/gcode', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
    })
    return await r.text()
  }
  [commentText.value, inlineText.value, mcodeText.value] = await Promise.all([
    fetchNC('comment'), fetchNC('inline_f'), fetchNC('mcode')
  ])
}

function makeDefault(mode: string){
  // forward to parent so they can persist per-post
  emit('make-default', mode)
}

async function batchExportFromModal(){
  const body = JSON.parse(JSON.stringify(props.requestBody || {}))
  
  try {
    const r = await fetch('/api/cam/pocket/adaptive/batch_export', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    const postId = body.post_id || 'POST'
    a.download = `ToolBox_MultiMode_${postId}.zip`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (err) {
    console.error('Batch export failed:', err)
    alert('Failed to batch export: ' + err)
  }
}
</script>

<style scoped>
/* simple sizing tweaks */
.preview-pane { }
</style>
