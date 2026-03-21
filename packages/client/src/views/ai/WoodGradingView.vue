<script setup lang="ts">
/**
 * WoodGradingView - Visual Wood Assessment (E-4)
 * Upload photos for AI visual analysis of wood characteristics.
 *
 * NOTE: Visual assessment only. For acoustic grading (density, stiffness,
 * Q factor), use the Tap Tone Analyzer at /tools/audio-analyzer.
 *
 * Connected to API endpoint:
 *   POST /api/ai/wood-grading/analyze
 */
import { ref } from "vue"
import { RouterLink } from "vue-router"

const selectedFile = ref<File | null>(null)
const previewUrl = ref<string>("")
const isAnalyzing = ref(false)
const errorMessage = ref<string | null>(null)
const analysisResult = ref<{
  observations: string
  grain_spacing_estimate: string
  grain_straightness: string
  figure_type: string
  color_uniformity: string
  surface_anomalies: string[]
  confidence: string
} | null>(null)

const recentAnalyses = ref([
  { id: 1, filename: "sitka_top_001.jpg", figure: "Plain", date: "2026-03-06", species: "Sitka Spruce" },
  { id: 2, filename: "rosewood_set_12.jpg", figure: "Quilted", date: "2026-03-05", species: "Indian Rosewood" },
  { id: 3, filename: "maple_neck_03.jpg", figure: "Flamed", date: "2026-03-05", species: "Hard Maple" },
])

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    analysisResult.value = null
    errorMessage.value = null
  }
}

async function analyzeWood() {
  if (!selectedFile.value) return

  isAnalyzing.value = true
  errorMessage.value = null

  try {
    // Convert file to base64
    const reader = new FileReader()
    const base64Promise = new Promise<string>((resolve, reject) => {
      reader.onload = () => {
        const result = reader.result as string
        // Remove data URL prefix to get raw base64
        const base64 = result.split(",")[1]
        resolve(base64)
      }
      reader.onerror = reject
    })
    reader.readAsDataURL(selectedFile.value)
    const imageBase64 = await base64Promise

    // Call real API endpoint
    const response = await fetch("/api/ai/wood-grading/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: imageBase64 }),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Analysis failed" }))
      throw new Error(err.detail || "Analysis failed")
    }

    const data = await response.json()
    analysisResult.value = {
      observations: data.observations,
      grain_spacing_estimate: data.grain_spacing_estimate,
      grain_straightness: data.grain_straightness,
      figure_type: data.figure_type,
      color_uniformity: data.color_uniformity,
      surface_anomalies: data.surface_anomalies || [],
      confidence: data.confidence,
    }
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Analysis failed"
    analysisResult.value = null
  } finally {
    isAnalyzing.value = false
  }
}
</script>

<template>
  <div class="wood-grading-view">
    <div class="header">
      <h1>Visual Wood Assessment</h1>
      <p class="subtitle">Upload photos for AI visual analysis of wood characteristics</p>
    </div>

    <!-- Tap Tone Callout -->
    <div class="tap-tone-callout">
      <span class="callout-icon">&#127925;</span>
      <div class="callout-content">
        <strong>For acoustic grading (density, stiffness, Q factor), use the Tap Tone Analyzer</strong>
        <p>Visual analysis cannot measure acoustic properties. Physical tap testing is required for tonewood grading.</p>
        <RouterLink to="/tools/audio-analyzer" class="callout-link">
          Open Tap Tone Analyzer &rarr;
        </RouterLink>
      </div>
    </div>

    <div class="content">
      <div class="panel upload-panel">
        <h3>Upload Image</h3>
        <div
          class="upload-zone"
          :class="{ 'has-image': previewUrl }"
          @click="($refs.fileInput as HTMLInputElement).click()"
        >
          <input type="file" ref="fileInput" accept="image/*" @change="handleFileSelect" hidden />
          <img v-if="previewUrl" :src="previewUrl" alt="Wood preview" class="preview-image" />
          <div v-else class="upload-placeholder">
            <span class="upload-icon">&#128247;</span>
            <p>Click to upload wood photo</p>
            <p class="hint">JPG, PNG up to 10MB</p>
          </div>
        </div>

        <div class="guidelines">
          <h4>Photo Guidelines</h4>
          <ul>
            <li>Good lighting, avoid shadows</li>
            <li>Include the entire piece</li>
            <li>Show grain pattern clearly</li>
            <li>Include a size reference if possible</li>
          </ul>
        </div>

        <button
          class="btn btn-primary btn-large"
          @click="analyzeWood"
          :disabled="!selectedFile || isAnalyzing"
        >
          {{ isAnalyzing ? "Analyzing..." : "Analyze Wood" }}
        </button>
      </div>

      <div class="panel results-panel">
        <h3>Visual Observations</h3>

        <div v-if="isAnalyzing" class="analyzing">
          <div class="spinner"></div>
          <p>AI is analyzing the wood surface...</p>
        </div>

        <div v-else-if="errorMessage" class="error-result">
          <span class="error-icon">&#9888;</span>
          <p>{{ errorMessage }}</p>
        </div>

        <div v-else-if="analysisResult" class="analysis-result">
          <div class="observation-summary">
            <p class="observations-text">{{ analysisResult.observations }}</p>
            <span class="confidence-badge">{{ analysisResult.confidence }} confidence</span>
          </div>

          <div class="result-grid">
            <div class="result-item">
              <span class="label">Grain Spacing</span>
              <span class="value">{{ analysisResult.grain_spacing_estimate }}</span>
            </div>
            <div class="result-item">
              <span class="label">Grain Straightness</span>
              <span class="value">{{ analysisResult.grain_straightness }}</span>
            </div>
            <div class="result-item">
              <span class="label">Figure Type</span>
              <span class="value">{{ analysisResult.figure_type }}</span>
            </div>
            <div class="result-item">
              <span class="label">Color Uniformity</span>
              <span class="value">{{ analysisResult.color_uniformity }}</span>
            </div>
          </div>

          <div v-if="analysisResult.surface_anomalies.length" class="result-section">
            <h4>Surface Observations</h4>
            <ul>
              <li v-for="anomaly in analysisResult.surface_anomalies" :key="anomaly">{{ anomaly }}</li>
            </ul>
          </div>

          <div class="result-actions">
            <button class="btn btn-secondary">Save to Library</button>
            <button class="btn btn-secondary">Export Report</button>
          </div>
        </div>

        <div v-else class="no-result">
          <span class="icon">&#127794;</span>
          <p>Upload a photo to begin visual analysis</p>
        </div>
      </div>

      <div class="panel history-panel">
        <h3>Recent Analyses</h3>
        <div class="history-list">
          <div v-for="item in recentAnalyses" :key="item.id" class="history-item">
            <div class="history-info">
              <span class="filename">{{ item.filename }}</span>
              <span class="species">{{ item.species }}</span>
            </div>
            <div class="history-meta">
              <span class="history-figure">{{ item.figure }}</span>
              <span class="date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wood-grading-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 1rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.tap-tone-callout {
  max-width: 1400px;
  margin: 0 auto 2rem;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, #1e3a5f 0%, #1a2f4a 100%);
  border-radius: 0.75rem;
  border-left: 4px solid #60a5fa;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}
