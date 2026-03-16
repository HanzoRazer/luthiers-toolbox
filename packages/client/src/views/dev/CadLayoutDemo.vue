<script setup lang="ts">
/**
 * CadLayoutDemo.vue
 * @deprecated — dev scratch view, not routed
 *
 * Demonstration of the VCarve/Fusion 360 style layout components.
 */

import { ref } from "vue";
import CadLayout from "@/layouts/CadLayout.vue";
import CadSidebar from "@/components/layout/CadSidebar.vue";
import CadPanel from "@/components/layout/CadPanel.vue";
import CadFeatureToggles from "@/components/layout/CadFeatureToggles.vue";
import CadInput from "@/components/ui/CadInput.vue";
import CadCheckbox from "@/components/ui/CadCheckbox.vue";
import type { FeatureToggleItem } from "@/components/layout/CadFeatureToggles.vue";
import { useFeatureToggles } from "@/composables/useFeatureToggles";

// Feature toggles demo
const { toggles, isEnabled, toggle } = useFeatureToggles({
  showToolpath: true,
  showRapids: true,
  showMaterial: false,
  showGrid: true,
  snapToGrid: false,
  animate: false,
});

// Convert to array for CadFeatureToggles component
const displayFeatures = ref<FeatureToggleItem[]>([
  { key: "showToolpath", label: "Show Toolpath", checked: true },
  { key: "showRapids", label: "Show Rapid Moves", checked: true },
  { key: "showMaterial", label: "Show Material Bounds", checked: false },
  { key: "showGrid", label: "Show Grid", checked: true },
  { key: "snapToGrid", label: "Snap to Grid", checked: false },
  { key: "animate", label: "Animate Preview", checked: false },
]);

function handleToggle(key: string, checked: boolean) {
  toggle(key as keyof typeof toggles);
  const feature = displayFeatures.value.find((f) => f.key === key);
  if (feature) feature.checked = checked;
}

// Demo form values
const toolDiameter = ref(6);
const feedRate = ref(1500);
const plungeRate = ref(500);
const stepDown = ref(2);
const stepOver = ref(40);
const safeZ = ref(5);

// Coordinates for status bar
const cursorX = ref(125.5);
const cursorY = ref(87.3);
const zoom = ref(100);

// Handle canvas mouse move for coordinate demo
function handleCanvasMouseMove(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const rect = target.getBoundingClientRect();
  cursorX.value = Math.round((e.clientX - rect.left) * 10) / 10;
  cursorY.value = Math.round((rect.bottom - e.clientY) * 10) / 10;
}

// Checkbox demo
const rememberSettings = ref(true);
const autoSave = ref(false);
</script>

<template>
  <CadLayout title="CAD Layout Demo">
    <!-- Left Panel: Navigation -->
    <template #left>
      <CadSidebar />
    </template>

    <!-- Center: Canvas Area -->
    <template #default>
      <div class="demo-canvas" @mousemove="handleCanvasMouseMove">
        <div class="canvas-content">
          <h2>Canvas Area</h2>
          <p>This is where the DXF preview, toolpath visualization, or 3D viewport would go.</p>

          <div class="toggle-status">
            <h3>Active Toggles:</h3>
            <ul>
              <li v-if="isEnabled('showToolpath')">Toolpath: ON</li>
              <li v-if="isEnabled('showRapids')">Rapids: ON</li>
              <li v-if="isEnabled('showMaterial')">Material: ON</li>
              <li v-if="isEnabled('showGrid')">Grid: ON</li>
              <li v-if="isEnabled('snapToGrid')">Snap: ON</li>
              <li v-if="isEnabled('animate')">Animate: ON</li>
            </ul>
          </div>

          <div class="params-display">
            <h3>Current Parameters:</h3>
            <code>
              Tool: {{ toolDiameter }}mm |
              Feed: {{ feedRate }}mm/min |
              Plunge: {{ plungeRate }}mm/min |
              Step Down: {{ stepDown }}mm |
              Step Over: {{ stepOver }}%
            </code>
          </div>
        </div>
      </div>
    </template>

    <!-- Right Panel: Properties -->
    <template #right>
      <div class="properties-scroll">
        <!-- Tool Settings Panel -->
        <CadPanel title="Tool Settings" icon="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z">
          <div class="property-group">
            <CadInput
              v-model="toolDiameter"
              label="Tool Diameter"
              type="number"
              suffix="mm"
              :min="0.1"
              :max="50"
              :step="0.1"
            />
            <CadInput
              v-model="feedRate"
              label="Feed Rate"
              type="number"
              suffix="mm/min"
              :min="100"
              :max="10000"
              :step="100"
            />
            <CadInput
              v-model="plungeRate"
              label="Plunge Rate"
              type="number"
              suffix="mm/min"
              :min="50"
              :max="5000"
              :step="50"
            />
          </div>
        </CadPanel>

        <!-- Cut Settings Panel -->
        <CadPanel title="Cut Settings" :collapsed="false">
          <div class="property-group">
            <CadInput
              v-model="stepDown"
              label="Step Down"
              type="number"
              suffix="mm"
              :min="0.1"
              :max="20"
              :step="0.1"
            />
            <CadInput
              v-model="stepOver"
              label="Step Over"
              type="number"
              suffix="%"
              :min="10"
              :max="100"
              :step="5"
            />
            <CadInput
              v-model="safeZ"
              label="Safe Z"
              type="number"
              suffix="mm"
              :min="1"
              :max="50"
            />
          </div>
        </CadPanel>

        <!-- Display Options Panel -->
        <CadPanel title="Display Options" :collapsed="false">
          <CadFeatureToggles
            :features="displayFeatures"
            @toggle="handleToggle"
          />
        </CadPanel>

        <!-- Preferences Panel -->
        <CadPanel title="Preferences" :collapsed="true">
          <div class="checkbox-group">
            <CadCheckbox
              v-model="rememberSettings"
              label="Remember Settings"
              description="Save parameters for next session"
            />
            <CadCheckbox
              v-model="autoSave"
              label="Auto-save Project"
              description="Automatically save changes"
            />
          </div>
        </CadPanel>
      </div>
    </template>

    <!-- Status Bar: Coordinates -->
    <template #status>
      <div class="demo-status">
        <span class="status-left">Ready - Move mouse over canvas</span>
        <div class="status-right">
          <span class="coord">X: {{ cursorX.toFixed(1) }}</span>
          <span class="coord">Y: {{ cursorY.toFixed(1) }}</span>
          <span class="sep">|</span>
          <span class="zoom">{{ zoom }}%</span>
          <span class="units">MM</span>
        </div>
      </div>
    </template>
  </CadLayout>
