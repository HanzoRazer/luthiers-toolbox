/**
 * Rosette Store - Bundle 31.0.5, 31.0.6
 *
 * Pinia store for Design-First Mode rosette editor state.
 */

import { defineStore } from "pinia";
import type { RosetteParamSpec } from "../types/rosette";
import type { PatternRecord, PatternSummary } from "../types/patternLibrary";
import type { GeneratorDescriptor } from "../types/generators";
import type { RosettePreviewSvgResponse } from "../types/preview";
import type { DesignSnapshot, SnapshotSummary } from "../types/designSnapshot";
import type { RosetteFeasibilitySummary, RiskBucket } from "../types/feasibility";

import { artPatternsClient } from "../api/artPatternsClient";
import { artGeneratorsClient } from "../api/artGeneratorsClient";
import { artPreviewClient } from "../api/artPreviewClient";
import { artSnapshotsClient } from "../api/artSnapshotsClient";
import { artFeasibilityClient } from "../api/artFeasibilityClient";
import { useToastStore } from "./toastStore";
import { useUiToastStore } from "./uiToastStore";
import { debounce } from "../utils/debounce";

function defaultSpec(): RosetteParamSpec {
  return {
    outer_diameter_mm: 120,
    inner_diameter_mm: 100,
    ring_params: [],
  };
}

