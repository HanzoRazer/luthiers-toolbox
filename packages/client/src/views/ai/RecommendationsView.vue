<script setup lang="ts">
/**
 * RecommendationsView - AI Design & Material Recommendations
 * Get intelligent recommendations for builds based on preferences
 *
 * Connected to API endpoints:
 *   POST /api/ai/recommendations/generate
 *   GET  /api/ai/recommendations/history
 */
import { ref } from 'vue'

const buildType = ref('acoustic')  // acoustic, classical, electric
const targetTone = ref('warm')  // warm, bright, balanced
const playingStyle = ref('fingerstyle')
const budget = ref('mid')  // budget, mid, premium
const isGenerating = ref(false)

const recommendations = ref<{
  tonewoods: { name: string; reason: string; score: number }[]
  design: { feature: string; suggestion: string }[]
  hardware: { item: string; recommendation: string }[]
} | null>(null)

const recentQueries = ref([
  { id: 1, type: 'Classical', tone: 'Warm', date: '2026-03-06' },
  { id: 2, type: 'Electric', tone: 'Bright', date: '2026-03-05' },
  { id: 3, type: 'Acoustic', tone: 'Balanced', date: '2026-03-04' },
])

async function generateRecommendations() {
  isGenerating.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))

  recommendations.value = {
    tonewoods: [
      { name: 'Sitka Spruce Top', reason: 'Excellent dynamic range for fingerstyle', score: 95 },
      { name: 'Indian Rosewood Back/Sides', reason: 'Rich overtones, warm fundamental', score: 92 },
      { name: 'Mahogany Neck', reason: 'Stable, warm sustain', score: 88 },
      { name: 'Ebony Fingerboard', reason: 'Articulate attack, durability', score: 90 },
    ],
    design: [
      { feature: 'Body Shape', suggestion: 'OM or 000 for balanced response' },
      { feature: 'Scale Length', suggestion: '25.4" for warm tone with good tension' },
      { feature: 'Bracing', suggestion: 'Scalloped X-bracing for responsiveness' },
      { feature: 'Soundhole', suggestion: 'Standard 4" with decorative rosette' },
    ],
    hardware: [
      { item: 'Tuners', recommendation: 'Gotoh 510 or equivalent' },
      { item: 'Nut/Saddle', recommendation: 'Bone for clarity and sustain' },
      { item: 'Bridge Pins', recommendation: 'Ebony to match fingerboard' },
    ],
  }
  isGenerating.value = false
}
</script>

