<script setup lang="ts">
/**
 * ApertureWorkspace — Unified aperture/soundhole workspace shell
 *
 * Status: Beta consolidation shell
 *
 * Dev Order 5: Shell only, no logic migration yet.
 * Dev Order 6: Mount SpiralSoundholeDesigner in Spiral tab.
 * Dev Order 9: Clarify canonical/beta provenance.
 *
 * Tabs:
 *   - Spiral: logarithmic spiral soundhole design (mounted production tool)
 *   - Round/Oval/F-hole: standard aperture types
 *   - Comparison: cross-type area/acoustic comparison
 *   - Inverse Solver: target area → parameter calculation
 *   - Calibration: measurement import and validation
 *
 * The Spiral tab mounts SpiralSoundholeDesigner.vue, the canonical production
 * implementation. The standalone route /calculators/acoustics/spiral-soundhole
 * remains canonical until feature parity is verified.
 */
import { ref, computed, defineAsyncComponent } from 'vue'
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import type { WorkflowGateLevel } from '@/types/workflow'

const SpiralSoundholeDesigner = defineAsyncComponent(
  () => import('@/components/toolbox/acoustics/SpiralSoundholeDesigner.vue')
)

type TabId = 'spiral' | 'standard' | 'comparison' | 'inverse' | 'calibration'

interface Tab {
  id: TabId
  label: string
  icon: string
  description: string
}

const tabs: Tab[] = [
  {
    id: 'spiral',
    label: 'Spiral',
    icon: '🌀',
    description: 'Logarithmic spiral soundhole design (Williams 2019)',
  },
  {
    id: 'standard',
    label: 'Round / Oval / F-hole',
    icon: '⭕',
    description: 'Traditional aperture types with standard sizing',
  },
  {
    id: 'comparison',
    label: 'Comparison',
    icon: '⚖️',
    description: 'Cross-type area and acoustic efficiency comparison',
  },
  {
    id: 'inverse',
    label: 'Inverse Solver',
    icon: '🔄',
    description: 'Calculate parameters from target area or P:A ratio',
  },
  {
    id: 'calibration',
    label: 'Calibration',
    icon: '📐',
    description: 'Import measurements and validate against specs',
  },
]

const activeTab = ref<TabId>('spiral')

function setTab(id: TabId) {
  activeTab.value = id
}

const activeTabData = computed(() => tabs.find((t) => t.id === activeTab.value))

const workspaceGate: WorkflowGateLevel = 'green'
</script>