export const useRosetteStore = defineStore("rosette", {
  state: () => ({
    // Canonical design
    currentParams: defaultSpec() as RosetteParamSpec,

    // Pattern library
    patterns: [] as PatternSummary[],
    selectedPattern: null as PatternRecord | null,
    patternsLoading: false,
    patternsError: "" as string,

    // Generators
    generators: [] as GeneratorDescriptor[],
    selectedGeneratorKey: "basic_rings@1" as string,
    generatorParams: {} as Record<string, any>,
    generatorsLoading: false,
    generatorsError: "" as string,
    generatorWarnings: [] as string[],

    // Preview
    preview: null as RosettePreviewSvgResponse | null,
    previewLoading: false,
    previewError: "" as string,

    // Snapshots
    snapshots: [] as SnapshotSummary[],
    snapshotsLoading: false,
    snapshotsError: "" as string,
    lastSavedSnapshot: null as DesignSnapshot | null,
    selectedSnapshotId: null as string | null,

    // Feasibility
    lastFeasibility: null as RosetteFeasibilitySummary | null,
    feasibilityLoading: false,
    feasibilityError: "" as string,

    // Auto-refresh settings
    autoRefreshEnabled: true,
    autoRefreshDebounceMs: 350,
    _lastAutoRefreshToken: 0,
    _debouncedAutoRefresh: null as (() => void) | null,

    // Ring focus (Bundle 32.3.1)
    focusedRingIndex: null as number | null,

    // Jump severity filter (Bundle 32.3.5)
    jumpSeverity: "RED_ONLY" as "RED_ONLY" | "RED_YELLOW",

    // Bundle 32.4.0: Undo history stack
    // Bundle 32.4.4: Typed HistoryEntry with labels
    historyStack: [] as HistoryEntry[],
    historyMax: 20,
    // Bundle 32.4.3: Redo stack
    redoStack: [] as HistoryEntry[],
    redoMax: 20,
  }),

  getters: {
    feasibilityRisk(): RiskBucket | null {
      return this.lastFeasibility?.risk_bucket || null;
    },

    isRedBlocked(): boolean {
      return (this.lastFeasibility?.risk_bucket || null) === "RED";
    },

    feasibilityLabel(): string {
      const f = this.lastFeasibility;
      if (!f) return "No feasibility yet";
      return `${f.risk_bucket} - Score ${Math.round(f.overall_score)} - ${f.estimated_cut_time_min.toFixed(1)} min`;
    },

    /** Ring at focusedRingIndex, or null (Bundle 32.3.1) */
    focusedRing(): any | null {
      if (this.focusedRingIndex == null) return null;
      return (this.currentParams?.ring_params ?? [])[this.focusedRingIndex] ?? null;
    },

    /** Selected snapshot object (Bundle 32.3.2) */
    selectedSnapshot(): SnapshotSummary | null {
      if (!this.selectedSnapshotId) return null;
      return this.snapshots.find((s) => s.snapshot_id === this.selectedSnapshotId) ?? null;
    },

    /** Problematic ring indices sorted by severity RED > YELLOW, filtered by jumpSeverity (Bundle 32.3.3, 32.3.5) */
    problematicRingIndices(): number[] {
      const snap = this.selectedSnapshot;
      if (!snap) return [];

      const diags: any[] =
        (snap as any).ring_diagnostics ??
        (snap as any).feasibility?.ring_diagnostics ??
        [];

      const severityRank = (r: string) =>
        r === "RED" ? 2 : r === "YELLOW" ? 1 : 0;

      const allow = (risk: string) => {
        if (this.jumpSeverity === "RED_ONLY") return risk === "RED";
        return risk === "RED" || risk === "YELLOW";
      };

      return diags
        .map((d: any) => ({
          idx: d.ring_index ?? d.ringIndex,
          risk: String(d.risk_bucket ?? d.riskBucket ?? "UNKNOWN"),
        }))
        .filter((x: any) => typeof x.idx === "number" && allow(x.risk))
        .sort((a: any, b: any) => severityRank(b.risk) - severityRank(a.risk))
        .map((x: any) => x.idx);
    },

    /** Total ring count from currentParams (Bundle 32.3.6) */
    totalRingCount(): number {
      return this.currentParams?.ring_params?.length ?? 0;
    },

    /** Count of RED-only rings from diagnostics (Bundle 32.3.6) */
    redRingCount(): number {
      const snap = this.selectedSnapshot;
      if (!snap) return 0;

      const diags: any[] =
        (snap as any).ring_diagnostics ??
        (snap as any).feasibility?.ring_diagnostics ??
        [];

      return diags.filter(
        (d: any) => String(d.risk_bucket ?? d.riskBucket) === "RED"
      ).length;
    },

    /** Current position in jump list { pos, total } (Bundle 32.3.6) */
    jumpRingPosition(): { pos: number; total: number } {
      const rings = this.problematicRingIndices;
      if (!rings.length) return { pos: 0, total: 0 };

      const current = this.focusedRingIndex;
      if (current == null) return { pos: 0, total: rings.length };

      const idx = rings.indexOf(current);
      // 1-based display; 0 if current ring not in list
      return { pos: idx >= 0 ? idx + 1 : 0, total: rings.length };
    },
  },

  actions: {
    // -------------------------
    // Patterns
    // -------------------------
    async loadPatterns(filters?: { q?: string; tag?: string; generator_key?: string }) {
      this.patternsLoading = true;
      this.patternsError = "";
      try {
        const res = await artPatternsClient.list({ ...filters, limit: 200 });
        this.patterns = res.items;
      } catch (e: any) {
        this.patternsError = e?.message || String(e);
      } finally {
        this.patternsLoading = false;
      }
    },

    async openPattern(pattern_id: string) {
      const toast = useToastStore();
      try {
        const rec = await artPatternsClient.get(pattern_id);
        this.selectedPattern = rec;
        this.selectedGeneratorKey = rec.generator_key;
        this.generatorParams = { ...(rec.params || {}) };
        toast.push("success", `Loaded pattern: ${rec.name}`);
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to load pattern");
      }
    },

    async saveCurrentAsPattern(opts: { name: string; description?: string; tags?: string[] }) {
      const toast = useToastStore();
      try {
        const rec = await artPatternsClient.create({
          name: opts.name,
          description: opts.description || null,
          tags: opts.tags || [],
          generator_key: this.selectedGeneratorKey,
          params: this.generatorParams || {},
        });
        toast.push("success", `Saved pattern: ${rec.name}`);
        await this.loadPatterns();
        this.selectedPattern = rec;
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to save pattern");
      }
    },

    async deleteSelectedPattern() {
      const toast = useToastStore();
      if (!this.selectedPattern) {
        toast.push("warning", "No pattern selected.");
        return;
      }
      try {
        await artPatternsClient.delete(this.selectedPattern.pattern_id);
        toast.push("success", "Pattern deleted.");
        this.selectedPattern = null;
        await this.loadPatterns();
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to delete pattern");
      }
    },

    // -------------------------
    // Generators
    // -------------------------
    async loadGenerators() {
      this.generatorsLoading = true;
      this.generatorsError = "";
      try {
        const res = await artGeneratorsClient.list();
        this.generators = res.generators;
        if (!this.generators.find((g) => g.generator_key === this.selectedGeneratorKey) && this.generators.length) {
          this.selectedGeneratorKey = this.generators[0].generator_key;
        }
      } catch (e: any) {
        this.generatorsError = e?.message || String(e);
      } finally {
        this.generatorsLoading = false;
      }
    },

    async generateSpecFromGenerator() {
      const toast = useToastStore();
      this.generatorWarnings = [];
      try {
        const res = await artGeneratorsClient.generate(this.selectedGeneratorKey, {
          outer_diameter_mm: this.currentParams.outer_diameter_mm,
          inner_diameter_mm: this.currentParams.inner_diameter_mm,
          params: this.generatorParams || {},
        });
        this.currentParams = res.spec;
        this.generatorWarnings = res.warnings || [];
        if (this.generatorWarnings.length) {
          toast.push("warning", `Generated with warnings: ${this.generatorWarnings[0]}`);
        } else {
          toast.push("success", "Generated RosetteParamSpec.");
        }
        this.requestAutoRefresh();
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to generate design");
      }
    },

    // -------------------------
    // Preview
    // -------------------------
    async refreshPreview() {
      this.previewLoading = true;
      this.previewError = "";
      try {
        this.preview = await artPreviewClient.previewSvg({ spec: this.currentParams, size_px: 520, padding_px: 20 });
      } catch (e: any) {
        this.previewError = e?.message || String(e);
        this.preview = null;
      } finally {
        this.previewLoading = false;
      }
    },

    // -------------------------
    // Feasibility
    // -------------------------
    async refreshFeasibility() {
      this.feasibilityLoading = true;
      this.feasibilityError = "";
      try {
        const res = await artFeasibilityClient.batch({ specs: [this.currentParams] });
        const s = res.summaries?.[0] || null;
        this.lastFeasibility = s;
      } catch (e: any) {
        this.feasibilityError = e?.message || String(e);
        this.lastFeasibility = null;
      } finally {
        this.feasibilityLoading = false;
      }
    },

    async refreshPreviewAndFeasibility() {
      await Promise.allSettled([this.refreshPreview(), this.refreshFeasibility()]);
    },

    setCurrentParams(next: RosetteParamSpec) {
      this.currentParams = next;
    },

    requestAutoRefresh() {
      if (!this.autoRefreshEnabled) return;
      const token = ++this._lastAutoRefreshToken;

      if (!this._debouncedAutoRefresh) {
        this._debouncedAutoRefresh = debounce(async () => {
          if (token !== this._lastAutoRefreshToken) return;
          await this.refreshPreviewAndFeasibility();
        }, this.autoRefreshDebounceMs);
      }
      this._debouncedAutoRefresh();
    },

    // -------------------------
    // Ring Focus (Bundle 32.3.1)
    // -------------------------
    focusRing(index: number) {
      this.focusedRingIndex = index;
    },

    clearRingFocus() {
      this.focusedRingIndex = null;
    },

    /** Toggle jump severity filter between RED_ONLY and RED_YELLOW (Bundle 32.3.5) */
    toggleJumpSeverity() {
      this.jumpSeverity = this.jumpSeverity === "RED_ONLY" ? "RED_YELLOW" : "RED_ONLY";
    },

    /** Jump to next problematic ring, cycling through RED then YELLOW (Bundle 32.3.3) */
    jumpToNextProblemRing() {
      const rings = this.problematicRingIndices;
      if (!rings.length) return;

      const current = this.focusedRingIndex;
      const pos = current == null ? -1 : rings.indexOf(current);

      const nextIdx = rings[(pos + 1) % rings.length];
      this.focusRing(nextIdx);
    },

    /** Jump to previous problematic ring (Bundle 32.3.4) */
    jumpToPreviousProblemRing() {
      const rings = this.problematicRingIndices;
      if (!rings.length) return;

      const current = this.focusedRingIndex;
      const pos = current == null ? rings.length : rings.indexOf(current);

      const prevIdx = rings[(pos - 1 + rings.length) % rings.length];
      this.focusRing(prevIdx);
    },

    /** Jump to worst (first) problematic ring (Bundle 32.3.7) */
    jumpToWorstProblemRing() {
      const rings = this.problematicRingIndices; // already sorted worst-first
      if (!rings.length) return;
      this.focusRing(rings[0]);
    },

    // -------------------------
    // Snapshots
    // -------------------------
    selectSnapshot(snapshotId: string | null) {
      if (this.selectedSnapshotId === snapshotId) {
        this.selectedSnapshotId = null;
      } else {
        this.selectedSnapshotId = snapshotId;
      }
    },

    async loadRecentSnapshots(filters?: { q?: string; tag?: string; pattern_id?: string }) {
      this.snapshotsLoading = true;
      this.snapshotsError = "";
      try {
        const res = await artSnapshotsClient.listRecent({ ...filters, limit: 50 });
        this.snapshots = res.items;
      } catch (e: any) {
        this.snapshotsError = e?.message || String(e);
      } finally {
        this.snapshotsLoading = false;
      }
    },

    async saveSnapshot(opts: { name: string; notes?: string; tags?: string[] }) {
      const toast = useToastStore();

      if (this.isRedBlocked) {
        toast.push("warning", "Blocked: Feasibility is RED. Adjust design before saving a snapshot.");
        return;
      }

      try {
        const snap = await artSnapshotsClient.create({
          name: opts.name,
          notes: opts.notes || null,
          tags: opts.tags || [],
          pattern_id: this.selectedPattern?.pattern_id || null,
          context_refs: { mode: "MODE_A" },
          rosette_params: this.currentParams,
          feasibility: this.lastFeasibility || null,
        });
        this.lastSavedSnapshot = snap;
        toast.push("success", `Snapshot saved: ${snap.name}`);
        await this.loadRecentSnapshots();
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to save snapshot");
      }
    },

    async loadSnapshot(snapshot_id: string) {
      const toast = useToastStore();
      try {
        const snap = await artSnapshotsClient.get(snapshot_id);
        this.currentParams = snap.rosette_params;
        this.lastFeasibility = (snap.feasibility as any) || null;
        toast.push("success", `Loaded snapshot: ${snap.name}`);
        this.requestAutoRefresh();
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to load snapshot");
      }
    },

    async exportSnapshot(snapshot_id: string) {
      const toast = useToastStore();
      try {
        const res = await artSnapshotsClient.export(snapshot_id);
        const blob = new Blob([JSON.stringify(res.snapshot, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${snapshot_id}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        toast.push("success", "Snapshot exported.");
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to export snapshot");
      }
    },

    async importSnapshotFromJsonText(jsonText: string) {
      const toast = useToastStore();
      try {
        const parsed = JSON.parse(jsonText);
        const snap = await artSnapshotsClient.import({ snapshot: parsed });
        toast.push("success", `Imported snapshot: ${snap.name}`);
        await this.loadRecentSnapshots();
        this.currentParams = snap.rosette_params;
        this.lastFeasibility = (snap.feasibility as any) || null;
      } catch (e: any) {
        toast.push("error", e?.message || "Failed to import snapshot");
      }
    },

    // -------------------------
    // Bundle 32.4.0: History + Nudge
    // Bundle 32.4.3: Redo stack support
    // -------------------------

    /** Clone helper (structuredClone with JSON fallback) */
    _clone(v: any): any {
      const sc = (globalThis as any).structuredClone;
      return sc ? sc(v) : JSON.parse(JSON.stringify(v));
    },

    /** Push a snapshot to history stack before edits (Bundle 32.4.4: with label) */
    _pushHistorySnapshot(label = "Edit", params?: any) {
      // Any new edit invalidates redo history (canonical behavior)
      this.redoStack = [];

      const src = params ?? this.currentParams;
      if (!src) return;

      try {
        const snap = this._clone(src);
        this.historyStack.push({ params: snap, label, ts: Date.now() });
        if (this.historyStack.length > this.historyMax) this.historyStack.shift();
      } catch {
        // fail gracefully
      }
    },

    /** Check if edits are allowed (blocked when RED) */
    _canEditNow(): boolean {
      return !this.isRedBlocked;
    },

    /** Set max history size */
    setHistoryMax(n: number) {
      const v = Math.max(5, Math.min(50, n));
      this.historyMax = v;
      if (this.historyStack.length > v) {
        this.historyStack = this.historyStack.slice(this.historyStack.length - v);
      }
    },

    /** Undo last edit (pushes current → redo before reverting) */
    undoLastEdit() {
      if (!this.historyStack.length) return;

      const prev = this.historyStack.pop();
      if (!prev) return;

      // Push current into redo before reverting (Bundle 32.4.4: preserve label)
      try {
        const curSnap = this._clone(this.currentParams);
        this.redoStack.push({ params: curSnap, label: prev.label, ts: Date.now() });
        if (this.redoStack.length > this.redoMax) this.redoStack.shift();
      } catch {
        // ignore
      }

      this.currentParams = prev.params;
    },

    /** Redo last undone edit (pushes current → undo before applying redo) */
    redoLastEdit() {
      if (!this.redoStack.length) return;

      const next = this.redoStack.pop();
      if (!next) return;

      // Push current into undo history before applying redo (Bundle 32.4.4: preserve label)
      try {
        const curSnap = this._clone(this.currentParams);
        this.historyStack.push({ params: curSnap, label: next.label, ts: Date.now() });
        if (this.historyStack.length > this.historyMax) this.historyStack.shift();
      } catch {
        // ignore
      }

      this.currentParams = next.params;
    },

    /**
     * Safe single-ring width nudge.
     * - Captures history before change
     * - Blocks when risk is RED
     * - Clamps widths to a minimum
     */
    nudgeRingWidth(ringIndex: number, deltaMm: number, opts?: { minWidthMm?: number }) {
      if (!this.currentParams?.ring_params?.length) return;
      if (ringIndex < 0 || ringIndex >= this.currentParams.ring_params.length) return;

      if (!this._canEditNow()) {
        const toast = useUiToastStore();
        toast.push({
          level: "warn",
          message: "Edit blocked (RED risk)",
          detail: "Resolve feasibility warnings or reduce risk before using fix-it actions.",
          durationMs: 3200,
        });
        return;
      }

      const minWidthMm = opts?.minWidthMm ?? 0.2;

      // History snapshot BEFORE change (Bundle 32.4.4: with label)
      this._pushHistorySnapshot(
        `Ring ${ringIndex + 1} ${deltaMm > 0 ? "+" : ""}${deltaMm.toFixed(2)}mm`
      );

      // Clone current params
      const next = JSON.parse(JSON.stringify(this.currentParams));
      const ring = next.ring_params[ringIndex];
      const cur = Number(ring.width_mm ?? 0);
      const nextW = Math.max(minWidthMm, cur + deltaMm);
      ring.width_mm = nextW;

      this.currentParams = next;
    },

    /**
     * Safe "distribute" nudge:
     * widen/shrink target ring by delta, and compensate neighbors equally
     * so total ring-width sum stays ~constant (local conservation).
     */
    nudgeRingWidthDistribute(ringIndex: number, deltaMm: number, opts?: { minWidthMm?: number }) {
      if (!this.currentParams?.ring_params?.length) return;
      if (ringIndex < 0 || ringIndex >= this.currentParams.ring_params.length) return;

      if (!this._canEditNow()) {
        const toast = useUiToastStore();
        toast.push({
          level: "warn",
          message: "Edit blocked (RED risk)",
          detail: "Resolve feasibility warnings or reduce risk before using fix-it actions.",
          durationMs: 3200,
        });
        return;
      }

      const minWidthMm = opts?.minWidthMm ?? 0.2;
      const rings = this.currentParams.ring_params;
      const left = ringIndex - 1;
      const right = ringIndex + 1;

      // need at least one neighbor to distribute
      if (left < 0 && right >= rings.length) return;

      // Bundle 32.4.4: with distribute label
      this._pushHistorySnapshot(
        `Ring ${ringIndex + 1} ${deltaMm > 0 ? "+" : ""}${deltaMm.toFixed(2)}↔ (distribute)`
      );

      const next = JSON.parse(JSON.stringify(this.currentParams));

      const getW = (r: any) => Number(r.width_mm ?? 0);
      const setW = (r: any, w: number) => { r.width_mm = w; };

      const t = next.ring_params[ringIndex];
      const tW = getW(t);
      const tNext = Math.max(minWidthMm, tW + deltaMm);

      const neighbors: number[] = [];
      if (left >= 0) neighbors.push(left);
      if (right < next.ring_params.length) neighbors.push(right);

      const compTotal = tNext - tW;
      const per = neighbors.length ? compTotal / neighbors.length : 0;

      setW(t, tNext);

      for (const ni of neighbors) {
        const r = next.ring_params[ni];
        const w = getW(r);
        const wNext = Math.max(minWidthMm, w - per);
        setW(r, wNext);
      }

      this.currentParams = next;
    },

    // -------------------------
    // Bundle 32.4.2: History revert + clear
    // -------------------------

    /** Revert to a specific history index (clears redo - new branch) */
    revertToHistoryIndex(absIndex: number) {
      const stack = this.historyStack ?? [];
      if (!stack.length) return;
      if (absIndex < 0 || absIndex >= stack.length) return;

      // Revert = new branch, clears redo
      this.redoStack = [];

      // Save current state into history before reverting (Bundle 32.4.4: with label)
      try {
        this._pushHistorySnapshot("Revert (before)");
      } catch {
        // ignore
      }

      const target = stack[absIndex];
      if (!target) return;

      // Drop everything newer than target (so revert is deterministic)
      this.historyStack = stack.slice(0, absIndex);

      this.currentParams = target.params;
    },

    /** Clear all history (undo + redo) */
    clearHistory() {
      this.historyStack = [];
      this.redoStack = [];
    },
  },
});
