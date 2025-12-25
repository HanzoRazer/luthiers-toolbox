/**
 * Design Snapshot Types - Bundle 31.0.5
 */

import type { RosetteParamSpec } from "./rosette";

export type DesignContextRefs = {
  material_preset_id?: string | null;
  tool_preset_id?: string | null;
  machine_id?: string | null;
  mode?: string | null;
};

export type DesignSnapshot = {
  snapshot_id: string;
  name: string;
  notes?: string | null;
  pattern_id?: string | null;
  tags: string[];
  context_refs: DesignContextRefs;
  rosette_params: RosetteParamSpec;
  feasibility?: Record<string, any> | null;
  baseline?: boolean;  // 32.1.0 - is this the baseline snapshot?
  created_at: string;
  updated_at: string;
};

export type SnapshotCreateRequest = {
  name: string;
  notes?: string | null;
  pattern_id?: string | null;
  tags?: string[];
  context_refs?: DesignContextRefs;
  rosette_params: RosetteParamSpec;
  feasibility?: Record<string, any> | null;
};

export type SnapshotUpdateRequest = Partial<{
  name: string;
  notes: string | null;
  pattern_id: string | null;
  tags: string[];
  context_refs: DesignContextRefs;
  rosette_params: RosetteParamSpec;
  feasibility: Record<string, any> | null;
}>;

export type SnapshotSummary = {
  snapshot_id: string;
  name: string;
  pattern_id?: string | null;
  tags: string[];
  baseline?: boolean;  // 32.1.0
  updated_at: string;
};

export type SnapshotListResponse = {
  items: SnapshotSummary[];
};

export type SnapshotExportResponse = {
  snapshot: Record<string, any>;
};

export type SnapshotImportRequest = {
  snapshot: Record<string, any>;
};
