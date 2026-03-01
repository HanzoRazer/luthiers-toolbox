<script setup lang="ts">
/**
 * QuoteTab - Generate customer-facing quotes
 *
 * Features:
 * - Configurable markup percentage
 * - Customer name and validity period
 * - Printable quote format
 * - Copy to clipboard
 */
import { ref, computed } from "vue";
import type { EstimateResult } from "@/types/businessEstimator";

const props = defineProps<{
  estimate: EstimateResult;
}>();

// ============================================================================
// STATE
// ============================================================================

const customerName = ref("");
const markupPct = ref(25);
const validityDays = ref(30);
const notes = ref("");
const showPreview = ref(false);

// ============================================================================
// COMPUTED
// ============================================================================

const markup = computed(() => {
  return props.estimate.total_cost_per_unit * (markupPct.value / 100);
});

const finalPrice = computed(() => {
  return props.estimate.total_cost_per_unit + markup.value;
});

const profitMargin = computed(() => {
  if (finalPrice.value === 0) return 0;
  return (markup.value / finalPrice.value) * 100;
});

const validUntil = computed(() => {
  const date = new Date();
  date.setDate(date.getDate() + validityDays.value);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
});

const quoteId = computed(() => {
  const now = new Date();
  const datePart = now.toISOString().slice(0, 10).replace(/-/g, "");
  const randomPart = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `Q-${datePart}-${randomPart}`;
});

const quoteText = computed(() => {
  const lines = [
    "═══════════════════════════════════════════════════════",
    "                      QUOTE",
    "═══════════════════════════════════════════════════════",
    "",
    `Quote #:        ${quoteId.value}`,
    `Date:           ${new Date().toLocaleDateString()}`,
    `Valid Until:    ${validUntil.value}`,
    "",
  ];

  if (customerName.value) {
    lines.push(`Customer:       ${customerName.value}`);
    lines.push("");
  }

  lines.push("───────────────────────────────────────────────────────");
  lines.push("DESCRIPTION");
  lines.push("───────────────────────────────────────────────────────");
  lines.push("");
  lines.push(`Instrument:     ${props.estimate.instrument_type}`);
  lines.push(`Quantity:       ${props.estimate.quantity}`);
  lines.push(`Est. Hours:     ${props.estimate.total_hours.toFixed(1)} hours`);
  lines.push("");
  lines.push("───────────────────────────────────────────────────────");
  lines.push("PRICING");
  lines.push("───────────────────────────────────────────────────────");
  lines.push("");
  lines.push(`Labor:          $${props.estimate.labor_cost_per_unit.toFixed(2)}`);
  lines.push(`Materials:      $${props.estimate.material_cost_per_unit.toFixed(2)}`);
  lines.push(`Subtotal:       $${props.estimate.total_cost_per_unit.toFixed(2)}`);
  lines.push("");
  lines.push("───────────────────────────────────────────────────────");
  lines.push(`TOTAL:          $${finalPrice.value.toFixed(2)}`);
  lines.push("───────────────────────────────────────────────────────");
  lines.push("");

  if (notes.value) {
    lines.push("NOTES:");
    lines.push(notes.value);
    lines.push("");
  }

  lines.push("TERMS:");
  lines.push("• 50% deposit required to begin work");
  lines.push("• Balance due upon completion");
  lines.push("• Timeline estimate provided after deposit");
  lines.push("");
  lines.push("═══════════════════════════════════════════════════════");

  return lines.join("\n");
});

// ============================================================================
// ACTIONS
// ============================================================================

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(quoteText.value);
    alert("Quote copied to clipboard!");
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement("textarea");
    textarea.value = quoteText.value;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    alert("Quote copied to clipboard!");
  }
}

