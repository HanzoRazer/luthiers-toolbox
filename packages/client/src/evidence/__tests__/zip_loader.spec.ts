/**
 * Viewer Pack Loader Tests (viewer_pack_v1)
 *
 * These tests validate the pack loader as a *contract surface*.
 * They use canonical fixtures from: services/api/tests/fixtures/viewer_packs/
 *
 * Contract guarantees tested:
 * - Schema detection and validation
 * - File listing normalization
 * - Bytes extraction via resolveFile()
 * - Forward-compatible unknown kinds (soft fallback)
 * - Coherence as both overlay column AND separate JSON kind
 */

import { describe, it, expect } from "vitest";
import JSZip from "jszip";
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { loadNormalizedPack } from "../zip_loader";
import type { NormalizedPack, NormalizedFileEntry } from "../types";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function fixtureAbs(rel: string): string {
  const here = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(
    here,
    "../../../../../services/api/tests/fixtures/viewer_packs",
    rel
  );
}

function fileFromBytes(bytes: Uint8Array, name = "fixture.zip"): File {
  // Node's File/Blob polyfill lacks arrayBuffer(), so create minimal File-like object
  const fileLike = {
    name,
    size: bytes.byteLength,
    type: "application/zip",
    arrayBuffer: async (): Promise<ArrayBuffer> => {
      const copy = new ArrayBuffer(bytes.byteLength);
      new Uint8Array(copy).set(bytes);
      return copy;
    },
  } as unknown as File;
  return fileLike;
}

async function loadFixtureZip(name: string): Promise<NormalizedPack> {
  const buf = readFileSync(fixtureAbs(name));
  const bytes = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
  const file = fileFromBytes(bytes, name);
  return await loadNormalizedPack(file);
}

function findByRelpath(
  files: NormalizedFileEntry[],
  rel: string
): NormalizedFileEntry | undefined {
  return files.find((f) => f.relpath === rel);
}

