<template>
  <div class="pattern-templates">
    <div class="templates-header">
      <h3>📐 Pattern Templates</h3>
    </div>

    <div class="templates-grid">
      <button
        v-for="template in templates"
        :key="template.id"
        :class="['template-card', { active: selectedTemplate === template.id }]"
        @click="selectTemplate(template.id)"
      >
        <div class="template-preview">
          {{ template.icon }}
        </div>
        <div class="template-name">{{ template.name }}</div>
        <div class="template-desc">{{ template.description }}</div>
      </button>
    </div>

    <div class="template-info" v-if="selectedTemplateInfo">
      <h4>{{ selectedTemplateInfo.name }}</h4>
      <p>{{ selectedTemplateInfo.longDescription }}</p>
      <div class="template-specs">
        <div class="spec-item">
          <strong>Segments:</strong> {{ selectedTemplateInfo.segments }}
        </div>
        <div class="spec-item">
          <strong>Difficulty:</strong> 
          <span :class="`difficulty-${selectedTemplateInfo.difficulty}`">
            {{ selectedTemplateInfo.difficulty }}
          </span>
        </div>
        <div class="spec-item">
          <strong>Strips:</strong> {{ selectedTemplateInfo.strips.length }} types
        </div>
      </div>
      <button class="btn-apply" @click="applyTemplate">
        Apply Template
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface PatternTemplate {
  id: string
  name: string
  icon: string
  description: string
  longDescription: string
  segments: number
  difficulty: 'easy' | 'medium' | 'hard'
  strips: Array<{
    shape: 'rectangle' | 'trapezoid' | 'curve'
    width: number
    angle: number
    material: string
  }>
}

const props = defineProps<{
  selectedTemplate?: string
}>()

const emit = defineEmits<{
  templateSelected: [templateId: string]
  templateApplied: [template: PatternTemplate]
}>()

const templates: PatternTemplate[] = [
  {
    id: 'simple-ring',
    name: 'Simple Ring',
    icon: '⭕',
    description: 'Single contrasting ring',
    longDescription: 'A classic single-ring rosette with alternating light and dark woods. Perfect for beginners.',
    segments: 1,
    difficulty: 'easy',
    strips: [
      { shape: 'rectangle', width: 2.0, angle: 0, material: 'maple' },
      { shape: 'rectangle', width: 1.0, angle: 0, material: 'walnut' }
    ]
  },
  {
    id: 'herringbone',
    name: 'Herringbone',
    icon: '《《',
    description: 'Classic V-pattern',
    longDescription: 'Traditional herringbone pattern with alternating angled strips creating a distinctive chevron effect.',
    segments: 16,
    difficulty: 'medium',
    strips: [
      { shape: 'rectangle', width: 1.0, angle: 45, material: 'maple' },
      { shape: 'rectangle', width: 1.0, angle: -45, material: 'walnut' }
    ]
  },
  {
    id: 'rope',
    name: 'Rope/Twist',
    icon: '🪢',
    description: 'Alternating diagonal strips',
    longDescription: 'Creates a rope or twisted appearance with diagonal strips that spiral around the soundhole.',
    segments: 32,
    difficulty: 'medium',
    strips: [
      { shape: 'trapezoid', width: 0.8, angle: 30, material: 'ebony' },
      { shape: 'trapezoid', width: 0.8, angle: -30, material: 'maple' }
    ]
  },
  {
    id: 'triple-ring',
    name: 'Triple Ring',
    icon: '⊚',
    description: 'Three concentric bands',
    longDescription: 'Three distinct rings with different woods creating a layered, elegant appearance.',
    segments: 3,
    difficulty: 'easy',
    strips: [
      { shape: 'rectangle', width: 1.5, angle: 0, material: 'walnut' },
      { shape: 'rectangle', width: 0.5, angle: 0, material: 'maple' },
      { shape: 'rectangle', width: 2.0, angle: 0, material: 'rosewood' }
    ]
  },
  {
    id: 'celtic-knot',
    name: 'Celtic Knot',
    icon: '☘️',
    description: 'Interwoven pattern',
    longDescription: 'Complex interwoven pattern inspired by Celtic knotwork. Requires precision cutting and assembly.',
    segments: 24,
    difficulty: 'hard',
    strips: [
      { shape: 'curve', width: 0.5, angle: 15, material: 'ebony' },
      { shape: 'curve', width: 0.5, angle: -15, material: 'maple' }
    ]
  },
  {
    id: 'sunburst',
    name: 'Sunburst',
    icon: '☀️',
    description: 'Radiating rays',
    longDescription: 'Rays emanating from the center, alternating light and dark woods for dramatic contrast.',
    segments: 24,
    difficulty: 'medium',
    strips: [
      { shape: 'trapezoid', width: 1.2, angle: 0, material: 'maple' },
      { shape: 'trapezoid', width: 1.2, angle: 0, material: 'walnut' }
    ]
  }
]

const selectedTemplateInfo = computed(() => {
  return templates.find(t => t.id === props.selectedTemplate)
})

function selectTemplate(templateId: string) {
  emit('templateSelected', templateId)
}

function applyTemplate() {
  if (selectedTemplateInfo.value) {
    emit('templateApplied', selectedTemplateInfo.value)
  }
}
</script>

<style scoped>
.pattern-templates {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.templates-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}

.template-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.template-card:hover {
  background: white;
  border-color: #cbd5e1;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.template-card.active {
  background: white;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.template-preview {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  filter: grayscale(30%);
}

.template-card.active .template-preview {
  filter: grayscale(0%);
}

.template-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.template-desc {
  font-size: 0.75rem;
  color: #64748b;
}

.template-info {
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.template-info h4 {
  margin: 0 0 0.5rem;
  color: #1e293b;
  font-size: 1rem;
}

.template-info p {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: #475569;
  line-height: 1.5;
}

.template-specs {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.spec-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.difficulty-easy {
  color: #16a34a;
  font-weight: 600;
}

.difficulty-medium {
  color: #d97706;
  font-weight: 600;
}

.difficulty-hard {
  color: #dc2626;
  font-weight: 600;
}

.btn-apply {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-apply:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
