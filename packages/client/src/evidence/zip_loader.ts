import JSZip from "jszip";
import type {
  EvidenceBundle,
  EvidenceLoadedFile,
  EvidenceManifestV1,
  ViewerPackManifestV1,
  NormalizedPack,
  NormalizedFileEntry,
  EvidenceFileKind,
} from "./types";
import {
  validateEvidenceManifestV1,
  validateViewerPackV1,
  detectSchema,
} from "./validate";

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────

function decodeUtf8(u8: Uint8Array): string {
  return new TextDecoder("utf-8").decode(u8);
}

async function readZipFileBytes(zip: JSZip, path: string): Promise<Uint8Array> {
  const f = zip.file(path);
  if (!f) throw new Error(`missing file in zip: ${path}`);
  const ab = await f.async("arraybuffer");
  return new Uint8Array(ab);
}

async function tryReadZipFileBytes(zip: JSZip, path: string): Promise<Uint8Array | null> {
  const f = zip.file(path);
  if (!f) return null;
  const ab = await f.async("arraybuffer");
  return new Uint8Array(ab);
}

// ─────────────────────────────────────────────────────────────────────────────
// Normalization: toolbox_evidence_manifest_v1 → NormalizedPack
// ─────────────────────────────────────────────────────────────────────────────

function normalizeFromEvidenceManifest(
  manifest: EvidenceManifestV1,
  bytesByPath: Map<string, Uint8Array>
): NormalizedPack {
  const files: NormalizedFileEntry[] = manifest.files.map((f) => ({
    relpath: f.path,
    kind: f.kind as EvidenceFileKind,
    bytes: f.size_bytes ?? bytesByPath.get(f.path)?.byteLength ?? 0,
    mime: guessMime(f.kind, f.path),
    sha256: f.sha256,
  }));

  return {
    schema_id: "toolbox_evidence_manifest_v1",
    created_at_utc: manifest.created_at_utc,
    source_capdir: undefined,
    detected_phase: undefined,
    measurement_only: false,
    interpretation: undefined,
    bundle_sha256: undefined,
    files,
    resolveFile(relpath: string) {
      return bytesByPath.get(relpath) ?? null;
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Normalization: viewer_pack_v1 → NormalizedPack
// ─────────────────────────────────────────────────────────────────────────────

function normalizeFromViewerPack(
  manifest: ViewerPackManifestV1,
  bytesByPath: Map<string, Uint8Array>
): NormalizedPack {
  const files: NormalizedFileEntry[] = manifest.files.map((f) => ({
    relpath: f.relpath,
    kind: f.kind as EvidenceFileKind,
    bytes: f.bytes ?? bytesByPath.get(f.relpath)?.byteLength ?? 0,
    mime: f.mime ?? guessMime(f.kind, f.relpath),
    sha256: f.sha256,
  }));

  return {
    schema_id: "viewer_pack_v1",
    created_at_utc: manifest.created_at_utc ?? "",
    source_capdir: manifest.source_capdir,
    detected_phase: manifest.detected_phase,
    measurement_only: manifest.measurement_only ?? false,
    interpretation: manifest.interpretation,
    bundle_sha256: manifest.bundle_sha256,
    files,
    resolveFile(relpath: string) {
      return bytesByPath.get(relpath) ?? null;
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// MIME inference from kind/extension
// ─────────────────────────────────────────────────────────────────────────────

function guessMime(kind: string, relpath: string): string {
  // Kind-based MIME
  const kindMap: Record<string, string> = {
    audio_wav: "audio/wav",
    audio_flac: "audio/flac",
    audio_raw: "application/octet-stream",
    spectrum_csv: "text/csv",
    peaks_csv: "text/csv",
    coherence_csv: "text/csv",
    waveform_csv: "text/csv",
    wsi_curve: "text/csv",
    notes_md: "text/markdown",
    image_png: "image/png",
    image_jpg: "image/jpeg",
    plot_png: "image/png",
    analysis_peaks: "application/json",
    provenance: "application/json",
    session_meta: "application/json",
    transfer_function: "application/json",
    wolf_candidates: "application/json",
  };
  if (kindMap[kind]) return kindMap[kind];

  // Extension fallback
  const ext = relpath.split(".").pop()?.toLowerCase() ?? "";
  const extMap: Record<string, string> = {
    wav: "audio/wav",
    flac: "audio/flac",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    csv: "text/csv",
    md: "text/markdown",
    json: "application/json",
    txt: "text/plain",
  };
  return extMap[ext] ?? "application/octet-stream";
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Loader: Auto-detects schema, normalizes to NormalizedPack
// ─────────────────────────────────────────────────────────────────────────────

export async function loadNormalizedPack(file: File): Promise<NormalizedPack> {
  const ab = await file.arrayBuffer();
  const zip = await JSZip.loadAsync(ab);

  // Manifest discovery
  const manifestCandidates = ["manifest.json", "evidence/manifest.json", "toolbox/manifest.json"];
  let manifestPath: string | null = null;

  for (const c of manifestCandidates) {
    if (zip.file(c)) {
      manifestPath = c;
      break;
    }
  }
  if (!manifestPath) {
    throw new Error(`manifest.json not found (tried: ${manifestCandidates.join(", ")})`);
  }

  const manifestBytes = await readZipFileBytes(zip, manifestPath);
  const manifestJson = JSON.parse(decodeUtf8(manifestBytes));
  const schema = detectSchema(manifestJson);

  // Gather file bytes by relpath
  const bytesByPath = new Map<string, Uint8Array>();

  if (schema === "viewer_pack_v1") {
    const manifest = validateViewerPackV1(manifestJson);
    for (const f of manifest.files) {
      const bytes = await tryReadZipFileBytes(zip, f.relpath);
      if (bytes) bytesByPath.set(f.relpath, bytes);
    }
    return normalizeFromViewerPack(manifest, bytesByPath);
  }

  if (schema === "toolbox_evidence_manifest_v1") {
    const manifest = validateEvidenceManifestV1(manifestJson);
    for (const f of manifest.files) {
      const bytes = await tryReadZipFileBytes(zip, f.path);
      if (bytes) bytesByPath.set(f.path, bytes);
    }
    return normalizeFromEvidenceManifest(manifest, bytesByPath);
  }

  throw new Error(`Unsupported or unrecognized manifest schema. Expected viewer_pack_v1 or toolbox_evidence_manifest_v1.`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Legacy Loader: Returns EvidenceBundle (for backward compatibility)
// ─────────────────────────────────────────────────────────────────────────────

export async function loadEvidenceZip(file: File): Promise<EvidenceBundle> {
  const ab = await file.arrayBuffer();
  const zip = await JSZip.loadAsync(ab);

  const manifestCandidates = ["manifest.json", "evidence/manifest.json", "toolbox/manifest.json"];
  let manifestPath: string | null = null;

  for (const c of manifestCandidates) {
    if (zip.file(c)) {
      manifestPath = c;
      break;
    }
  }
  if (!manifestPath) {
    throw new Error(`manifest.json not found (tried: ${manifestCandidates.join(", ")})`);
  }

  const manifestBytes = await readZipFileBytes(zip, manifestPath);
  const manifestJson = JSON.parse(decodeUtf8(manifestBytes));
  const manifest = validateEvidenceManifestV1(manifestJson);

  const filesByPath = new Map<string, EvidenceLoadedFile>();

  for (const entry of manifest.files) {
    const bytes = await readZipFileBytes(zip, entry.path);
    const loaded: EvidenceLoadedFile = { entry, bytes };
    filesByPath.set(entry.path, loaded);
  }

  return { manifest, filesByPath };
}
