<script setup lang="ts">
import { ref } from 'vue'
import { DEFAULT_TOAST_MS } from '@/constants/timing'
const visible = ref(false)
const msg = ref('')
function show(m: string, timeout=DEFAULT_TOAST_MS){ msg.value = m; visible.value = true; window.setTimeout(()=>visible.value=false, timeout) }
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
