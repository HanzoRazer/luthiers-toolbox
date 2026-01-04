import type { EvidenceManifestV1, ViewerPackManifestV1 } from "./types";

// ─────────────────────────────────────────────────────────────────────────────
// toolbox_evidence_manifest_v1 validator
// ─────────────────────────────────────────────────────────────────────────────

export function validateEvidenceManifestV1(x: unknown): EvidenceManifestV1 {
  if (!x || typeof x !== "object") throw new Error("manifest is not an object");
  const obj = x as Record<string, unknown>;
  if (obj.schema_version !== "toolbox_evidence_manifest_v1") {
    throw new Error(`unsupported schema_version: ${String(obj.schema_version)}`);
  }
  if (typeof obj.bundle_id !== "string" || !obj.bundle_id) throw new Error("bundle_id missing");
  if (typeof obj.created_at_utc !== "string" || !obj.created_at_utc) throw new Error("created_at_utc missing");
  if (!Array.isArray(obj.files)) throw new Error("files[] missing");

  for (const f of obj.files) {
    if (!f || typeof f !== "object") throw new Error("files[] contains non-object");
    const file = f as Record<string, unknown>;
    if (typeof file.path !== "string" || !file.path) throw new Error("files[].path missing");
    if (typeof file.kind !== "string" || !file.kind) throw new Error("files[].kind missing");
  }

  return x as EvidenceManifestV1;
}

// Legacy alias
export const validateManifestV1 = validateEvidenceManifestV1;

// ─────────────────────────────────────────────────────────────────────────────
// viewer_pack_v1 validator (canonical for tap_tone_pi interchange)
// ─────────────────────────────────────────────────────────────────────────────

export function validateViewerPackV1(x: unknown): ViewerPackManifestV1 {
  if (!x || typeof x !== "object") throw new Error("manifest is not an object");
  const obj = x as Record<string, unknown>;
  if (obj.schema_id !== "viewer_pack_v1") {
    throw new Error(`unsupported schema_id: ${String(obj.schema_id)}. Expected viewer_pack_v1.`);
  }
  if (!Array.isArray(obj.files)) throw new Error("manifest.json missing files[] array");

  for (const f of obj.files) {
    if (!f || typeof f !== "object") throw new Error("files[] contains non-object");
    const file = f as Record<string, unknown>;
    if (typeof file.relpath !== "string" || !file.relpath) throw new Error("files[].relpath missing");
    if (typeof file.kind !== "string" || !file.kind) throw new Error("files[].kind missing");
  }

  // Normalize files array
  const files = (obj.files as Record<string, unknown>[]).map((f) => ({
    relpath: String(f.relpath ?? ""),
    sha256: f.sha256 ? String(f.sha256) : undefined,
    bytes: Number(f.bytes ?? 0),
    mime: String(f.mime ?? "application/octet-stream"),
    kind: String(f.kind ?? "unknown"),
  }));

  return {
    viewer_pack_version: String(obj.viewer_pack_version ?? "v1"),
    schema_id: "viewer_pack_v1",
    created_at_utc: String(obj.created_at_utc ?? ""),
    source_capdir: obj.source_capdir ? String(obj.source_capdir) : undefined,
    detected_phase: obj.detected_phase ? String(obj.detected_phase) : undefined,
    measurement_only: !!obj.measurement_only,
    interpretation: obj.interpretation ? String(obj.interpretation) : undefined,
    contents: (obj.contents as Record<string, boolean>) ?? {},
    files,
    bundle_sha256: obj.bundle_sha256 ? String(obj.bundle_sha256) : undefined,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Schema detection
// ─────────────────────────────────────────────────────────────────────────────

export type DetectedSchema = "viewer_pack_v1" | "toolbox_evidence_manifest_v1" | "unknown";

export function detectSchema(x: unknown): DetectedSchema {
  if (!x || typeof x !== "object") return "unknown";
  const obj = x as Record<string, unknown>;
  if (obj.schema_id === "viewer_pack_v1") return "viewer_pack_v1";
  if (obj.schema_version === "toolbox_evidence_manifest_v1") return "toolbox_evidence_manifest_v1";
  return "unknown";
}

