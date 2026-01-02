<template>
  <div>
    <button
      class="legend-btn"
      type="button"
      aria-label="Confidence legend"
      @click="open = true"
      title="Confidence legend"
    >
      ?
    </button>

    <div v-if="open" class="modal-backdrop" @click.self="open = false">
      <div class="modal" role="dialog" aria-modal="true" aria-label="Confidence legend">
        <div class="modal-header">
          <div class="modal-title">Confidence legend</div>
          <button class="close-btn" type="button" @click="open = false" aria-label="Close">×</button>
        </div>

        <div class="modal-body">
          <section class="section">
            <h4>Levels</h4>

            <div class="row">
              <span class="badge" data-level="HIGH">HIGH</span>
              <div class="text">
                No hot rings (|Δ| &lt; 0.15mm), no pattern changes, warnings not worse.
              </div>
            </div>

            <div class="row">
              <span class="badge" data-level="MED">MED</span>
              <div class="text">
                Minor diffs (≤2 hot rings, ≤1 pattern change, warnings +2 max).
              </div>
            </div>

            <div class="row">
              <span class="badge" data-level="LOW">LOW</span>
              <div class="text">
                Significant differences, or no compare result yet.
              </div>
            </div>
          </section>

          <section class="section">
            <h4>Trend</h4>
            <div class="trend-row"><strong>↑</strong> Improved vs previous compare</div>
            <div class="trend-row"><strong>→</strong> Unchanged vs previous compare</div>
            <div class="trend-row"><strong>↓</strong> Decreased vs previous compare</div>
          </section>

          <section class="section">
            <h4>Notes</h4>
            <ul class="notes">
              <li>Confidence is a heuristic for reviewer speed, not correctness proof.</li>
              <li>Tooltip + legend text are generated from the same util to prevent drift.</li>
            </ul>
          </section>
        </div>

        <div class="modal-footer">
          <button class="ok-btn" type="button" @click="open = false">OK</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ConfidenceLegendModal.vue
 * Bundle 09: Confidence Legend Modal (UI-only)
 *
 * Shows a "?" button that opens a modal explaining confidence levels and trends.
 * Text is aligned with rmosConfidence.ts to prevent drift.
 */
import { ref } from "vue";

const open = ref(false);
</script>

<style scoped>
.legend-btn {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border: 1px solid #ccc;
  background: #fff;
  font-weight: 700;
  font-size: 0.75rem;
  line-height: 18px;
  cursor: pointer;
  margin-left: 6px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 9999;
}

.modal {
  width: min(560px, 96vw);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 16px 60px rgba(0,0,0,0.25);
  overflow: hidden;
}

.modal-header, .modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #eee;
}

.modal-footer {
  border-bottom: 0;
  border-top: 1px solid #eee;
  justify-content: flex-end;
}

.modal-title {
  font-weight: 700;
}

.close-btn {
  border: 0;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 14px;
  font-size: 0.9rem;
}

.section + .section {
  margin-top: 14px;
}

.row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 8px;
}

.text {
  color: #333;
}

.badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.badge[data-level="HIGH"] { background: #e6f7ee; color: #18794e; }
.badge[data-level="MED"]  { background: #fff4e5; color: #8a5a00; }
.badge[data-level="LOW"]  { background: #fdecea; color: #b42318; }

.trend-row { margin-top: 6px; }
.notes { margin: 8px 0 0 16px; }
.ok-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #ccc;
  background: #fff;
  cursor: pointer;
}
</style>
