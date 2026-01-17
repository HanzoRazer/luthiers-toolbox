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

// ─────────────────────────────────────────────────────────────────────────────
// Integrity Checking (viewer_pack_v1)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Compute SHA256 hash of bytes using SubtleCrypto.
 */
async function sha256Hex(data: Uint8Array): Promise<string> {
  const hashBuffer = await crypto.subtle.digest("SHA-256", data.buffer as ArrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Verify a single file's integrity against manifest entry.
 */
export async function verifyFileIntegrity(
  entry: { relpath: string; sha256?: string; bytes: number },
  actualBytes: Uint8Array
): Promise<{ valid: boolean; errors: string[] }> {
  const errors: string[] = [];

  // Check byte size
  if (actualBytes.byteLength !== entry.bytes) {
    errors.push(
      `bytes mismatch for ${entry.relpath}: manifest=${entry.bytes}, actual=${actualBytes.byteLength}`
    );
  }

  // Check SHA256 if present
  if (entry.sha256) {
    const actualHash = await sha256Hex(actualBytes);
    if (actualHash !== entry.sha256) {
      errors.push(
        `sha256 mismatch for ${entry.relpath}: manifest=${entry.sha256}, actual=${actualHash}`
      );
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Verify bundle_sha256 matches the canonical manifest hash.
 *
 * The bundle hash is computed from the manifest JSON bytes WITHOUT bundle_sha256,
 * using sorted keys and indent=2 (matching Python exporter).
 */
export async function verifyBundleHash(
  manifest: Record<string, unknown>
): Promise<{ valid: boolean; expected: string; actual: string }> {
  // Remove bundle_sha256 for hashing
  const manifestWithoutHash = { ...manifest };
  delete manifestWithoutHash.bundle_sha256;

  // Canonical JSON: sorted keys (JS default), indent 2
  const sortedKeys = Object.keys(manifestWithoutHash).sort();
  const sorted: Record<string, unknown> = {};
  for (const k of sortedKeys) {
    sorted[k] = manifestWithoutHash[k];
  }

  const jsonBytes = new TextEncoder().encode(JSON.stringify(sorted, null, 2));
  const computedHash = await sha256Hex(jsonBytes);
  const declaredHash = String(manifest.bundle_sha256 ?? "");

  return {
    valid: computedHash === declaredHash,
    expected: declaredHash,
    actual: computedHash,
  };
}

/**
 * Result of full pack integrity verification.
 */
export interface PackIntegrityResult {
  valid: boolean;
  bundleHashValid: boolean;
  fileErrors: string[];
  bundleHashExpected?: string;
  bundleHashActual?: string;
}

/**
 * Verify full pack integrity: bundle hash + all file hashes.
 *
 * @param manifest - The parsed manifest object
 * @param resolveFile - Function to get file bytes by relpath
 */
export async function verifyPackIntegrity(
  manifest: ViewerPackManifestV1,
  resolveFile: (relpath: string) => Uint8Array | null
): Promise<PackIntegrityResult> {
  const result: PackIntegrityResult = {
    valid: true,
    bundleHashValid: true,
    fileErrors: [],
  };

  // Verify bundle hash
  const bundleCheck = await verifyBundleHash(manifest as unknown as Record<string, unknown>);
  result.bundleHashValid = bundleCheck.valid;
  result.bundleHashExpected = bundleCheck.expected;
  result.bundleHashActual = bundleCheck.actual;
  if (!bundleCheck.valid) {
    result.valid = false;
  }

  // Verify each file
  for (const entry of manifest.files) {
    const bytes = resolveFile(entry.relpath);
    if (!bytes) {
      result.fileErrors.push(`missing file: ${entry.relpath}`);
      result.valid = false;
      continue;
    }

    const fileCheck = await verifyFileIntegrity(entry, bytes);
    if (!fileCheck.valid) {
      result.fileErrors.push(...fileCheck.errors);
      result.valid = false;
    }
  }

  return result;
}

