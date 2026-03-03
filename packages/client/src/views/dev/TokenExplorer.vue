<template>
  <div class="token-explorer">
    <!-- Color Groups -->
    <section
      v-for="group in colorGroups"
      :key="group.label"
      class="token-section"
    >
      <h2 class="section-title">
        {{ group.label }}
      </h2>
      <div class="swatch-grid">
        <div
          v-for="token in group.tokens"
          :key="token.name"
          class="swatch-card"
          :title="`var(${token.name})`"
          @click="copyToken(token.name)"
        >
          <div
            class="swatch-color"
            :style="{ background: `var(${token.name})` }"
          >
            <span class="copy-hint">Copy</span>
          </div>
          <div class="swatch-meta">
            <div class="swatch-name">
              {{ token.label }}
            </div>
            <div class="swatch-var">
              {{ token.name }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Spacing Scale -->
    <section class="token-section">
      <h2 class="section-title">
        Spacing Scale
      </h2>
      <div class="spacing-list">
        <div
          v-for="token in spacingTokens"
          :key="token.name"
          class="spacing-row"
        >
          <div class="spacing-label">
            <span class="spacing-name">{{ token.label }}</span>
            <span class="spacing-var">{{ token.name }}</span>
          </div>
          <div class="spacing-bar-wrap">
            <div
              class="spacing-bar"
              :style="{ width: `var(${token.name})`, maxWidth: '100%' }"
            />
          </div>
          <span class="spacing-value">{{ token.value }}</span>
        </div>
      </div>
    </section>

    <!-- Radius Scale -->
    <section class="token-section">
      <h2 class="section-title">
        Border Radius
      </h2>
      <div class="radius-grid">
        <div
          v-for="token in radiusTokens"
          :key="token.name"
          class="radius-card"
        >
          <div
            class="radius-box"
            :style="{ borderRadius: `var(${token.name})` }"
          />
          <div class="radius-label">
            {{ token.label }}
          </div>
          <div class="radius-var">
            {{ token.name }}
          </div>
        </div>
      </div>
    </section>

    <!-- Shadow Scale -->
    <section class="token-section">
      <h2 class="section-title">
        Shadows
      </h2>
      <div class="shadow-grid">
        <div
          v-for="token in shadowTokens"
          :key="token.name"
          class="shadow-card"
        >
          <div
            class="shadow-box"
            :style="{ boxShadow: `var(${token.name})` }"
          />
          <div class="shadow-label">
            {{ token.label }}
          </div>
          <div class="shadow-var">
            {{ token.name }}
          </div>
        </div>
      </div>
    </section>

    <!-- Toast notification -->
    <Transition name="toast">
      <div
        v-if="copiedToken"
        class="copy-toast"
      >
        Copied: {{ copiedToken }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const copiedToken = ref('')

function copyToken(name: string) {
  navigator.clipboard.writeText(`var(${name})`).catch(() => {})
  copiedToken.value = `var(${name})`
  setTimeout(() => { copiedToken.value = '' }, 1800)
}

const colorGroups = [
  {
    label: 'Primary Brand',
    tokens: [
      { name: '--color-primary',        label: 'Primary' },
      { name: '--color-primary-hover',  label: 'Primary Hover' },
      { name: '--color-primary-active', label: 'Primary Active' },
      { name: '--color-primary-light',  label: 'Primary Light' },
      { name: '--color-primary-dark',   label: 'Primary Dark' },
    ],
  },
  {
    label: 'Semantic',
    tokens: [
      { name: '--color-success',      label: 'Success' },
      { name: '--color-success-light',label: 'Success Light' },
      { name: '--color-warning',      label: 'Warning' },
      { name: '--color-warning-light',label: 'Warning Light' },
      { name: '--color-danger',       label: 'Danger' },
      { name: '--color-danger-light', label: 'Danger Light' },
    ],
  },
  {
    label: 'Surface & Text',
    tokens: [
      { name: '--color-surface',          label: 'Surface' },
      { name: '--color-surface-elevated', label: 'Surface Elevated' },
      { name: '--color-surface-hover',    label: 'Surface Hover' },
      { name: '--color-text',             label: 'Text' },
      { name: '--color-text-muted',       label: 'Text Muted' },
      { name: '--color-text-light',       label: 'Text Light' },
      { name: '--color-border',           label: 'Border' },
      { name: '--color-border-light',     label: 'Border Light' },
    ],
  },
  {
    label: 'RMOS Risk Levels',
    tokens: [
      { name: '--color-risk-green',    label: 'Risk Green' },
      { name: '--color-risk-green-bg', label: 'Risk Green BG' },
      { name: '--color-risk-yellow',   label: 'Risk Yellow' },
      { name: '--color-risk-yellow-bg',label: 'Risk Yellow BG' },
      { name: '--color-risk-red',      label: 'Risk Red' },
      { name: '--color-risk-red-bg',   label: 'Risk Red BG' },
    ],
  },
]

const spacingTokens = [
  { name: '--space-1',  label: 'Space 1',  value: '4px' },
  { name: '--space-2',  label: 'Space 2',  value: '8px' },
  { name: '--space-3',  label: 'Space 3',  value: '12px' },
  { name: '--space-4',  label: 'Space 4',  value: '16px' },
  { name: '--space-5',  label: 'Space 5',  value: '20px' },
  { name: '--space-6',  label: 'Space 6',  value: '24px' },
  { name: '--space-8',  label: 'Space 8',  value: '32px' },
  { name: '--space-10', label: 'Space 10', value: '40px' },
  { name: '--space-12', label: 'Space 12', value: '48px' },
  { name: '--space-16', label: 'Space 16', value: '64px' },
]

const radiusTokens = [
  { name: '--radius-sm',   label: 'sm — 4px' },
  { name: '--radius-md',   label: 'md — 6px' },
  { name: '--radius-lg',   label: 'lg — 8px' },
  { name: '--radius-xl',   label: 'xl — 12px' },
  { name: '--radius-2xl',  label: '2xl — 16px' },
  { name: '--radius-full', label: 'full — 9999px' },
]

const shadowTokens = [
  { name: '--shadow-sm', label: 'Shadow SM' },
  { name: '--shadow-md', label: 'Shadow MD' },
  { name: '--shadow-lg', label: 'Shadow LG' },
  { name: '--shadow-xl', label: 'Shadow XL' },
]
</script>

<style scoped>
.token-explorer {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.token-section {}

.section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-4) 0;
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border);
}

