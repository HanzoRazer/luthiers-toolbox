<template>
  <div class="material-palette">
    <div class="palette-header">
      <h3>🪵 Wood Species</h3>
      <button class="btn-small" @click="showAll = !showAll">
        {{ showAll ? 'Show Common' : 'Show All' }}
      </button>
    </div>

    <div class="material-grid">
      <button
        v-for="wood in displayedWoods"
        :key="wood.id"
        :class="['material-swatch', { active: selectedMaterial === wood.id }]"
        :style="{ background: wood.color, color: wood.textColor }"
        @click="selectMaterial(wood.id)"
        :title="`${wood.name} - ${wood.availability}`"
      >
        <div class="swatch-name">{{ wood.name }}</div>
        <div class="swatch-grain" :style="{ opacity: wood.grain === 'figured' ? 0.3 : 0.1 }">
          {{ wood.grain === 'figured' ? '≈≈≈' : '|||' }}
        </div>
      </button>
    </div>

    <div class="material-info" v-if="selectedWoodInfo">
      <div class="info-row">
        <strong>{{ selectedWoodInfo.name }}</strong>
        <span class="badge" :class="`badge-${selectedWoodInfo.availability}`">
          {{ selectedWoodInfo.availability }}
        </span>
      </div>
      <div class="info-row">
        <span>Grain: {{ selectedWoodInfo.grain }}</span>
        <span>Width: {{ stripWidth }}mm</span>
      </div>
      <div class="info-row small">
        <span>{{ selectedWoodInfo.supplier }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface WoodSpecies {
  id: string
  name: string
  color: string
  textColor: string
  grain: 'straight' | 'wavy' | 'figured'
  availability: 'common' | 'specialty' | 'exotic'
  supplier: string
}

const props = defineProps<{
  selectedMaterial?: string
  stripWidth?: number
}>()

const emit = defineEmits<{
  materialSelected: [materialId: string]
}>()

const showAll = ref(false)

const woods: WoodSpecies[] = [
  // Common woods
  { id: 'maple', name: 'Maple', color: '#F5E6D3', textColor: '#333', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { id: 'walnut', name: 'Walnut', color: '#5C4033', textColor: '#fff', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { id: 'ebony', name: 'Ebony', color: '#1a1a1a', textColor: '#fff', grain: 'straight', availability: 'specialty', supplier: 'LMI' },
  { id: 'rosewood', name: 'Rosewood', color: '#3E2723', textColor: '#fff', grain: 'wavy', availability: 'common', supplier: 'StewMac' },
  
  // Specialty woods
  { id: 'maple-figured', name: 'Maple (Figured)', color: '#F5E6D3', textColor: '#333', grain: 'figured', availability: 'specialty', supplier: 'LMI' },
  { id: 'mahogany', name: 'Mahogany', color: '#6B4423', textColor: '#fff', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { id: 'cherry', name: 'Cherry', color: '#8B4513', textColor: '#fff', grain: 'straight', availability: 'common', supplier: 'StewMac' },
  { id: 'wenge', name: 'Wenge', color: '#2B1810', textColor: '#fff', grain: 'straight', availability: 'specialty', supplier: 'LMI' },
  
  // Exotic/colored woods
  { id: 'bloodwood', name: 'Bloodwood', color: '#8B0000', textColor: '#fff', grain: 'straight', availability: 'exotic', supplier: 'LMI' },
  { id: 'padauk', name: 'Padauk', color: '#D2691E', textColor: '#fff', grain: 'straight', availability: 'specialty', supplier: 'LMI' },
  { id: 'purpleheart', name: 'Purpleheart', color: '#6A0DAD', textColor: '#fff', grain: 'straight', availability: 'exotic', supplier: 'LMI' },
  { id: 'yellowheart', name: 'Yellowheart', color: '#FFD700', textColor: '#333', grain: 'straight', availability: 'exotic', supplier: 'LMI' }
]

const displayedWoods = computed(() => {
  if (showAll.value) return woods
  return woods.filter(w => w.availability === 'common' || w.id === 'ebony')
})

const selectedWoodInfo = computed(() => {
  return woods.find(w => w.id === props.selectedMaterial)
})

function selectMaterial(materialId: string) {
  emit('materialSelected', materialId)
}
</script>

<style scoped>
.material-palette {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.palette-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.palette-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.btn-small {
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-small:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.5rem;
}

.material-swatch {
  position: relative;
  height: 80px;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.material-swatch:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.material-swatch.active {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.swatch-name {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  z-index: 1;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.swatch-grain {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
  letter-spacing: -0.1em;
  pointer-events: none;
}

.material-info {
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  font-size: 0.875rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row.small {
  font-size: 0.75rem;
  color: #64748b;
}

.badge {
  padding: 0.125rem 0.5rem;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 3px;
  letter-spacing: 0.05em;
}

.badge-common {
  background: #dcfce7;
  color: #166534;
}

.badge-specialty {
  background: #fef3c7;
  color: #92400e;
}

.badge-exotic {
  background: #fce7f3;
  color: #831843;
}
</style>
