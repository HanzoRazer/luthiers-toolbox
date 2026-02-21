<template>
  <div class="traditional-section">
    <div class="content-grid">
      <!-- Pattern Catalog -->
      <div class="catalog-panel">
        <h2>Pattern Catalog</h2>

        <div class="category-filter">
          <Button
            label="All"
            :class="{ 'p-button-outlined': selectedCategory !== null }"
            size="small"
            @click="emit('update:selectedCategory', null)"
          />
          <Button
            v-for="cat in categories"
            :key="cat"
            :label="cat"
            :class="{ 'p-button-outlined': selectedCategory !== cat }"
            size="small"
            @click="emit('update:selectedCategory', cat)"
          />
        </div>

        <div class="pattern-list">
          <div
            v-for="pattern in filteredPatterns"
            :key="pattern.id"
            class="pattern-card"
            :class="{ selected: selectedPattern?.id === pattern.id }"
            @click="emit('select-pattern', pattern)"
          >
            <div class="pattern-header">
              <strong>{{ pattern.name }}</strong>
              <span class="badge">{{ pattern.category }}</span>
            </div>
            <div class="pattern-info">
              <span>{{ pattern.rows }}×{{ pattern.columns }}</span>
              <span>{{ pattern.materials.join(", ") }}</span>
            </div>
            <div
              v-if="pattern.notes"
              class="pattern-notes"
            >
              {{ pattern.notes }}
            </div>
          </div>
        </div>
      </div>

      <!-- Generation Panel -->
      <div class="generation-panel">
        <h2>Generate Pattern</h2>

        <div
          v-if="selectedPattern"
          class="selected-pattern-info"
        >
          <h3>{{ selectedPattern.name }}</h3>
          <p>{{ selectedPattern.notes }}</p>
        </div>

        <div class="settings-group">
          <div class="field">
            <label>Chip Length (mm)</label>
            <InputNumber
              :model-value="chipLength"
              :min="0.5"
              :max="5"
              :step="0.1"
              @update:model-value="emit('update:chipLength', $event)"
            />
          </div>

          <div class="field">
            <label>Waste Factor (%)</label>
            <InputNumber
              :model-value="wasteFactor"
              :min="0"
              :max="0.5"
              :step="0.05"
              :min-fraction-digits="2"
              @update:model-value="emit('update:wasteFactor', $event)"
            />
          </div>
        </div>

        <Button
          label="Generate Traditional Pattern"
          icon="pi pi-cog"
          :disabled="!selectedPattern || isLoading"
          :loading="isLoading"
          class="w-full"
          @click="emit('generate')"
        />

        <!-- Results -->
        <div
          v-if="result"
          class="results-section"
        >
          <h3>Results</h3>

          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">
                Width
              </div>
              <div class="stat-value">
                {{ result.pattern_dimensions.width_mm.toFixed(1) }} mm
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Height
              </div>
              <div class="stat-value">
                {{ result.pattern_dimensions.height_mm.toFixed(1) }} mm
              </div>
            </div>
          </div>

          <div class="material-totals">
            <h4>Material Totals (strips needed)</h4>
            <div
              v-for="(count, material) in result.material_totals"
              :key="material"
              class="material-row"
            >
              <span>{{ material }}:</span>
              <strong>{{ count }} strips</strong>
            </div>
          </div>

          <div class="cut-list">
            <h4>Cut List (with waste)</h4>
            <div
              v-for="(item, idx) in result.cut_list"
              :key="idx"
              class="cut-item"
            >
              {{ item.material }}: {{ item.count }}× @ {{ item.width_mm }}×{{
                item.length_mm
              }} mm
            </div>
          </div>

          <div class="assembly-instructions">
            <h4>Assembly Instructions</h4>
            <ol>
              <li
                v-for="instr in result.assembly_instructions"
                :key="instr.step"
              >
                {{ instr.action }}
              </li>
            </ol>
          </div>

          <Button
            label="Download JSON"
            icon="pi pi-download"
            class="w-full"
            @click="emit('download-json', result, `${selectedPattern.id}_traditional.json`)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  selectedPattern: any | null
  selectedCategory: string | null
  categories: string[]
  filteredPatterns: any[]
  chipLength: number
  wasteFactor: number
  result: any | null
  isLoading: boolean
}>()

const emit = defineEmits<{
  'update:selectedCategory': [value: string | null]
  'update:chipLength': [value: number]
  'update:wasteFactor': [value: number]
  'select-pattern': [pattern: any]
  'generate': []
  'download-json': [data: any, filename: string]
}>()
</script>

<style scoped>
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.catalog-panel,
.generation-panel {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.catalog-panel h2,
.generation-panel h2 {
  margin-top: 0;
  font-size: 1.5rem;
}

.category-filter {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.pattern-list {
  max-height: 600px;
  overflow-y: auto;
}

.pattern-card {
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.pattern-card:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.pattern-card.selected {
  background: #e7f3ff;
  border-color: #007bff;
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.badge {
  background: #6c757d;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.pattern-info {
  display: flex;
  gap: 1rem;
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.pattern-notes {
  font-size: 0.85rem;
  color: #495057;
  font-style: italic;
}

.settings-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}

.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.stat-card {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #495057;
}

.material-totals,
.cut-list,
.assembly-instructions {
  margin: 1.5rem 0;
}

.material-totals h4,
.cut-list h4,
.assembly-instructions h4 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.material-row,
.cut-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #f8f9fa;
  margin-bottom: 0.25rem;
  border-radius: 4px;
}

.w-full {
  width: 100%;
}
</style>
