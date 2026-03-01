<script setup lang="ts">
/**
 * EstimatorExportPanel - Export estimates to various formats
 *
 * Features:
 * - Export to JSON (full data)
 * - Export to CSV (WBS breakdown)
 * - Copy to clipboard
 * - Download as file
 */
import { computed } from "vue";
import type { EstimateRequest, EstimateResult } from "@/types/businessEstimator";

const props = defineProps<{
  request: EstimateRequest;
  estimate: EstimateResult;
}>();

// ============================================================================
// COMPUTED
// ============================================================================

const jsonExport = computed(() => {
  return JSON.stringify(
    {
      exported_at: new Date().toISOString(),
      version: "1.0",
      request: props.request,
      result: props.estimate,
    },
    null,
    2
  );
});

const csvExport = computed(() => {
  const headers = [
    "Task ID",
    "Task Name",
    "Base Hours",
    "Adjusted Hours",
    "Labor Cost",
    "Percent of Total",
  ];

  const rows = props.estimate.wbs_tasks.map((task) => [
    task.task_id,
    `"${task.task_name}"`,
    task.base_hours.toFixed(2),
    task.adjusted_hours.toFixed(2),
    `$${task.labor_cost.toFixed(2)}`,
    ((task.adjusted_hours / props.estimate.total_hours) * 100).toFixed(1) + "%",
  ]);

  // Add summary rows
  rows.push([]);
  rows.push(["", "TOTAL", "", "", props.estimate.total_hours.toFixed(2), "100%"]);
  rows.push([]);
  rows.push(["", "Labor Cost", "", "", `$${props.estimate.labor_cost_per_unit.toFixed(2)}`, ""]);
  rows.push(["", "Material Cost", "", "", `$${props.estimate.material_cost_per_unit.toFixed(2)}`, ""]);
  rows.push(["", "Total Cost", "", "", `$${props.estimate.total_cost_per_unit.toFixed(2)}`, ""]);

  return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
});

const summaryText = computed(() => {
  const lines = [
    "ENGINEERING ESTIMATE SUMMARY",
    "============================",
    "",
    `Instrument: ${formatInstrumentType(props.estimate.instrument_type)}`,
    `Experience: ${props.estimate.experience_level} (${props.estimate.experience_multiplier}x)`,
    `Confidence: ${props.estimate.confidence_level}`,
    "",
    "HOURS",
    "-----",
    `First Unit:    ${props.estimate.first_unit_hours.toFixed(1)}h`,
    `Average/Unit:  ${props.estimate.average_hours_per_unit.toFixed(1)}h`,
    `Total Hours:   ${props.estimate.total_hours.toFixed(1)}h`,
    "",
    "COSTS",
    "-----",
    `Labor:     $${props.estimate.labor_cost_per_unit.toFixed(2)}`,
    `Materials: $${props.estimate.material_cost_per_unit.toFixed(2)}`,
    `Total:     $${props.estimate.total_cost_per_unit.toFixed(2)}`,
    "",
    `Range: $${props.estimate.estimate_range_low.toFixed(0)} - $${props.estimate.estimate_range_high.toFixed(0)}`,
    "",
    "COMPLEXITY FACTORS",
    "------------------",
    ...Object.entries(props.estimate.complexity_factors_applied).map(
      ([key, val]) => `${key}: ${(val as number).toFixed(2)}x`
    ),
    "",
    `Combined Multiplier: ${props.estimate.total_complexity_multiplier.toFixed(2)}x`,
  ];

  if (props.estimate.notes.length > 0) {
    lines.push("", "NOTES", "-----", ...props.estimate.notes.map((n) => `• ${n}`));
  }

  return lines.join("\n");
});

// ============================================================================
// ACTIONS
// ============================================================================

async function copyToClipboard(content: string, type: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(content);
    alert(`${type} copied to clipboard!`);
  } catch {
    // Fallback
    const textarea = document.createElement("textarea");
    textarea.value = content;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    alert(`${type} copied to clipboard!`);
  }
}

function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function exportJSON(): void {
  const filename = `estimate_${props.estimate.instrument_type}_${Date.now()}.json`;
  downloadFile(jsonExport.value, filename, "application/json");
}

function exportCSV(): void {
  const filename = `estimate_wbs_${props.estimate.instrument_type}_${Date.now()}.csv`;
  downloadFile(csvExport.value, filename, "text/csv");
}

function exportSummary(): void {
  const filename = `estimate_summary_${props.estimate.instrument_type}_${Date.now()}.txt`;
  downloadFile(summaryText.value, filename, "text/plain");
}

function formatInstrumentType(type: string): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
</script>

<template>
  <div class="export-panel">
    <h3>Export Estimate</h3>

    <!-- Export Options -->
    <div class="export-grid">
      <!-- JSON Export -->
      <div class="export-card">
        <div class="export-icon">{ }</div>
        <div class="export-info">
          <div class="export-title">JSON</div>
          <div class="export-desc">Full data for import/backup</div>
        </div>
        <div class="export-actions">
          <button type="button" @click="copyToClipboard(jsonExport, 'JSON')">
            Copy
          </button>
          <button type="button" @click="exportJSON">Download</button>
        </div>
      </div>

      <!-- CSV Export -->
      <div class="export-card">
        <div class="export-icon">CSV</div>
        <div class="export-info">
          <div class="export-title">CSV</div>
          <div class="export-desc">WBS breakdown for spreadsheets</div>
        </div>
        <div class="export-actions">
          <button type="button" @click="copyToClipboard(csvExport, 'CSV')">
            Copy
          </button>
          <button type="button" @click="exportCSV">Download</button>
        </div>
      </div>

      <!-- Summary Export -->
      <div class="export-card">
        <div class="export-icon">TXT</div>
        <div class="export-info">
          <div class="export-title">Summary</div>
          <div class="export-desc">Plain text for notes/docs</div>
        </div>
        <div class="export-actions">
          <button type="button" @click="copyToClipboard(summaryText, 'Summary')">
            Copy
          </button>
          <button type="button" @click="exportSummary">Download</button>
        </div>
      </div>
    </div>

    <!-- Preview -->
    <details class="preview-section">
      <summary>Preview JSON</summary>
      <pre class="preview-content">{{ jsonExport }}</pre>
    </details>
  </div>
</template>

<style scoped>
.export-panel {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.export-panel h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0 0 16px;
}

/* Export Grid */
.export-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 12px;
}

.export-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a2040;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #4080f0;
  flex-shrink: 0;
}

.export-info {
  flex: 1;
  min-width: 0;
}

.export-title {
  font-size: 12px;
  font-weight: 600;
  color: #c0c8e0;
  margin-bottom: 2px;
}

.export-desc {
  font-size: 10px;
  color: #506090;
}

.export-actions {
  display: flex;
  gap: 6px;
}

.export-actions button {
  padding: 6px 10px;
  font-size: 9px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.export-actions button:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

.export-actions button:last-child {
  background: #2050a0;
  border-color: #3060c0;
  color: #e0e8ff;
}

.export-actions button:last-child:hover {
  background: #2860c0;
}

/* Preview Section */
.preview-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #1e2438;
}

.preview-section summary {
  font-size: 10px;
  letter-spacing: 1px;
  color: #6080b0;
  cursor: pointer;
  text-transform: uppercase;
}

.preview-section summary:hover {
  color: #80a0d0;
}

.preview-content {
  margin-top: 12px;
  padding: 12px;
  background: #0a0d14;
  border: 1px solid #1e2438;
  border-radius: 4px;
  font-size: 10px;
  color: #8090b0;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}
</style>