</template>

<style scoped>
.demo-canvas {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: repeating-linear-gradient(
    0deg,
    var(--color-bg-canvas, #1e1e1e) 0px,
    var(--color-bg-canvas, #1e1e1e) 19px,
    var(--color-border-panel, #3a3a3a) 19px,
    var(--color-border-panel, #3a3a3a) 20px
  ),
  repeating-linear-gradient(
    90deg,
    var(--color-bg-canvas, #1e1e1e) 0px,
    var(--color-bg-canvas, #1e1e1e) 19px,
    var(--color-border-panel, #3a3a3a) 19px,
    var(--color-border-panel, #3a3a3a) 20px
  );
}

.canvas-content {
  text-align: center;
  padding: 40px;
  background: var(--color-bg-panel, #242424);
  border-radius: 8px;
  border: 1px solid var(--color-border-panel, #3a3a3a);
  max-width: 500px;
}

.canvas-content h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--color-text-primary, #e0e0e0);
}

.canvas-content p {
  margin: 0 0 24px;
  color: var(--color-text-secondary, #a0a0a0);
  font-size: 13px;
}

.toggle-status {
  text-align: left;
  margin-bottom: 16px;
}

.toggle-status h3 {
  font-size: 12px;
  margin: 0 0 8px;
  color: var(--color-text-secondary, #a0a0a0);
}

.toggle-status ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toggle-status li {
  padding: 4px 8px;
  background: var(--color-success-light, #064e3b);
  color: var(--color-success, #4ade80);
  border-radius: 4px;
  font-size: 11px;
}

.params-display {
  text-align: left;
}

.params-display h3 {
  font-size: 12px;
  margin: 0 0 8px;
  color: var(--color-text-secondary, #a0a0a0);
}

.params-display code {
  display: block;
  padding: 8px;
  background: var(--color-bg-input, #333333);
  border-radius: 4px;
  font-size: 11px;
  color: var(--color-accent, #4a9eff);
}

.properties-scroll {
  padding: 12px;
  height: 100%;
  overflow-y: auto;
}

.property-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.demo-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 12px;
  font-size: 11px;
  font-family: ui-monospace, "SF Mono", Menlo, Monaco, monospace;
}

.status-left {
  color: var(--color-text-secondary, #a0a0a0);
}

.status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.coord {
  color: var(--color-text-primary, #e0e0e0);
  min-width: 70px;
}

.sep {
  color: var(--color-border-panel, #3a3a3a);
}

.zoom {
  color: var(--color-text-secondary, #a0a0a0);
}

.units {
  padding: 2px 6px;
  background: var(--color-bg-panel, #242424);
  border-radius: 3px;
  color: var(--color-accent, #4a9eff);
  font-weight: 500;
}
</style>