/* Color swatches */
.swatch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-3);
}

.swatch-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
  cursor: pointer;
  transition: box-shadow var(--transition-fast);
}

.swatch-card:hover {
  box-shadow: var(--shadow-md);
}

.swatch-card:hover .copy-hint {
  opacity: 1;
}

.swatch-color {
  height: 64px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-hint {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: white;
  background: rgba(0,0,0,0.45);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  opacity: 0;
  transition: opacity var(--transition-fast);
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.swatch-meta {
  padding: var(--space-2) var(--space-3);
}

.swatch-name {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.swatch-var {
  font-size: 0.625rem;
  color: var(--color-text-light);
  font-family: var(--font-family-mono);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Spacing */
.spacing-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.spacing-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.spacing-label {
  width: 140px;
  flex-shrink: 0;
}

.spacing-name {
  font-size: var(--font-size-sm);
  color: var(--color-text);
  display: block;
}

.spacing-var {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-muted);
}

.spacing-bar-wrap {
  flex: 1;
  height: 24px;
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
  position: relative;
}

.spacing-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-sm);
  min-width: 4px;
}

.spacing-value {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-muted);
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

/* Radius */
.radius-grid {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.radius-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.radius-box {
  width: 64px;
  height: 64px;
  background: var(--color-primary-light);
  border: 2px solid var(--color-primary);
}

.radius-label {
  font-size: var(--font-size-xs);
  color: var(--color-text);
  text-align: center;
}

.radius-var {
  font-size: 0.625rem;
  font-family: var(--font-family-mono);
  color: var(--color-text-light);
}

/* Shadow */
.shadow-grid {
  display: flex;
  gap: var(--space-8);
  flex-wrap: wrap;
}

.shadow-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.shadow-box {
  width: 100px;
  height: 64px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.shadow-label {
  font-size: var(--font-size-xs);
  color: var(--color-text);
}

.shadow-var {
  font-size: 0.625rem;
  font-family: var(--font-family-mono);
  color: var(--color-text-light);
}

/* Toast */
.copy-toast {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-text);
  color: var(--color-surface);
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-toast);
  pointer-events: none;
}

.toast-enter-active, .toast-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
</style>
