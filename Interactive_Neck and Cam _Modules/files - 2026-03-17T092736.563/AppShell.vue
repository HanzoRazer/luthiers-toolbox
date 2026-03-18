<script setup lang="ts">
import { ref } from 'vue'
import WorkspaceView  from '@/views/WorkspaceView.vue'
import ImportView     from '@/views/ImportView.vue'
import ParametricView from '@/views/ParametricView.vue'

const activeTab = ref<'workspace' | 'import' | 'parametric'>('workspace')
const toast = ref({ msg: '', visible: false, t: 0 as ReturnType<typeof setTimeout> })

function showToast(msg: string) {
  toast.value.msg = msg; toast.value.visible = true
  clearTimeout(toast.value.t)
  toast.value.t = setTimeout(() => toast.value.visible = false, 2800)
}
function navigate(tab: string) { activeTab.value = tab as typeof activeTab.value }
</script>

<template>
  <div class="shell">
    <nav class="shell-nav">
      <div class="brand">Production<em>Shop</em></div>
      <div class="nav-tabs">
        <button v-for="tab in ['workspace','import','parametric'] as const" :key="tab"
          class="nav-tab" :class="{ on: activeTab === tab }" @click="activeTab = tab">
          <span class="tab-dot"></span>
          {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
          <span v-if="tab === 'parametric'" class="pro-badge">Pro</span>
        </button>
      </div>
    </nav>
    <main class="shell-main">
      <WorkspaceView  v-show="activeTab === 'workspace'"  @toast="showToast" />
      <ImportView     v-show="activeTab === 'import'"     @navigate="navigate" @toast="showToast" />
      <ParametricView v-show="activeTab === 'parametric'" @navigate="navigate" @toast="showToast" />
    </main>
    <Transition name="toast">
      <div v-if="toast.visible" class="toast">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.shell { display:flex; flex-direction:column; height:100vh; background:var(--w0); color:var(--v0); }
.shell-nav { height:40px; background:var(--w1); border-bottom:1px solid var(--w3); display:flex; align-items:center; padding:0 14px; flex-shrink:0; }
.brand { font-family:var(--serif); font-size:14px; font-style:italic; color:var(--v1); margin-right:18px; white-space:nowrap; }
.brand em { color:var(--br2); font-style:normal; }
.nav-tabs { display:flex; align-items:stretch; }
.nav-tab { display:flex; align-items:center; gap:7px; padding:0 13px; height:40px; cursor:pointer; border:none; background:none; border-bottom:2px solid transparent; font-family:var(--mono); font-size:10px; letter-spacing:.6px; text-transform:uppercase; color:var(--dim); transition:all .12s; }
.nav-tab:hover { color:var(--v1); } .nav-tab.on { color:var(--br2); border-bottom-color:var(--br); }
.tab-dot { width:6px; height:6px; border-radius:50%; background:var(--w4); flex-shrink:0; }
.nav-tab.on .tab-dot { background:var(--br); }
.pro-badge { font-size:7px; padding:1px 5px; background:rgba(184,150,46,.1); border:1px solid var(--br3); border-radius:2px; color:var(--br); letter-spacing:.8px; }
.shell-main { flex:1; overflow:hidden; }
.toast { position:fixed; top:48px; right:18px; z-index:9999; background:var(--w1); border:1px solid var(--br3); border-radius:4px; padding:9px 14px; font-size:10px; color:var(--br2); font-family:var(--mono); pointer-events:none; }
.toast-enter-active,.toast-leave-active { transition:all .2s ease; }
.toast-enter-from,.toast-leave-to { opacity:0; transform:translateY(-8px); }
</style>