function findByKind(
  files: NormalizedFileEntry[],
  kind: string
): NormalizedFileEntry | undefined {
  return files.find((f) => f.kind === kind);
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe("evidence/zip_loader (viewer_pack_v1)", () => {
  describe("basic loading", () => {
    it("loads minimal fixture and normalizes file list", async () => {
      const pack = await loadFixtureZip("session_minimal.zip");

      expect(pack.schema_id).toBe("viewer_pack_v1");
      expect(pack.files.length).toBeGreaterThan(0);

      // Core presence checks
      expect(findByRelpath(pack.files, "meta/session_meta.json")).toBeTruthy();

      // Audio file
      const wav = pack.files.find((f) => f.relpath.endsWith(".wav"));
      expect(wav).toBeTruthy();
      expect(wav?.kind).toBe("audio_raw");
      expect(wav?.mime).toBe("audio/wav");

      // Spectrum CSV
      const csv = pack.files.find((f) => f.relpath.endsWith("spectrum.csv"));
      expect(csv).toBeTruthy();
      expect(csv?.kind).toBe("spectrum_csv");
      expect(csv?.mime).toBe("text/csv");
    });

    it("resolves file bytes for a known entry", async () => {
      const pack = await loadFixtureZip("session_minimal.zip");
      const csv = pack.files.find((f) => f.relpath.endsWith("spectrum.csv"));
      expect(csv).toBeTruthy();

      const bytes = pack.resolveFile(csv!.relpath);
      expect(bytes).toBeTruthy();
      expect(bytes!.byteLength).toBeGreaterThan(0);

      const text = new TextDecoder().decode(bytes!);
      expect(text.toLowerCase()).toContain("freq");
    });

    it("returns null for non-existent file", async () => {
      const pack = await loadFixtureZip("session_minimal.zip");
      const bytes = pack.resolveFile("does/not/exist.txt");
      expect(bytes).toBeNull();
    });
  });

  describe("error handling", () => {
    it("throws clear error when manifest.json is missing", async () => {
      const zip = new JSZip();
      zip.file("meta/session_meta.json", JSON.stringify({ ok: true }));
      const buf = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(buf, "no_manifest.zip");

      await expect(loadNormalizedPack(file)).rejects.toThrow(/manifest/i);
    });

    it("throws on unsupported schema", async () => {
      const zip = new JSZip();
      zip.file(
        "manifest.json",
        JSON.stringify({
          schema_id: "unknown_schema_v99",
          files: [],
        })
      );
      const buf = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(buf, "bad_schema.zip");

      await expect(loadNormalizedPack(file)).rejects.toThrow(
        /unsupported|unrecognized/i
      );
    });
  });

  describe("coherence contract", () => {
    it("loads coherence fixture with overlay column in spectrum CSV", async () => {
      const pack = await loadFixtureZip("session_with_coherence.zip");

      const csv = findByKind(pack.files, "spectrum_csv");
      expect(csv).toBeTruthy();

      const bytes = pack.resolveFile(csv!.relpath);
      expect(bytes).toBeTruthy();

      const text = new TextDecoder().decode(bytes!);
      // Coherence overlay column truth
      expect(text.toLowerCase()).toContain("coherence");
    });

    it("loads coherence fixture with separate coherence JSON kind", async () => {
      const pack = await loadFixtureZip("session_with_coherence.zip");

      // Separate coherence kind (metadata JSON)
      const cohFile = findByKind(pack.files, "coherence");
      expect(cohFile).toBeTruthy();
      expect(cohFile?.mime).toBe("application/json");

      const bytes = pack.resolveFile(cohFile!.relpath);
      expect(bytes).toBeTruthy();
      expect(bytes!.byteLength).toBeGreaterThan(0);

      // Verify it's valid JSON
      const text = new TextDecoder().decode(bytes!);
      const parsed = JSON.parse(text);
      expect(parsed).toHaveProperty("overall_coherence");
    });
  });

  describe("forward compatibility", () => {
    it("does not reject unknown kinds (soft fallback)", async () => {
      const pack = await loadFixtureZip("session_unknown_kind.zip");

      // Pack should load successfully
      expect(pack.schema_id).toBe("viewer_pack_v1");
      expect(pack.files.length).toBeGreaterThan(0);

      // Confirm unknown kinds are present and preserved
      const unknownKinds = pack.files.filter(
        (f) =>
          !["audio_raw", "spectrum_csv", "session_meta", "provenance"].includes(
            f.kind
          )
      );
      expect(unknownKinds.length).toBeGreaterThan(0);

      // Verify specific unknown kinds from fixture
      const futureKind = findByKind(pack.files, "future_mode_shape");
      expect(futureKind).toBeTruthy();

      const experimentalKind = findByKind(pack.files, "experimental_binary");
      expect(experimentalKind).toBeTruthy();
    });

    it("accepts in-memory pack with future unknown kind", async () => {
      const zip = new JSZip();
      zip.file(
        "manifest.json",
        JSON.stringify({
          schema_version: "v1",
          schema_id: "viewer_pack_v1",
          created_at_utc: "2026-01-15T00:00:00Z",
          source_capdir: "future_test",
          detected_phase: "phase2",
          measurement_only: true,
          interpretation: "deferred",
          points: ["A1"],
          contents: {
            audio: false,
            spectra: true,
            coherence: false,
            ods: false,
            wolf: false,
            plots: false,
          },
          files: [
            {
              relpath: "future/spectrogram_v2.bin",
              sha256: "0".repeat(64),
              bytes: 20,
              mime: "application/octet-stream",
              kind: "spectrogram_v2", // Unknown future kind
            },
          ],
          bundle_sha256: "0".repeat(64),
        })
      );
      zip.file("future/spectrogram_v2.bin", "future data here");

      const buf = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(buf, "future_kind.zip");

      // Should NOT throw - loader is kind-agnostic
      const pack = await loadNormalizedPack(file);

      expect(pack.schema_id).toBe("viewer_pack_v1");
      expect(pack.files[0].kind).toBe("spectrogram_v2");
    });
  });
});