.callout-icon { font-size: 2rem; flex-shrink: 0; }
.callout-content { flex: 1; }
.callout-content strong { display: block; color: #93c5fd; margin-bottom: 0.5rem; }
.callout-content p { color: #94a3b8; font-size: 0.875rem; margin: 0 0 0.75rem; }
.callout-link {
  display: inline-block;
  color: #60a5fa;
  font-weight: 600;
  text-decoration: none;
  padding: 0.5rem 1rem;
  background: rgba(96, 165, 250, 0.1);
  border-radius: 0.375rem;
  transition: background 0.2s;
}
.callout-link:hover { background: rgba(96, 165, 250, 0.2); }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 300px 1fr 280px; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h4 { font-size: 0.75rem; color: #888; margin: 1rem 0 0.5rem; }

.upload-zone { border: 2px dashed #333; border-radius: 0.5rem; padding: 2rem; text-align: center; cursor: pointer; min-height: 200px; display: flex; align-items: center; justify-content: center; }
.upload-zone:hover { border-color: #60a5fa; }
.upload-zone.has-image { padding: 0; border-style: solid; }
.preview-image { width: 100%; height: auto; border-radius: 0.375rem; }
.upload-placeholder .upload-icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.upload-placeholder .hint { font-size: 0.75rem; color: #666; }

.guidelines { margin: 1rem 0; }
.guidelines ul { padding-left: 1.5rem; margin: 0; }
.guidelines li { font-size: 0.875rem; color: #888; margin: 0.25rem 0; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-large { width: 100%; padding: 1rem; font-size: 1rem; margin-top: 1rem; }

.analyzing { text-align: center; padding: 3rem; }
.spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }

.no-result { text-align: center; padding: 3rem; color: #666; }
.no-result .icon { font-size: 3rem; display: block; margin-bottom: 1rem; }

.error-result { text-align: center; padding: 2rem; color: #f87171; }
.error-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.observation-summary { background: #262626; border-radius: 0.5rem; padding: 1.25rem; margin-bottom: 1.5rem; }
.observations-text { font-size: 0.9375rem; line-height: 1.6; margin: 0 0 0.75rem; }
.confidence-badge { display: inline-block; font-size: 0.75rem; color: #60a5fa; background: rgba(96, 165, 250, 0.1); padding: 0.25rem 0.75rem; border-radius: 1rem; }

.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
.result-item { background: #262626; padding: 1rem; border-radius: 0.5rem; }
.result-item .label { display: block; font-size: 0.75rem; color: #888; margin-bottom: 0.25rem; }
.result-item .value { display: block; font-weight: 600; text-transform: capitalize; }

.result-section { margin-bottom: 1.5rem; }
.result-section ul { padding-left: 1.5rem; margin: 0; }
.result-section li { font-size: 0.875rem; margin: 0.5rem 0; color: #ccc; }

.result-actions { display: flex; gap: 0.75rem; }
.result-actions .btn { flex: 1; }

.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; padding: 0.75rem; background: #262626; border-radius: 0.375rem; }
.history-info { display: flex; flex-direction: column; }
.filename { font-size: 0.875rem; font-weight: 500; }
.species { font-size: 0.75rem; color: #888; }
.history-meta { text-align: right; }
.history-figure { display: block; font-weight: 600; color: #60a5fa; }
.date { font-size: 0.75rem; color: #888; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
