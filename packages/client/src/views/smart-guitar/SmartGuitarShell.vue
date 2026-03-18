<script setup lang="ts">
/**
 * SmartGuitarShell — Module 5 container for Smart Guitar workflow.
 * Tabs: Body Design, Electronics Layout, RPi5 Cavity, WiFi & Antenna, Export & BOM.
 */
import { ref } from "vue";
import { RouterLink } from "vue-router";

type TabId = "body" | "electronics" | "cavity" | "wifi" | "export";

const tabs: { id: TabId; label: string; icon: string }[] = [
  { id: "body", label: "Body Design", icon: "🎸" },
  { id: "electronics", label: "Electronics Layout", icon: "⚡" },
  { id: "cavity", label: "RPi5 Cavity", icon: "📦" },
  { id: "wifi", label: "WiFi & Antenna", icon: "📡" },
  { id: "export", label: "Export & BOM", icon: "📋" },
];

const activeTab = ref<TabId>("body");

function setTab(id: TabId) {
  activeTab.value = id;
}
</script>

<template>
  <div class="smart-guitar-shell">
    <header class="shell-header">
      <h1 class="shell-title">Smart Guitar</h1>
      <p class="shell-subtitle">
        Body design · Electronics · RPi5 cavity · WiFi & antenna · Export & BOM
      </p>
    </header>

    <nav class="tab-nav" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="setTab(tab.id)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </nav>

    <div class="tab-panels">
      <!-- Tab 1 — Body Design -->
      <section
        v-show="activeTab === 'body'"
        id="panel-body"
        role="tabpanel"
        class="tab-panel"
      >
        <div class="panel-content link-card">
          <p class="panel-text">
            Start from Instrument Hub with Smart Guitar model selected.
          </p>
          <RouterLink to="/instrument-hub" class="action-btn">
            Open Instrument Hub →
          </RouterLink>
        </div>

        <!-- ARCH-004: Plate physics info for semi-hollow variant -->
        <div class="panel-content info-card">
          <h3 class="panel-heading">Semi-Hollow Variant</h3>
          <p class="panel-text">
            Acoustic plate physics available for semi-hollow variant via
            <code>POST /api/acoustics/plate/analyze</code>
          </p>
          <p class="panel-note">
            Solid body guitars do not require plate thickness calculation.
            For carved top or semi-hollow variants, the plate design endpoints
            provide physics-based thickness recommendations.
          </p>
        </div>
      </section>

      <!-- Tab 2 — Electronics Layout -->
      <section
        v-show="activeTab === 'electronics'"
        id="panel-electronics"
        role="tabpanel"
        class="tab-panel"
      >
        <div class="panel-content placeholder">
          <h3 class="panel-heading">RPi5 cavity dimensions</h3>
          <ul class="spec-list">
            <li>Board: 85mm × 56mm × 17mm</li>
            <li>Minimum cavity depth: 20mm</li>
            <li>Footprint with clearance: 95mm × 66mm</li>
          </ul>
          <p class="panel-text coming">Electronics cavity routing — CAM generation coming in Week 4.</p>
        </div>
      </section>

      <!-- Tab 3 — RPi5 Cavity -->
      <section
        v-show="activeTab === 'cavity'"
        id="panel-cavity"
        role="tabpanel"
        class="tab-panel"
      >
        <div class="panel-content placeholder">
          <h3 class="panel-heading">USB-C port spec</h3>
          <ul class="spec-list">
            <li>Port: 9mm × 3.5mm</li>
            <li>Position: lower bout side</li>
            <li>Routing approach: 3+1 axis</li>
          </ul>
          <p class="panel-text coming">Cavity G-code generation coming soon.</p>
        </div>
      </section>

      <!-- Tab 4 — WiFi & Antenna -->
      <section
        v-show="activeTab === 'wifi'"
        id="panel-wifi"
        role="tabpanel"
        class="tab-panel"
      >
        <div class="panel-content placeholder">
          <p class="panel-text coming">Antenna placement and routing geometry — coming in Week 5.</p>
          <p class="panel-note">Antenna routed to upper horn area for signal clearance from strings.</p>
        </div>
      </section>

      <!-- Tab 5 — Export & BOM -->
      <section
        v-show="activeTab === 'export'"
        id="panel-export"
        role="tabpanel"
        class="tab-panel"
      >
        <div class="panel-content placeholder">
          <p class="panel-text coming">Full Smart Guitar BOM and G-code export — coming in Week 7.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.smart-guitar-shell {
  min-height: 100vh;
  background: var(--color-surface-alt, #f8fafc);
  padding: var(--space-6, 1.5rem);
}

.shell-header {
  margin-bottom: var(--space-6, 1.5rem);
}

.shell-title {
  font-size: var(--font-size-3xl, 1.875rem);
  font-weight: 800;
  color: var(--color-text, #1e293b);
  margin: 0 0 0.25rem;
}

.shell-subtitle {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
  margin: 0;
}

.tab-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: var(--space-4, 1rem);
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 500;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.tab-btn:hover {
  color: var(--color-text, #1e293b);
}

.tab-btn.active {
  color: var(--color-primary, #2563eb);
  border-bottom-color: var(--color-primary, #2563eb);
}

.tab-icon {
  font-size: 1.125rem;
}

.tab-panels {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-lg, 0.75rem);
  padding: var(--space-6, 1.5rem);
  min-height: 320px;
}

.tab-panel {
  outline: none;
}

.panel-content {
  max-width: 640px;
}

.panel-heading {
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: 700;
  color: var(--color-text, #1e293b);
  margin: 0 0 1rem;
}

.spec-list {
  margin: 0 0 1rem;
  padding-left: 1.25rem;
  color: var(--color-text, #1e293b);
  line-height: 1.6;
}

.panel-text {
  margin: 0 0 0.5rem;
  color: var(--color-text, #1e293b);
}

.panel-text.coming {
  color: var(--color-text-muted, #64748b);
  font-style: italic;
}

.panel-note {
  margin: 1rem 0 0;
  padding: 0.75rem;
  background: var(--color-surface-alt, #f1f5f9);
  border-radius: var(--radius-md, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
}

.link-card {
  padding: 1rem 0;
}

.info-card {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--color-surface-alt, #f1f5f9);
  border-radius: var(--radius-md, 0.5rem);
  border-left: 3px solid var(--color-primary, #2563eb);
}

.info-card code {
  background: var(--color-surface, #fff);
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius-sm, 0.25rem);
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: var(--color-primary, #2563eb);
  color: white;
  border-radius: var(--radius-md, 0.5rem);
  font-weight: 600;
  font-size: var(--font-size-sm, 0.875rem);
  text-decoration: none;
  transition: background 0.2s;
}

.action-btn:hover {
  background: var(--color-primary-dark, #1d4ed8);
  text-decoration: none;
  color: white;
}
</style>
