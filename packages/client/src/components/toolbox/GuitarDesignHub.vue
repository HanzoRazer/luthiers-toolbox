<template>
  <div class="guitar-design-hub">
    <div class="hub-header">
      <h2>🎸 Guitar Design Tools</h2>
      <p>Complete suite of guitar construction design tools - organized by build phase</p>
    </div>

    <!-- Tool Selection by Phase -->
    <div v-if="!activeTool" class="design-grid">
      <!-- Phase 1: Body Foundation -->
      <div class="design-category">
        <h3>🏗️ Phase 1: Body Foundation</h3>
        <p class="phase-desc">Start here - create the body shape and structural design</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('body-outline')">
            <div class="tool-icon">🎸</div>
            <h4>Body Outline Generator</h4>
            <p>Parametric guitar body shapes (Acoustic/Electric/Classical/Bass)</p>
            <span class="tool-badge">FOUNDATION</span>
          </div>
          <div class="tool-card" @click="selectTool('bracing')">
            <div class="tool-icon">🏗️</div>
            <h4>Bracing Calculator</h4>
            <p>Structural mass estimation and glue area analysis</p>
          </div>
          <div class="tool-card" @click="selectTool('archtop')">
            <div class="tool-icon">🎻</div>
            <h4>Archtop Calculator</h4>
            <p>Top/back carving radii with Math API and SVG preview</p>
          </div>
        </div>
      </div>

      <!-- Phase 2: Neck & Fretboard -->
      <div class="design-category">
        <h3>🎯 Phase 2: Neck & Fretboard</h3>
        <p class="phase-desc">Design the neck profile and fretboard geometry</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('neck')">
            <div class="tool-icon">🎸</div>
            <h4>Neck Generator</h4>
            <p>Parametric Les Paul C-profile neck with fretboard taper</p>
          </div>
          <div class="tool-card" @click="selectTool('scale-length')">
            <div class="tool-icon">📏</div>
            <h4>Scale Length Designer</h4>
            <p>Interactive tension calculator and intonation compensation</p>
          </div>
          <div class="tool-card" @click="selectTool('radius')">
            <div class="tool-icon">📏</div>
            <h4>Radius Dish Designer</h4>
            <p>Basic radius dish calculations and CNC setup</p>
          </div>
          <div class="tool-card" @click="selectTool('radius-enhanced')">
            <div class="tool-icon">🥏</div>
            <h4>Enhanced Radius Dish</h4>
            <p>Design new dishes OR measure existing radii</p>
          </div>
          <div class="tool-card" @click="selectTool('compound-radius')">
            <div class="tool-icon">📐</div>
            <h4>Compound Radius</h4>
            <p>Fretboard compound radius visualization (12"→16")</p>
          </div>
        </div>
      </div>

      <!-- Phase 3: Bridge & Setup -->
      <div class="design-category">
        <h3>🌉 Phase 3: Bridge & Setup</h3>
        <p class="phase-desc">Calculate bridge compensation and setup measurements</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('bridge')">
            <div class="tool-icon">🌉</div>
            <h4>Bridge Calculator</h4>
            <p>Saddle compensation with family presets and DXF export</p>
          </div>
        </div>
      </div>

      <!-- Phase 4: Hardware & Electronics -->
      <div class="design-category">
        <h3>🔌 Phase 4: Hardware & Electronics</h3>
        <p class="phase-desc">Plan electronics cavity and wiring layouts</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('hardware')">
            <div class="tool-icon">🔌</div>
            <h4>Hardware Layout</h4>
            <p>Electronics cavity positioning with DXF export</p>
          </div>
          <div class="tool-card" @click="selectTool('wiring')">
            <div class="tool-icon">⚡</div>
            <h4>Wiring Workbench</h4>
            <p>Treble bleed calculator and switch validation</p>
          </div>
        </div>
      </div>

      <!-- Phase 5: Decorative Details -->
      <div class="design-category">
        <h3>🌹 Phase 5: Decorative Details</h3>
        <p class="phase-desc">Add decorative rosette patterns</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('rosette')">
            <div class="tool-icon">🌹</div>
            <h4>Rosette Designer</h4>
            <p>Parametric soundhole rosette with DXF/G-code export</p>
          </div>
        </div>
      </div>

      <!-- Phase 6: Finishing -->
      <div class="design-category">
        <h3>🎨 Phase 6: Finishing</h3>
        <p class="phase-desc">Plan finishing schedule and costs</p>
        <div class="tool-cards">
          <div class="tool-card" @click="selectTool('finish')">
            <div class="tool-icon">🎨</div>
            <h4>Finish Planner</h4>
            <p>Finish schedule generator with cost estimation</p>
          </div>
          <div class="tool-card" @click="selectTool('finishing')">
            <div class="tool-icon">🎨</div>
            <h4>Finishing Guide</h4>
            <p>Workflow planning (varnish, french polish, nitro, poly, oil)</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Tool Display -->
    <div v-else class="active-tool">
      <div class="tool-toolbar">
        <button @click="activeTool = null" class="back-btn">
          ← Back to Guitar Design Tools
        </button>
        <h3>{{ getToolTitle(activeTool) }}</h3>
      </div>

      <GuitarDimensionsForm v-if="activeTool === 'body-outline'" />
      <BracingCalculator v-if="activeTool === 'bracing'" />
      <ArchtopCalculator v-if="activeTool === 'archtop'" />
      <LesPaulNeckGenerator v-if="activeTool === 'neck'" />
      <ScaleLengthDesigner v-if="activeTool === 'scale-length'" />
      <RadiusDishDesigner v-if="activeTool === 'radius'" />
      <EnhancedRadiusDish v-if="activeTool === 'radius-enhanced'" />
      <FretboardCompoundRadius v-if="activeTool === 'compound-radius'" />
      <BridgeCalculator v-if="activeTool === 'bridge'" />
      <HardwareLayout v-if="activeTool === 'hardware'" />
      <WiringWorkbench v-if="activeTool === 'wiring'" />
      <RosetteDesigner v-if="activeTool === 'rosette'" />
      <FinishPlanner v-if="activeTool === 'finish'" />
      <FinishingDesigner v-if="activeTool === 'finishing'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import GuitarDimensionsForm from './GuitarDimensionsForm.vue'