function printQuote() {
  const printWindow = window.open("", "_blank");
  if (printWindow) {
    printWindow.document.write(`
      <html>
        <head>
          <title>Quote ${quoteId.value}</title>
          <style>
            body { font-family: 'Courier New', monospace; font-size: 12px; padding: 20px; }
            pre { white-space: pre-wrap; }
          </style>
        </head>
        <body>
          <pre>${quoteText.value}</pre>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  }
}
</script>

<template>
  <div class="quote-tab">
    <!-- Quote Configuration -->
    <section class="config-section">
      <h3>Quote Settings</h3>

      <div class="config-grid">
        <label class="config-field">
          <span class="field-label">Customer Name</span>
          <input
            v-model="customerName"
            type="text"
            placeholder="Optional"
            class="text-input"
          />
        </label>

        <label class="config-field">
          <span class="field-label">Markup %</span>
          <div class="markup-input">
            <input
              v-model.number="markupPct"
              type="number"
              min="0"
              max="100"
              step="5"
              class="number-input"
            />
            <span class="unit">%</span>
          </div>
        </label>

        <label class="config-field">
          <span class="field-label">Valid For</span>
          <div class="validity-input">
            <input
              v-model.number="validityDays"
              type="number"
              min="7"
              max="90"
              step="7"
              class="number-input"
            />
            <span class="unit">days</span>
          </div>
        </label>
      </div>

      <label class="config-field full-width">
        <span class="field-label">Notes</span>
        <textarea
          v-model="notes"
          placeholder="Additional notes for the customer..."
          class="notes-input"
          rows="2"
        ></textarea>
      </label>
    </section>

    <!-- Pricing Summary -->
    <section class="pricing-section">
      <h3>Pricing Summary</h3>

      <div class="price-breakdown">
        <div class="price-row">
          <span class="price-label">Cost (Labor + Materials)</span>
          <span class="price-value">${{ estimate.total_cost_per_unit.toFixed(2) }}</span>
        </div>
        <div class="price-row">
          <span class="price-label">Markup ({{ markupPct }}%)</span>
          <span class="price-value">+${{ markup.toFixed(2) }}</span>
        </div>
        <div class="price-row total">
          <span class="price-label">Quote Price</span>
          <span class="price-value">${{ finalPrice.toFixed(2) }}</span>
        </div>
      </div>

      <div class="margin-info">
        Profit margin: <strong>{{ profitMargin.toFixed(1) }}%</strong>
      </div>
    </section>

    <!-- Preview Toggle -->
    <section class="preview-section">
      <button
        type="button"
        class="preview-toggle"
        @click="showPreview = !showPreview"
      >
        {{ showPreview ? '▾ Hide Preview' : '▸ Show Preview' }}
      </button>

      <div v-if="showPreview" class="quote-preview">
        <pre>{{ quoteText }}</pre>
      </div>
    </section>

    <!-- Actions -->
    <section class="actions-section">
      <button type="button" class="btn-secondary" @click="copyToClipboard">
        Copy to Clipboard
      </button>
      <button type="button" class="btn-primary" @click="printQuote">
        Print Quote
      </button>
    </section>
  </div>
</template>

<style scoped>
.quote-tab {
  padding: 16px;
}

.config-section,
.pricing-section,
.preview-section,
.actions-section {
  margin-bottom: 20px;
}

h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0 0 12px;
}

/* Config Grid */
.config-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.config-field {
  display: block;
}

.config-field.full-width {
  grid-column: 1 / -1;
}

.field-label {
  display: block;
  font-size: 9px;
  letter-spacing: 1px;
  color: #506090;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.text-input,
.notes-input {
  width: 100%;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #e0e8ff;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  border-radius: 3px;
}

.notes-input {
  resize: vertical;
  min-height: 50px;
}

.markup-input,
.validity-input {
  display: flex;
  align-items: center;
  gap: 6px;
}

.number-input {
  width: 70px;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #e0e8ff;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  border-radius: 3px;
  text-align: right;
}

.unit {
  font-size: 11px;
  color: #606888;
}

/* Pricing Section */
.price-breakdown {
  background: #14192a;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 12px;
}

.price-row:not(:last-child) {
  border-bottom: 1px solid #1e2438;
}

.price-row.total {
  padding-top: 10px;
  margin-top: 4px;
  border-top: 2px solid #2a3040;
}

.price-label {
  color: #8090b0;
}

.price-value {
  color: #c0c8e0;
  font-weight: 500;
}

.price-row.total .price-label {
  font-weight: 700;
  color: #f0c060;
}

.price-row.total .price-value {
  font-size: 16px;
  font-weight: 700;
  color: #60e0a0;
}

.margin-info {
  font-size: 11px;
  color: #606888;
  text-align: right;
}

.margin-info strong {
  color: #80a0d0;
}

/* Preview */
.preview-toggle {
  width: 100%;
  padding: 10px;
  background: none;
  border: 1px dashed #2a3040;
  color: #6080b0;
  font-size: 11px;
  font-family: inherit;
  letter-spacing: 1px;
  cursor: pointer;
  border-radius: 3px;
  transition: all 0.15s;
}

.preview-toggle:hover {
  border-color: #4060c0;
  color: #80a0d0;
}

.quote-preview {
  margin-top: 12px;
  background: #0a0d14;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.quote-preview pre {
  font-size: 10px;
  color: #a0a8c0;
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.5;
}

/* Actions */
.actions-section {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #1e2438;
}

.btn-secondary,
.btn-primary {
  flex: 1;
  padding: 10px 16px;
  font-size: 11px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
}

.btn-secondary:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

.btn-primary {
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
}

.btn-primary:hover {
  background: #2860c0;
}
</style>
