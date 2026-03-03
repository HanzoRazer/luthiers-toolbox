<template>
  <div class="typography">
    <section class="type-section">
      <h2 class="section-title">
        Type Scale
      </h2>
      <div class="scale-list">
        <div
          v-for="token in typeScale"
          :key="token.name"
          class="scale-row"
        >
          <div class="scale-meta">
            <span class="token-name">{{ token.name }}</span>
            <span class="token-value">{{ token.value }}</span>
          </div>
          <div
            class="scale-sample"
            :style="{ fontSize: `var(${token.name})` }"
          >
            {{ sampleText }}
          </div>
        </div>
      </div>
    </section>

    <section class="type-section">
      <h2 class="section-title">
        Font Families
      </h2>
      <div class="family-row">
        <div class="family-card">
          <div class="family-label">
            Sans — var(--font-family-sans)
          </div>
          <div class="family-sample sans">
            ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>
            abcdefghijklmnopqrstuvwxyz<br>
            0123456789 — CAM parameters, body text, UI labels
          </div>
        </div>
        <div class="family-card">
          <div class="family-label">
            Mono — var(--font-family-mono)
          </div>
          <div class="family-sample mono">
            G00 X12.500 Y-3.250 Z5.000<br>
            G01 F800 X0.000 Y0.000<br>
            M30 — G-code, DXF paths, SHA hashes
          </div>
        </div>
      </div>
    </section>

    <section class="type-section">
      <h2 class="section-title">
        Font Weights
      </h2>
      <div class="weight-list">
        <div
          v-for="w in weights"
          :key="w.name"
          class="weight-row"
        >
          <span class="token-name">{{ w.name }}</span>
          <span
            class="weight-sample"
            :style="{ fontWeight: `var(${w.name})` }"
          >{{ w.label }} — {{ sampleText }}</span>
        </div>
      </div>
    </section>

    <section class="type-section">
      <h2 class="section-title">
        Real Usage Examples
      </h2>
      <div class="usage-grid">
        <div class="usage-card">
          <div class="usage-label">
            CAM Dashboard Stat
          </div>
          <div class="stat-example">
            <div class="stat-value">
              94.2%
            </div>
            <div class="stat-label">
              Toolpath Efficiency
            </div>
            <div class="stat-sub">
              Last 30 runs · Updated 4 min ago
            </div>
          </div>
        </div>

        <div class="usage-card">
          <div class="usage-label">
            RMOS Candidate Row
          </div>
          <div class="candidate-example">
            <div class="candidate-header">
              <span class="candidate-name">Rosette #4 — Sitka v2</span>
              <span class="candidate-risk green">✓ GREEN</span>
            </div>
            <div class="candidate-meta">
              run_id: rmos_a1b2c3d4 · 2026-03-01 09:14
            </div>
          </div>
        </div>

        <div class="usage-card">
          <div class="usage-label">
            G-Code Line
          </div>
          <div class="gcode-example">
            <span class="gcode-line-num">0042</span>
            <span class="gcode-cmd">G01</span>
            <span class="gcode-param">X</span><span class="gcode-val">12.500</span>
            <span class="gcode-param">Y</span><span class="gcode-val">-3.250</span>
            <span class="gcode-param">F</span><span class="gcode-val">800</span>
          </div>
        </div>

        <div class="usage-card">
          <div class="usage-label">
            Section Header
          </div>
          <div class="header-example">
            <h3 class="ex-h3">
              Scale Length Designer
            </h3>
            <p class="ex-body">
              Configure fret spacing, multi-scale, and string tension for your instrument build.
            </p>
            <span class="ex-link">View documentation →</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const sampleText = 'Luthier\'s ToolBox — Production Shop'

const typeScale = [
  { name: '--font-size-xs',   value: '12px' },
  { name: '--font-size-sm',   value: '14px' },
  { name: '--font-size-base', value: '16px' },
  { name: '--font-size-lg',   value: '18px' },
  { name: '--font-size-xl',   value: '20px' },
  { name: '--font-size-2xl',  value: '24px' },
  { name: '--font-size-3xl',  value: '30px' },
]

const weights = [
  { name: '--font-weight-normal',   label: 'Normal 400' },
  { name: '--font-weight-medium',   label: 'Medium 500' },
  { name: '--font-weight-semibold', label: 'Semibold 600' },
  { name: '--font-weight-bold',     label: 'Bold 700' },
]
</script>

<style scoped>
.typography {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.type-section {}

.section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-4) 0;
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border);
}

/* Scale */
.scale-list { display: flex; flex-direction: column; gap: var(--space-4); }

.scale-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-6);
}

.scale-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 160px;
  flex-shrink: 0;
}

.token-name {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-primary-dark);
}

.token-value {
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
}

.scale-sample {
  color: var(--color-text);
  line-height: 1.2;
}

/* Families */
.family-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.family-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.family-label {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-muted);
  margin-bottom: var(--space-3);
}

.family-sample {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  color: var(--color-text);
}

.family-sample.sans { font-family: var(--font-family-sans); }
.family-sample.mono { font-family: var(--font-family-mono); }

/* Weights */
.weight-list { display: flex; flex-direction: column; gap: var(--space-3); }

.weight-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.weight-row .token-name {
  width: 180px;
  flex-shrink: 0;
}

.weight-sample {
  font-size: var(--font-size-lg);
  color: var(--color-text);
}

/* Usage examples */
.usage-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.usage-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.usage-label {
  font-size: 0.625rem;
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-light);
  margin-bottom: var(--space-3);
}

/* Stat */
.stat-example { display: flex; flex-direction: column; gap: 2px; }

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  line-height: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
}

.stat-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
}

/* Candidate */
.candidate-example {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.candidate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.candidate-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.candidate-risk {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.candidate-risk.green {
  background: var(--color-risk-green-bg);
  color: #065f46;
}

.candidate-meta {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-light);
}

/* G-code */
.gcode-example {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  background: #0d1117;
  color: #c9d1d9;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  align-items: baseline;
}

.gcode-line-num { color: #6e7681; font-size: var(--font-size-xs); }
.gcode-cmd     { color: #ff7b72; font-weight: var(--font-weight-bold); }
.gcode-param   { color: #79c0ff; }
.gcode-val     { color: #a5d6ff; }

/* Header example */
.header-example { display: flex; flex-direction: column; gap: var(--space-2); }

.ex-h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0;
}

.ex-body {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
  line-height: var(--line-height-normal);
}

.ex-link {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  cursor: pointer;
}
</style>
