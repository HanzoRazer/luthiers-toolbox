<template>
  <div class="csv-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="rows">{{ rows.length }} rows × {{ columns.length }} cols</span>
      <button
        class="copy-btn"
        @click="copyToClipboard"
      >
        📋 Copy
      </button>
    </div>

    <div class="table-container">
      <table v-if="rows.length > 0">
        <thead>
          <tr>
            <th
              v-for="(col, i) in columns"
              :key="i"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, ri) in displayRows"
            :key="ri"
          >
            <td
              v-for="(cell, ci) in row"
              :key="ci"
              :title="cell"
            >
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-else
        class="empty"
      >
        No data
      </div>
    </div>

    <div
      v-if="rows.length > maxDisplayRows"
      class="truncation-notice"
    >
      Showing {{ maxDisplayRows }} of {{ rows.length }} rows
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

const maxDisplayRows = 100;

const csvText = computed(() => {
  return new TextDecoder("utf-8").decode(props.bytes);
});

const rows = computed<string[][]>(() => {
  const lines = csvText.value.trim().split(/\r?\n/);
  return lines.map((line) => parseCSVLine(line));
});

const columns = computed<string[]>(() => {
  return rows.value[0] ?? [];
});

const displayRows = computed<string[][]>(() => {
  // Skip header row, limit to maxDisplayRows
  return rows.value.slice(1, maxDisplayRows + 1);
});

/**
 * Simple CSV line parser (handles basic quoting).
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  result.push(current.trim());
  return result;
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(csvText.value);
  } catch (e) {
    console.warn("Failed to copy CSV to clipboard:", e);
  }
}
</script>

<style scoped>
.csv-renderer {
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--vt-c-divider-light, #333);
}

.label {
  font-family: monospace;
  background: var(--vt-c-bg-mute, #2a2a2a);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.rows {
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
}

.copy-btn {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
}

.copy-btn:hover {
  background: var(--vt-c-bg, #252525);
}

.table-container {
  max-height: 400px;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-family: monospace;
  font-size: 0.8rem;
}

thead {
  position: sticky;
  top: 0;
  background: var(--vt-c-bg-mute, #2a2a2a);
}

th,
td {
  padding: 0.35rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--vt-c-divider-light, #333);
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

th {
  font-weight: 600;
  color: var(--vt-c-text-1, #fff);
}

td {
  color: var(--vt-c-text-2, #ccc);
}

tr:hover td {
  background: var(--vt-c-bg-mute, #252525);
}

.empty {
  padding: 2rem;
  text-align: center;
  color: var(--vt-c-text-3, #888);
}

.truncation-notice {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  color: var(--vt-c-text-3, #888);
  border-top: 1px solid var(--vt-c-divider-light, #333);
}
</style>
