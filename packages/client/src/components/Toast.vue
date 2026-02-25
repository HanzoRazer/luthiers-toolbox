<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { DEFAULT_TOAST_MS } from '@/constants/timing'
const visible = ref(false)
const msg = ref('')
let hideTimer: number | null = null
function show(m: string, timeout = DEFAULT_TOAST_MS) {
  msg.value = m
  visible.value = true
  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = window.setTimeout(() => (visible.value = false), timeout)
}
onBeforeUnmount(() => { if (hideTimer) clearTimeout(hideTimer) })
defineExpose({ show })
</script>
<template>
  <div
    v-show="visible"
    class="fixed bottom-4 right-4 bg-black text-white text-sm px-4 py-2 rounded-xl shadow-lg max-w-sm"
  >
    {{ msg }}
  </div>
</template>
