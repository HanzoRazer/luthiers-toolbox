<template>
  <div class="border-l first:border-l-0 flex flex-col">
    <div class="px-3 py-2 text-sm font-semibold bg-slate-50 flex items-center gap-2">
      <div class="flex-1">{{ title }}</div>
      <div class="flex items-center gap-2">
        <button class="px-2 py-1 text-xs border rounded" @click="copyText">Copy</button>
        <button class="px-2 py-1 text-xs border rounded bg-green-50" @click="saveThisVersion">Save</button>
        <button class="px-2 py-1 text-xs border rounded" @click="emitMakeDefault">Make default</button>
      </div>
    </div>
    <div class="grow overflow-auto font-mono text-[11.5px] leading-5">
      <table class="w-full">
        <tbody>
          <tr v-for="(ln,i) in lines" :key="i" :class="inHint(i) ? 'bg-yellow-100' : ''">
            <td class="px-2 py-0.5 text-right text-gray-400 w-10 select-none">{{ i+1 }}</td>
            <td class="px-2 py-0.5 whitespace-pre break-words" v-html="esc(ln)"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ title:string, text:string, mode:string }>()
const emit = defineEmits<{(e:'make-default', mode:string):void}>()

const lines = computed(()=> (props.text || '').split(/\r?\n/))
const ranges = computed(()=>{
  const r:number[][] = []; let s=-1
  lines.value.forEach((ln: string, i: number)=>{
    if (/\(FEED_HINT START/i.test(ln)) s=i
    if (/\(FEED_HINT END/i.test(ln)) { if (s>=0) r.push([s,i]); s=-1 }
  })
  return r
})
function inHint(i:number){
  return ranges.value.some(([a,b]: [number, number])=> i>=a && i<=b)
}
function esc(s:string){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function copyText(){
  try { navigator.clipboard.writeText(props.text || '') } catch(e){ console.warn('copy failed', e) }
}

function saveThisVersion(){
  // Download this NC as individual file
  const blob = new Blob([props.text || ''], { type: 'text/plain' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `pocket_${props.mode}_${Date.now()}.nc`
  a.click()
  URL.revokeObjectURL(a.href)
}

function emitMakeDefault(){ emit('make-default', props.mode) }
</script>

<style scoped>
</style>
