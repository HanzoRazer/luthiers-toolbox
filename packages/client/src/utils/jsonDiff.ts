/**
 * JSON Diff Utility
 *
 * Dependency-free JSON diff algorithm for comparing run artifacts.
 * Produces a flat list of differences with paths.
 *
 * Target: packages/client/src/utils/jsonDiff.ts
 */

// ============================================================================
// Types
// ============================================================================

export type DiffOp = "added" | "removed" | "changed";

export interface DiffItem {
  path: string;
  op: DiffOp;
  a?: any;
  b?: any;
}

export interface DiffSummary {
  added: number;
  removed: number;
  changed: number;
  total: number;
}

// ============================================================================
// Core Diff Algorithm
// ============================================================================

/**
 * Compare two JSON objects and return a flat list of differences.
 *
 * @param a - First object (typically "A" artifact)
 * @param b - Second object (typically "B" artifact)
 * @param prefix - Path prefix for nested keys (used recursively)
 * @returns Array of diff items
 */
export function diffJson(a: any, b: any, prefix = ""): DiffItem[] {
  const diffs: DiffItem[] = [];

  // Handle null/undefined
  if (a === null || a === undefined) {
    if (b !== null && b !== undefined) {
      diffs.push({ path: prefix || "(root)", op: "added", a, b });
    }
    return diffs;
  }

  if (b === null || b === undefined) {
    diffs.push({ path: prefix || "(root)", op: "removed", a, b });
    return diffs;
  }

  // Different types
  if (typeof a !== typeof b) {
    diffs.push({ path: prefix || "(root)", op: "changed", a, b });
    return diffs;
  }

  // Primitives
  if (typeof a !== "object") {
    if (a !== b) {
      diffs.push({ path: prefix || "(root)", op: "changed", a, b });
    }
    return diffs;
  }

  // Arrays
  if (Array.isArray(a) && Array.isArray(b)) {
    const maxLen = Math.max(a.length, b.length);
    for (let i = 0; i < maxLen; i++) {
      const itemPath = prefix ? `${prefix}[${i}]` : `[${i}]`;
      if (i >= a.length) {
        diffs.push({ path: itemPath, op: "added", a: undefined, b: b[i] });
      } else if (i >= b.length) {
        diffs.push({ path: itemPath, op: "removed", a: a[i], b: undefined });
      } else {
        diffs.push(...diffJson(a[i], b[i], itemPath));
      }
    }
    return diffs;
  }

  // Objects
  const allKeys = new Set([...Object.keys(a), ...Object.keys(b)]);

  for (const key of allKeys) {
    const keyPath = prefix ? `${prefix}.${key}` : key;
    const inA = key in a;
    const inB = key in b;

    if (!inA && inB) {
      diffs.push({ path: keyPath, op: "added", a: undefined, b: b[key] });
    } else if (inA && !inB) {
      diffs.push({ path: keyPath, op: "removed", a: a[key], b: undefined });
    } else {
      diffs.push(...diffJson(a[key], b[key], keyPath));
    }
  }

  return diffs;
}

// ============================================================================
// Summary
// ============================================================================

/**
 * Summarize diff results into counts.
 */
export function summarizeDiff(diffs: DiffItem[]): DiffSummary {
  let added = 0;
  let removed = 0;
  let changed = 0;

  for (const d of diffs) {
    switch (d.op) {
      case "added":
        added++;
        break;
      case "removed":
        removed++;
        break;
      case "changed":
        changed++;
        break;
    }
  }

  return { added, removed, changed, total: diffs.length };
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Check if two values are deeply equal.
 */
export function deepEqual(a: any, b: any): boolean {
  if (a === b) return true;
  if (a === null || b === null) return false;
  if (typeof a !== typeof b) return false;
  if (typeof a !== "object") return a === b;

  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;

  return keysA.every((k) => deepEqual(a[k], b[k]));
}

/**
 * Format a diff path for display.
 */
export function formatPath(path: string): string {
  return path
    .replace(/\[(\d+)\]/g, "[$1]")
    .replace(/^\./, "");
}

/**
 * Group diffs by top-level key.
 */
export function groupByTopLevel(diffs: DiffItem[]): Map<string, DiffItem[]> {
  const groups = new Map<string, DiffItem[]>();

  for (const d of diffs) {
    const topKey = d.path.split(/[.\[]/)[0] || "(root)";
    if (!groups.has(topKey)) {
      groups.set(topKey, []);
    }
    groups.get(topKey)!.push(d);
  }

  return groups;
}

// ============================================================================
// Default Export
// ============================================================================

export default {
  diffJson,
  summarizeDiff,
  deepEqual,
  formatPath,
  groupByTopLevel,
};