import BracingCalculator from './BracingCalculator.vue'
import ArchtopCalculator from './ArchtopCalculator.vue'
import LesPaulNeckGenerator from './LesPaulNeckGenerator.vue'
import ScaleLengthDesigner from './ScaleLengthDesigner.vue'
import RadiusDishDesigner from './RadiusDishDesigner.vue'
import EnhancedRadiusDish from './EnhancedRadiusDish.vue'
import FretboardCompoundRadius from './FretboardCompoundRadius.vue'
import BridgeCalculator from './BridgeCalculator.vue'
import HardwareLayout from './HardwareLayout.vue'
import WiringWorkbench from './WiringWorkbench.vue'
import RosetteDesigner from './RosetteDesigner.vue'
import FinishPlanner from './FinishPlanner.vue'
import FinishingDesigner from './FinishingDesigner.vue'

const activeTool = ref<string | null>(null)

function selectTool(toolId: string) {
  activeTool.value = toolId
}

// Listen for tool selection events from landing page
function handleToolSelection(event: any) {
  const toolId = event.detail
  if (toolId) {
    selectTool(toolId)
  }
}

onMounted(() => {
  window.addEventListener('select-guitar-tool', handleToolSelection)
})

onUnmounted(() => {
  window.removeEventListener('select-guitar-tool', handleToolSelection)
})

function getToolTitle(toolId: string): string {
  const titles: Record<string, string> = {
    'body-outline': '🎸 Body Outline Generator',
    'bracing': '🏗️ Bracing Calculator',
    'archtop': '🎻 Archtop Calculator',
    'neck': '🎸 Neck Generator',
    'scale-length': '📏 Scale Length Designer',
    'radius': '📏 Radius Dish Designer',
    'radius-enhanced': '🥏 Enhanced Radius Dish',
    'compound-radius': '📐 Compound Radius',
    'bridge': '🌉 Bridge Calculator',
    'hardware': '🔌 Hardware Layout',
    'wiring': '⚡ Wiring Workbench',
    'rosette': '🌹 Rosette Designer',
    'finish': '🎨 Finish Planner',
    'finishing': '🎨 Finishing Guide'
  }
  return titles[toolId] || toolId
}
</script>

<style scoped>
.guitar-design-hub {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.hub-header {
  text-align: center;
  margin-bottom: 3rem;
}

.hub-header h2 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.hub-header p {
  font-size: 1.1rem;
  color: #666;
}

.design-grid {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.design-category {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #3b82f6;
}

.design-category h3 {
  font-size: 1.6rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.phase-desc {
  color: #666;
  font-style: italic;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.tool-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
}

.tool-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.75rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 6px rgba(0,0,0,0.1);
  position: relative;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.2);
}

.tool-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  text-align: center;
}

.tool-card h4 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.tool-card p {
  font-size: 0.9rem;
  opacity: 0.9;
  text-align: center;
  line-height: 1.4;
  margin: 0;
}

.tool-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(255,255,255,0.3);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.active-tool {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.tool-toolbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(255,255,255,0.3);
}

.tool-toolbar h3 {
  margin: 0;
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .guitar-design-hub {
    padding: 1rem;
  }

  .tool-cards {
    grid-template-columns: 1fr;
  }

  .hub-header h2 {
    font-size: 2rem;
  }
}
</style>