<template>
  <div :class="$style.workspace">
    <!-- Sidebar -->
    <aside :class="$style.sidebar">
      <div :class="$style.sidebarHeader">
        <h2 :class="$style.title">Aperture Workspace</h2>
        <GateBadge :gate="workspaceGate" label="Beta" />
      </div>

      <nav :class="$style.tabNav">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[$style.tabButton, activeTab === tab.id && $style.active]"
          @click="setTab(tab.id)"
        >
          <span :class="$style.tabIcon">{{ tab.icon }}</span>
          <span :class="$style.tabLabel">{{ tab.label }}</span>
        </button>
      </nav>

      <div :class="$style.sidebarFooter">
        <PrerequisiteNotice
          message="Beta consolidation workspace. The Spiral tab mounts the production Spiral Soundhole Designer; the standalone route remains canonical until feature parity is verified."
        />
      </div>
    </aside>

    <!-- Main Content -->
    <main :class="$style.main">
      <!-- Header Strip -->
      <header :class="$style.header">
        <SectionLabel :text="activeTabData?.label ?? 'Aperture'" />
        <p :class="$style.description">{{ activeTabData?.description }}</p>
      </header>

      <!-- Tab Content -->
      <div :class="$style.content">
        <!-- Spiral Tab — Mounted Production Tool -->
        <div v-if="activeTab === 'spiral'" :class="$style.tabContent">
          <div :class="$style.mountedComponentHeader">
            <SectionLabel text="Spiral Aperture Designer" />
            <GateBadge gate="yellow" label="Mounted Production Tool" />
          </div>
          <div :class="$style.mountedComponentWrap">
            <Suspense>
              <template #default>
                <SpiralSoundholeDesigner />
              </template>
              <template #fallback>
                <div :class="$style.loadingPlaceholder">Loading Spiral Designer...</div>
              </template>
            </Suspense>
          </div>
        </div>

        <!-- Standard Types Tab -->
        <div v-else-if="activeTab === 'standard'" :class="$style.tabContent">
          <div :class="$style.placeholderCard">
            <SectionLabel text="Aperture Type Selection" />
            <div :class="$style.typePlaceholder">
              <div :class="$style.typeOption">
                <GateBadge gate="green" label="Round" />
                <span>Traditional circular soundhole</span>
              </div>
              <div :class="$style.typeOption">
                <GateBadge gate="green" label="Oval" />
                <span>Selmer/Maccaferri elliptical</span>
              </div>
              <div :class="$style.typeOption">
                <GateBadge gate="green" label="F-hole" />
                <span>Archtop f-holes</span>
              </div>
            </div>
          </div>

          <div :class="$style.placeholderCard">
            <SectionLabel text="Sizing" />
            <PrerequisiteNotice message="Select an aperture type above to configure sizing parameters." />
          </div>
        </div>

        <!-- Comparison Tab -->
        <div v-else-if="activeTab === 'comparison'" :class="$style.tabContent">
          <div :class="$style.placeholderCard">
            <SectionLabel text="Cross-Type Comparison" />
            <div :class="$style.comparisonPlaceholder">
              <p>Compare area, equivalent diameter, and P:A ratio across aperture types.</p>
              <p>Enables direct comparison: "How does my spiral compare to a 4-inch round?"</p>
            </div>
          </div>

          <PrerequisiteNotice
            message="Configure at least one aperture in Spiral or Standard tabs before comparing."
          />
        </div>

        <!-- Inverse Solver Tab -->
        <div v-else-if="activeTab === 'inverse'" :class="$style.tabContent">
          <div :class="$style.placeholderCard">
            <SectionLabel text="Inverse Solver" />
            <div :class="$style.inversePlaceholder">
              <p>Specify target area or P:A ratio, and the solver will calculate required parameters.</p>
              <p>Example: "I need 2000 mm² with P:A > 0.12 — what slot width and turns?"</p>
            </div>
          </div>

          <div :class="$style.placeholderCard">
            <SectionLabel text="Constraints" />
            <GateBadge gate="yellow" label="Not Implemented" />
            <p :class="$style.deferredNote">Inverse solver UI deferred to later dev order.</p>
          </div>
        </div>

        <!-- Calibration Tab -->
        <div v-else-if="activeTab === 'calibration'" :class="$style.tabContent">
          <div :class="$style.placeholderCard">
            <SectionLabel text="Measurement Import" />
            <div :class="$style.calibrationPlaceholder">
              <p>Import measured aperture dimensions from physical instruments.</p>
              <p>Validate against design specs and track deviations.</p>
            </div>
          </div>

          <PrerequisiteNotice message="Calibration framework deferred. Measurement import will integrate with NECK-A workflow patterns." />
        </div>
      </div>

      <!-- Export Region -->
      <footer :class="$style.footer">
        <SectionLabel text="Export" />
        <div :class="$style.exportPlaceholder">
          <button :class="$style.exportButton" disabled>DXF</button>
          <button :class="$style.exportButton" disabled>SVG</button>
          <button :class="$style.exportButton" disabled>JSON</button>
        </div>
      </footer>
    </main>
  </div>
</template>

<style module>
.workspace {
  display: flex;
  min-height: 100vh;
  background: #111827;
  color: #f9fafb;
}

.sidebar {
  width: 280px;
  background: #1f2937;
  border-right: 1px solid #374151;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.sidebarHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #374151;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.tabNav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.tabButton {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.5rem;
  color: #9ca3af;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.tabButton:hover {
  background: #374151;
  color: #f9fafb;
}

.tabButton.active {
  background: #374151;
  border-color: #6366f1;
  color: #f9fafb;
}

.tabIcon {
  font-size: 1.25rem;
}

.tabLabel {
  font-size: 0.875rem;
  font-weight: 500;
}

.sidebarFooter {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #374151;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  overflow-y: auto;
}

.header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #374151;
}

.description {
  color: #9ca3af;
  font-size: 0.875rem;
  margin: 0.5rem 0 0 0;
}

.content {
  flex: 1;
}

.tabContent {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.placeholderCard {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.previewPlaceholder,
.paramPlaceholder,
.resultsPlaceholder,
.typePlaceholder,
.comparisonPlaceholder,
.inversePlaceholder,
.calibrationPlaceholder {
  padding: 2rem;
  background: #111827;
  border-radius: 0.375rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

.previewPlaceholder {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.typePlaceholder {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: left;
  padding: 1rem;
}

.typeOption {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.375rem;
}

.typeOption span {
  color: #9ca3af;
}

.resultsPlaceholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.deferredNote {
  color: #6b7280;
  font-size: 0.8125rem;
  margin-top: 0.5rem;
}

.footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #374151;
}

.exportPlaceholder {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.exportButton {
  padding: 0.5rem 1rem;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.375rem;
  color: #6b7280;
  font-size: 0.875rem;
  cursor: not-allowed;
}

.exportButton:not(:disabled) {
  color: #f9fafb;
  cursor: pointer;
}

.exportButton:not(:disabled):hover {
  background: #4b5563;
}

/* Dev Order 6: Mounted component styles */
.mountedComponentHeader {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.mountedComponentWrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.loadingPlaceholder {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6b7280;
  font-size: 0.875rem;
}
</style>
