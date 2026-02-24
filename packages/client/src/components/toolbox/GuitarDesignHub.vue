<template>
  <div class="guitar-design-hub">
    <div class="hub-header">
      <h2>Guitar Design Tools</h2>
      <p>Complete suite of guitar construction design tools - organized by build phase</p>
    </div>

    <!-- Tool Selection by Phase -->
    <div
      v-if="!activeTool"
      class="design-grid"
    >
      <!-- Phase 1: Body Foundation -->
      <DesignPhaseSection
        icon="🏗️"
        phase="Phase 1"
        title="Body Foundation"
        description="Start here - create the body shape and structural design"
      >
        <ToolCard
          icon="🎸"
          title="Body Outline Generator"
          description="Parametric guitar body shapes (Acoustic/Electric/Classical/Bass)"
          badge="FOUNDATION"
          @select="selectTool('body-outline')"
        />
        <ToolCard
          icon="🏗️"
          title="Bracing Calculator"
          description="Structural mass estimation and glue area analysis"
          @select="selectTool('bracing')"
        />
        <ToolCard
          icon="🎻"
          title="Archtop Calculator"
          description="Top/back carving radii with Math API and SVG preview"
          @select="selectTool('archtop')"
        />
      </DesignPhaseSection>

      <!-- Phase 2: Neck & Fretboard -->
      <DesignPhaseSection
        icon="🎯"
        phase="Phase 2"
        title="Neck & Fretboard"
        description="Design the neck profile and fretboard geometry"
      >
        <ToolCard
          icon="🎸"
          title="Neck Generator"
          description="Parametric Les Paul C-profile neck with fretboard taper"
          @select="selectTool('neck')"
        />
        <ToolCard
          icon="📏"
          title="Scale Length Designer"
          description="Interactive tension calculator and intonation compensation"
          @select="selectTool('scale-length')"
        />
        <ToolCard
          icon="📏"
          title="Radius Dish Designer"
          description="Basic radius dish calculations and CNC setup"
          @select="selectTool('radius')"
        />
        <ToolCard
          icon="🥏"
          title="Enhanced Radius Dish"
          description="Design new dishes OR measure existing radii"
          @select="selectTool('radius-enhanced')"
        />
        <ToolCard
          icon="📐"
          title="Compound Radius"
          description="Fretboard compound radius visualization (12→16)"
          @select="selectTool('compound-radius')"
        />
      </DesignPhaseSection>

      <!-- Phase 3: Bridge & Setup -->
      <DesignPhaseSection
        icon="🌉"
        phase="Phase 3"
        title="Bridge & Setup"
        description="Calculate bridge compensation and setup measurements"
      >
        <ToolCard
          icon="🌉"
          title="Bridge Calculator"
          description="Saddle compensation with family presets and DXF export"
          @select="selectTool('bridge')"
        />
      </DesignPhaseSection>

      <!-- Phase 4: Hardware & Electronics -->
      <DesignPhaseSection
        icon="🔌"
        phase="Phase 4"
        title="Hardware & Electronics"
        description="Plan electronics cavity and wiring layouts"
      >
        <ToolCard
          icon="🔌"
          title="Hardware Layout"
          description="Electronics cavity positioning with DXF export"
          @select="selectTool('hardware')"
        />
        <ToolCard
          icon="⚡"
          title="Wiring Workbench"
          description="Treble bleed calculator and switch validation"
          @select="selectTool('wiring')"
        />
      </DesignPhaseSection>

      <!-- Phase 5: Decorative Details -->
      <DesignPhaseSection
        icon="🌹"
        phase="Phase 5"
        title="Decorative Details"
        description="Add decorative rosette patterns"
      >
        <ToolCard
          icon="🌹"
          title="Rosette Designer"
          description="Parametric soundhole rosette with DXF/G-code export"
          @select="selectTool('rosette')"
        />
      </DesignPhaseSection>

      <!-- Phase 6: Finishing -->
      <DesignPhaseSection
        icon="🎨"
        phase="Phase 6"
        title="Finishing"
        description="Plan finishing schedule and costs"
      >
        <ToolCard
          icon="🎨"
          title="Finish Planner"
          description="Finish schedule generator with cost estimation"
          @select="selectTool('finish')"
        />
        <ToolCard
          icon="🎨"
          title="Finishing Guide"
          description="Workflow planning (varnish, french polish, nitro, poly, oil)"
          @select="selectTool('finishing')"
        />
      </DesignPhaseSection>
    </div>

    <!-- Active Tool Display -->
    <div
      v-else
      class="active-tool"
    >
      <div class="tool-toolbar">
        <button
          class="back-btn"
          @click="activeTool = null"
        >
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
import { ToolCard, DesignPhaseSection } from './guitar-design-hub'
import GuitarDimensionsForm from './GuitarDimensionsForm.vue'
import BracingCalculator from './BracingCalculator.vue'
import ArchtopCalculator from './ArchtopCalculator.vue'
import LesPaulNeckGenerator from '../generators/neck/LesPaulNeckGenerator.vue'
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

  .hub-header h2 {
    font-size: 2rem;
  }
}
</style>
