<script setup lang="ts">
/**
 * ApertureWorkspace — Unified aperture/soundhole workspace shell
 *
 * Status: Beta consolidation shell
 *
 * Dev Order 5: Shell only, no logic migration yet.
 * Dev Order 6: Mount SpiralSoundholeDesigner in Spiral tab.
 * Dev Order 9: Clarify canonical/beta provenance.
 * Dev Order 60: Integrate MeasurementArchiveExchangeSection into Measurement Lab.
 * Dev Order 62: Add MeasurementArchiveEvidenceIndex for experimental history.
 * Dev Order 63: Add MeasurementResidualComparisonPanel for pairwise comparison.
 *
 * Tabs:
 *   - Spiral: logarithmic spiral soundhole design (mounted production tool)
 *   - Round/Oval/F-hole: standard aperture types
 *   - Comparison: cross-type area/acoustic comparison
 *   - Inverse Solver: target area → parameter calculation
 *   - Measurement Lab: archive exchange and evidence index
 *
 * The Spiral tab mounts SpiralSoundholeDesigner.vue, the canonical production
 * implementation. The standalone route /calculators/acoustics/spiral-soundhole
 * remains canonical until feature parity is verified.
 */
import { ref, computed, defineAsyncComponent } from 'vue'
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import {
  MeasurementArchiveExchangeSection,
  MeasurementArchiveEvidenceIndex,
  MeasurementResidualComparisonPanel,
} from '@/components/shared/acoustics'
import type { WorkflowGateLevel } from '@/types/workflow'
import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
} from '@/types/acoustics/measurementArchive'

const SpiralSoundholeDesigner = defineAsyncComponent(
  () => import('@/components/toolbox/acoustics/SpiralSoundholeDesigner.vue')
)

const StandardAperturePanel = defineAsyncComponent(
  () => import('./panels/StandardAperturePanel.vue')
)

const ApertureComparisonPanel = defineAsyncComponent(
  () => import('@/components/toolbox/acoustics/ApertureComparisonPanel.vue')
)

const TargetMatchingPanel = defineAsyncComponent(
  () => import('@/components/toolbox/acoustics/TargetMatchingPanel.vue')
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
    label: 'Target Matching',
    icon: '🎯',
    description: 'Solve for required aperture parameters from acoustic targets',
  },
  {
    id: 'calibration',
    label: 'Measurement Lab',
    icon: '📐',
    description: 'Archive, exchange, and review observational measurements',
  },
]

const activeTab = ref<TabId>('spiral')

function setTab(id: TabId) {
  activeTab.value = id
}

const activeTabData = computed(() => tabs.find((t) => t.id === activeTab.value))

const workspaceGate: WorkflowGateLevel = 'green'

// Dev Order 62: Evidence index state
const currentArchive = ref<MeasurementArchiveRecord | null>(null)
const evidenceArchives = ref<MeasurementArchiveRecord[]>([])

function handleArchiveExported(archive: MeasurementArchiveRecord) {
  // Add to evidence index if not already present
  if (!evidenceArchives.value.some((a) => a.archiveId === archive.archiveId)) {
    evidenceArchives.value = [archive, ...evidenceArchives.value]
  }
}

function handleArchiveImported(
  _result: MeasurementArchiveValidationResult,
  archive: MeasurementArchiveRecord | null
) {
  if (archive && !evidenceArchives.value.some((a) => a.archiveId === archive.archiveId)) {
    evidenceArchives.value = [archive, ...evidenceArchives.value]
  }
}

function handleArchiveSelect(archive: MeasurementArchiveRecord) {
  currentArchive.value = archive
}
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
          <Suspense>
            <template #default>
              <StandardAperturePanel />
            </template>
            <template #fallback>
              <div :class="$style.loadingPlaceholder">Loading Standard Aperture Panel...</div>
            </template>
          </Suspense>
        </div>

        <!-- Comparison Tab -->
        <div v-else-if="activeTab === 'comparison'" :class="$style.tabContent">
          <Suspense>
            <template #default>
              <ApertureComparisonPanel />
            </template>
            <template #fallback>
              <div :class="$style.loadingPlaceholder">Loading Comparison Panel...</div>
            </template>
          </Suspense>
        </div>

        <!-- Target Matching Tab -->
        <div v-else-if="activeTab === 'inverse'" :class="$style.tabContent">
          <Suspense>
            <template #default>
              <TargetMatchingPanel />
            </template>
            <template #fallback>
              <div :class="$style.loadingPlaceholder">Loading Target Matching Panel...</div>
            </template>
          </Suspense>
        </div>

        <!-- Measurement Lab Tab (Dev Order 60, 62) -->
        <div v-else-if="activeTab === 'calibration'" :class="$style.tabContent">
          <!-- Archive Exchange Section -->
          <MeasurementArchiveExchangeSection
            :archive="currentArchive"
            @exported="handleArchiveExported"
            @imported="handleArchiveImported"
          />

          <!-- Evidence Index -->
          <MeasurementArchiveEvidenceIndex
            :archives="evidenceArchives"
            @select="handleArchiveSelect"
          />

          <!-- Residual Comparison Panel (Dev Order 63) -->
          <MeasurementResidualComparisonPanel
            :archives="evidenceArchives"
          />

          <PrerequisiteNotice message="Measurement Lab is observational only. Archives are local — no persistence, calibration, or prediction authority." />
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

/* Dev Order 17: Solver card CSS moved to TargetMatchingPanel.vue */
</style>