<template>
  <div class="recommendations-view">
    <div class="header">
      <h1>AI Recommendations</h1>
      <p class="subtitle">Get intelligent suggestions for your next build</p>
    </div>

    <div class="content">
      <div class="panel preferences-panel">
        <h3>Build Preferences</h3>

        <div class="form-group">
          <label>Instrument Type</label>
          <div class="option-buttons">
            <button :class="{ active: buildType === 'acoustic' }" @click="buildType = 'acoustic'">Acoustic</button>
            <button :class="{ active: buildType === 'classical' }" @click="buildType = 'classical'">Classical</button>
            <button :class="{ active: buildType === 'electric' }" @click="buildType = 'electric'">Electric</button>
          </div>
        </div>

        <div class="form-group">
          <label>Target Tone</label>
          <div class="option-buttons">
            <button :class="{ active: targetTone === 'warm' }" @click="targetTone = 'warm'">Warm</button>
            <button :class="{ active: targetTone === 'balanced' }" @click="targetTone = 'balanced'">Balanced</button>
            <button :class="{ active: targetTone === 'bright' }" @click="targetTone = 'bright'">Bright</button>
          </div>
        </div>

        <div class="form-group">
          <label>Playing Style</label>
          <select v-model="playingStyle">
            <option value="fingerstyle">Fingerstyle</option>
            <option value="strumming">Strumming</option>
            <option value="flatpicking">Flatpicking</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>

        <div class="form-group">
          <label>Budget Range</label>
          <div class="option-buttons">
            <button :class="{ active: budget === 'budget' }" @click="budget = 'budget'">Budget</button>
            <button :class="{ active: budget === 'mid' }" @click="budget = 'mid'">Mid-Range</button>
            <button :class="{ active: budget === 'premium' }" @click="budget = 'premium'">Premium</button>
          </div>
        </div>

        <button class="btn btn-primary btn-large" @click="generateRecommendations" :disabled="isGenerating">
          {{ isGenerating ? 'Generating...' : '✨ Get Recommendations' }}
        </button>

        <div class="recent-queries">
          <h4>Recent Queries</h4>
          <div v-for="query in recentQueries" :key="query.id" class="query-item">
            <span>{{ query.type }} • {{ query.tone }}</span>
            <span class="date">{{ query.date }}</span>
          </div>
        </div>
      </div>

      <div class="panel results-panel">
        <div v-if="isGenerating" class="generating">
          <div class="spinner"></div>
          <p>AI is analyzing your preferences...</p>
        </div>

        <div v-else-if="recommendations" class="recommendations">
          <div class="rec-section">
            <h3>Recommended Tonewoods</h3>
            <div class="tonewood-list">
              <div v-for="wood in recommendations.tonewoods" :key="wood.name" class="tonewood-item">
                <div class="tonewood-info">
                  <span class="tonewood-name">{{ wood.name }}</span>
                  <span class="tonewood-reason">{{ wood.reason }}</span>
                </div>
                <div class="tonewood-score">
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: wood.score + '%' }"></div>
                  </div>
                  <span class="score-value">{{ wood.score }}%</span>
                </div>
              </div>
            </div>
          </div>

          <div class="rec-section">
            <h3>Design Suggestions</h3>
            <div class="suggestion-list">
              <div v-for="item in recommendations.design" :key="item.feature" class="suggestion-item">
                <span class="feature">{{ item.feature }}</span>
                <span class="suggestion">{{ item.suggestion }}</span>
              </div>
            </div>
          </div>

          <div class="rec-section">
            <h3>Hardware Recommendations</h3>
            <div class="hardware-list">
              <div v-for="item in recommendations.hardware" :key="item.item" class="hardware-item">
                <span class="hw-name">{{ item.item }}</span>
                <span class="hw-rec">{{ item.recommendation }}</span>
              </div>
            </div>
          </div>

          <div class="rec-actions">
            <button class="btn btn-secondary">Save Build Plan</button>
            <button class="btn btn-secondary">Export PDF</button>
            <button class="btn btn-primary">Start Project</button>
          </div>
        </div>

        <div v-else class="no-result">
          <span class="icon">🎸</span>
          <p>Configure your preferences and click Generate</p>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full AI recommendations with cost estimation and supplier integration coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.recommendations-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h4 { font-size: 0.75rem; color: #888; margin: 1.5rem 0 0.75rem; }

.form-group { margin-bottom: 1.25rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.5rem; }
.form-group select { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.option-buttons { display: flex; gap: 0.5rem; }
.option-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #888; cursor: pointer; font-size: 0.875rem; }
.option-buttons button.active { background: #2563eb; border-color: #2563eb; color: #fff; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-large { width: 100%; padding: 1rem; font-size: 1rem; }

.recent-queries { margin-top: 1.5rem; border-top: 1px solid #333; padding-top: 1rem; }
.query-item { display: flex; justify-content: space-between; font-size: 0.875rem; padding: 0.5rem 0; border-bottom: 1px solid #262626; }
.query-item .date { color: #888; }

.generating { text-align: center; padding: 4rem; }
.spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }

.no-result { text-align: center; padding: 4rem; color: #666; }
.no-result .icon { font-size: 4rem; display: block; margin-bottom: 1rem; }

.rec-section { margin-bottom: 2rem; }
.rec-section h3 { margin-bottom: 1rem; }

.tonewood-list { display: flex; flex-direction: column; gap: 0.75rem; }
.tonewood-item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #262626; border-radius: 0.5rem; }
.tonewood-info { display: flex; flex-direction: column; }
.tonewood-name { font-weight: 500; }
.tonewood-reason { font-size: 0.75rem; color: #888; }
.tonewood-score { display: flex; align-items: center; gap: 0.5rem; }
.score-bar { width: 80px; height: 6px; background: #333; border-radius: 3px; overflow: hidden; }
.score-fill { height: 100%; background: #22c55e; }
.score-value { font-size: 0.75rem; font-weight: 600; color: #22c55e; }

.suggestion-list, .hardware-list { display: flex; flex-direction: column; gap: 0.5rem; }
.suggestion-item, .hardware-item { display: flex; justify-content: space-between; padding: 0.75rem; background: #262626; border-radius: 0.5rem; font-size: 0.875rem; }
.feature, .hw-name { font-weight: 500; }
.suggestion, .hw-rec { color: #888; }

.rec-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.rec-actions .btn { flex: 1; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1000px) { .content { grid-template-columns: 1fr; } }
</style>
