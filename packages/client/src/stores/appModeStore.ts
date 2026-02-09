/**
 * App Mode Store - Controls Quick Cut vs Pro Mode
 * 
 * Quick Cut: Simplified DXF → G-code flow (3 screens)
 * Pro Mode: Full RMOS, governance, analytics, AI advisory
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppModeStore = defineStore('appMode', () => {
  // State
  const proMode = ref<boolean>(localStorage.getItem('appMode.proMode') === 'true')
  
  // Getters
  const isQuickCutMode = computed(() => !proMode.value)
  const isProMode = computed(() => proMode.value)
  
  // Actions
  function toggleProMode() {
    proMode.value = !proMode.value
    localStorage.setItem('appMode.proMode', String(proMode.value))
  }
  
  function setProMode(value: boolean) {
    proMode.value = value
    localStorage.setItem('appMode.proMode', String(value))
  }
  
  return {
    proMode,
    isQuickCutMode,
    isProMode,
    toggleProMode,
    setProMode
  }
})
