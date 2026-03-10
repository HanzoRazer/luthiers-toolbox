/**
 * toolpathAnnotations — P5 Annotations & Bookmarks System
 *
 * Provides annotation and bookmark functionality for toolpath segments:
 * - Bookmarks: Quick jump points with labels
 * - Annotations: Notes attached to segments or positions
 * - Categories: Organize annotations by type
 * - Persistence: Save/load to localStorage
 * - Export: Export annotations as JSON
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AnnotationType = "bookmark" | "note" | "warning" | "issue" | "todo";

export interface Annotation {
  /** Unique ID */
  id: string;
  /** Annotation type */
  type: AnnotationType;
  /** Short label/title */
  label: string;
  /** Full description/note */
  description: string;
  /** Segment index (null = position-based) */
  segmentIndex: number | null;
  /** 3D position */
  position: [number, number, number];
  /** G-code line number */
  lineNumber: number | null;
  /** Color for display */
  color: string;
  /** Icon for display */
  icon: string;
  /** Created timestamp */
  createdAt: number;
  /** Updated timestamp */
  updatedAt: number;
}

export interface AnnotationCategory {
  type: AnnotationType;
  label: string;
  icon: string;
  color: string;
  description: string;
}

export interface AnnotationExport {
  version: string;
  exportedAt: number;
  gcodeHash: string;
  annotations: Annotation[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const ANNOTATION_CATEGORIES: AnnotationCategory[] = [
  {
    type: "bookmark",
    label: "Bookmark",
    icon: "🔖",
    color: "#4a90d9",
    description: "Quick jump point",
  },
  {
    type: "note",
    label: "Note",
    icon: "📝",
    color: "#2ecc71",
    description: "General observation",
  },
  {
    type: "warning",
    label: "Warning",
    icon: "⚠️",
    color: "#f39c12",
    description: "Potential issue",
  },
  {
    type: "issue",
    label: "Issue",
    icon: "🚨",
    color: "#e74c3c",
    description: "Problem found",
  },
  {
    type: "todo",
    label: "To-Do",
    icon: "☐",
    color: "#9b59b6",
    description: "Action needed",
  },
];

const STORAGE_KEY = "toolpath-annotations-";

// ---------------------------------------------------------------------------
// Helper Functions
// ---------------------------------------------------------------------------

function generateId(): string {
  return `ann_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function getCategoryInfo(type: AnnotationType): AnnotationCategory {
  return ANNOTATION_CATEGORIES.find((c) => c.type === type) ?? ANNOTATION_CATEGORIES[0];
}

/** Simple hash for G-code to identify annotation sets */
function hashGcode(gcode: string): string {
  let hash = 0;
  for (let i = 0; i < Math.min(gcode.length, 10000); i++) {
    const char = gcode.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

// ---------------------------------------------------------------------------
// Annotation Manager Class
// ---------------------------------------------------------------------------

export class AnnotationManager {
  private annotations: Map<string, Annotation> = new Map();
  private gcodeHash: string = "";
  private listeners: Set<() => void> = new Set();

  constructor() {
    this.annotations = new Map();
  }

  // ── Initialization ──────────────────────────────────────────────────────

  /**
   * Initialize with G-code, loading any saved annotations
   */
  init(gcode: string): void {
    this.gcodeHash = hashGcode(gcode);
    this.load();
  }

  /**
   * Clear all annotations (for new G-code)
   */
  reset(): void {
    this.annotations.clear();
    this.gcodeHash = "";
    this.notifyListeners();
  }

  // ── CRUD Operations ─────────────────────────────────────────────────────

  /**
   * Add a new annotation
   */
  add(params: {
    type: AnnotationType;
    label: string;
    description?: string;
    segmentIndex?: number | null;
    position: [number, number, number];
    lineNumber?: number | null;
  }): Annotation {
    const category = getCategoryInfo(params.type);
    const now = Date.now();

    const annotation: Annotation = {
      id: generateId(),
      type: params.type,
      label: params.label,
      description: params.description ?? "",
      segmentIndex: params.segmentIndex ?? null,
      position: params.position,
      lineNumber: params.lineNumber ?? null,
      color: category.color,
      icon: category.icon,
      createdAt: now,
      updatedAt: now,
    };

    this.annotations.set(annotation.id, annotation);
    this.save();
    this.notifyListeners();

    return annotation;
  }

  /**
   * Update an existing annotation
   */
  update(id: string, updates: Partial<Omit<Annotation, "id" | "createdAt">>): boolean {
    const annotation = this.annotations.get(id);
    if (!annotation) return false;

    // Update type-dependent fields
    if (updates.type && updates.type !== annotation.type) {
      const category = getCategoryInfo(updates.type);
      updates.color = category.color;
      updates.icon = category.icon;
    }

    Object.assign(annotation, updates, { updatedAt: Date.now() });
    this.save();
    this.notifyListeners();

    return true;
  }

  /**
   * Remove an annotation
   */
  remove(id: string): boolean {
    const deleted = this.annotations.delete(id);
    if (deleted) {
      this.save();
      this.notifyListeners();
    }
    return deleted;
  }

  /**
   * Get annotation by ID
   */
  get(id: string): Annotation | undefined {
    return this.annotations.get(id);
  }

  /**
   * Get all annotations
   */
  getAll(): Annotation[] {
    return Array.from(this.annotations.values());
  }

  /**
   * Get annotations by type
   */
  getByType(type: AnnotationType): Annotation[] {
    return this.getAll().filter((a) => a.type === type);
  }

  /**
   * Get annotations for a specific segment
   */
  getBySegment(segmentIndex: number): Annotation[] {
    return this.getAll().filter((a) => a.segmentIndex === segmentIndex);
  }

  /**
   * Get bookmarks only (for quick navigation)
   */
  getBookmarks(): Annotation[] {
    return this.getByType("bookmark").sort((a, b) => {
      // Sort by segment index if available, otherwise by creation time
      if (a.segmentIndex !== null && b.segmentIndex !== null) {
        return a.segmentIndex - b.segmentIndex;
      }
      return a.createdAt - b.createdAt;
    });
  }

  /**
   * Count annotations by type
   */
  getCounts(): Record<AnnotationType, number> {
    const counts: Record<AnnotationType, number> = {
      bookmark: 0,
      note: 0,
      warning: 0,
      issue: 0,
      todo: 0,
    };

    for (const ann of this.annotations.values()) {
      counts[ann.type]++;
    }

    return counts;
  }

  // ── Persistence ─────────────────────────────────────────────────────────

  /**
   * Save annotations to localStorage
   */
  private save(): void {
    if (!this.gcodeHash) return;

    try {
      const data = JSON.stringify(this.getAll());
      localStorage.setItem(STORAGE_KEY + this.gcodeHash, data);
    } catch {
      // localStorage full or unavailable
      console.warn("Failed to save annotations to localStorage");
    }
  }

  /**
   * Load annotations from localStorage
   */
  private load(): void {
    if (!this.gcodeHash) return;

    try {
      const data = localStorage.getItem(STORAGE_KEY + this.gcodeHash);
      if (data) {
        const annotations: Annotation[] = JSON.parse(data);
        this.annotations.clear();
        for (const ann of annotations) {
          this.annotations.set(ann.id, ann);
        }
        this.notifyListeners();
      }
    } catch {
      // Invalid data or localStorage unavailable
      console.warn("Failed to load annotations from localStorage");
    }
  }

  /**
   * Export annotations as JSON
   */
  export(): AnnotationExport {
    return {
      version: "1.0",
      exportedAt: Date.now(),
      gcodeHash: this.gcodeHash,
      annotations: this.getAll(),
    };
  }

  /**
   * Import annotations from JSON
   */
  import(data: AnnotationExport): number {
    let imported = 0;

    for (const ann of data.annotations) {
      // Generate new ID to avoid conflicts
      const newAnn: Annotation = {
        ...ann,
        id: generateId(),
        updatedAt: Date.now(),
      };
      this.annotations.set(newAnn.id, newAnn);
      imported++;
    }

    if (imported > 0) {
      this.save();
      this.notifyListeners();
    }

    return imported;
  }

  /**
   * Clear all saved annotations for this G-code
   */
  clearSaved(): void {
    if (this.gcodeHash) {
      localStorage.removeItem(STORAGE_KEY + this.gcodeHash);
    }
    this.annotations.clear();
    this.notifyListeners();
  }

  // ── Listeners ───────────────────────────────────────────────────────────

  /**
   * Subscribe to annotation changes
   */
  subscribe(callback: () => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }
}

// ---------------------------------------------------------------------------
// Singleton instance
// ---------------------------------------------------------------------------

export const annotationManager = new AnnotationManager();

export default annotationManager;
