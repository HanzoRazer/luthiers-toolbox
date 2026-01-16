import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import JSZip from "jszip";

import { loadNormalizedPack } from "../zip_loader";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function repoRootFromThisFile(): string {
  // This file is in: packages/client/src/evidence/__tests__/zip_loader.spec.ts
  const here = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(here, "../../../../..");
}

function readFixtureZip(relFromRepoRoot: string): Uint8Array {
  const repoRoot = repoRootFromThisFile();
  const abs = path.join(repoRoot, relFromRepoRoot);
  const buf = fs.readFileSync(abs);
  return new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
}

function fileFromBytes(bytes: Uint8Array, name = "fixture.zip"): File {
  // Node's File/Blob polyfill lacks arrayBuffer(), so create minimal File-like object
  // The loader only uses arrayBuffer(), so we just need to provide that method
  const fileLike = {
    name,
    size: bytes.byteLength,
    type: "application/zip",
    arrayBuffer: async (): Promise<ArrayBuffer> => {
      // Return a copy of the buffer to avoid shared memory issues
      const copy = new ArrayBuffer(bytes.byteLength);
      new Uint8Array(copy).set(bytes);
      return copy;
    },
  } as unknown as File;

  return fileLike;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe("evidence/zip_loader", () => {
  describe("loadNormalizedPack", () => {
    it("loads the minimal viewer pack fixture", async () => {
      const bytes = readFixtureZip("services/api/tests/fixtures/viewer_packs/session_minimal.zip");
      const file = fileFromBytes(bytes, "session_minimal.zip");

      const pack = await loadNormalizedPack(file);

      expect(pack.schema_id).toBe("viewer_pack_v1");
      expect(pack.source_capdir).toBe("minimal_fixture_session");
      expect(pack.detected_phase).toBe("phase2");
      expect(pack.measurement_only).toBe(true);
      expect(pack.files.length).toBeGreaterThan(0);

      // Check audio file entry
      const audioEntry = pack.files.find((f) => f.relpath === "audio/points/A1.wav");
      expect(audioEntry).toBeTruthy();
      expect(audioEntry?.kind).toBe("audio_raw");
      expect(audioEntry?.mime).toBe("audio/wav");

      // Check spectrum CSV entry
      const csvEntry = pack.files.find((f) => f.relpath === "spectra/points/A1/spectrum.csv");
      expect(csvEntry).toBeTruthy();
      expect(csvEntry?.kind).toBe("spectrum_csv");
      expect(csvEntry?.mime).toBe("text/csv");

      // Check session meta entry
      const metaEntry = pack.files.find((f) => f.relpath === "meta/session_meta.json");
      expect(metaEntry).toBeTruthy();
      expect(metaEntry?.kind).toBe("session_meta");
      expect(metaEntry?.mime).toBe("application/json");

      // Verify resolveFile works
      const audioBytes = pack.resolveFile("audio/points/A1.wav");
      expect(audioBytes).toBeTruthy();
      expect(audioBytes?.byteLength).toBe(44);
    });

    it("loads the coherence fixture with dual-axis data", async () => {
      const bytes = readFixtureZip("services/api/tests/fixtures/viewer_packs/session_with_coherence.zip");
      const file = fileFromBytes(bytes, "session_with_coherence.zip");

      const pack = await loadNormalizedPack(file);

      expect(pack.schema_id).toBe("viewer_pack_v1");

      // Verify spectrum CSV with coherence column exists
      const csvEntry = pack.files.find((f) => f.kind === "spectrum_csv");
      expect(csvEntry).toBeTruthy();

      // Verify we can read the CSV content
      const csvBytes = pack.resolveFile(csvEntry!.relpath);
      expect(csvBytes).toBeTruthy();

      const csvText = new TextDecoder().decode(csvBytes!);
      expect(csvText).toContain("coherence");
    });

    it("rejects zips without manifest.json", async () => {
      const zip = new JSZip();
      zip.file("audio/points/A1.wav", new Uint8Array([0, 1, 2]));

      const bytes = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(bytes, "no_manifest.zip");

      await expect(loadNormalizedPack(file)).rejects.toThrow(/manifest\.json/i);
    });

    it("rejects zips with unsupported schema", async () => {
      const zip = new JSZip();
      zip.file(
        "manifest.json",
        JSON.stringify({
          schema_id: "unknown_schema_v99",
          files: [],
        })
      );

      const bytes = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(bytes, "bad_schema.zip");

      await expect(loadNormalizedPack(file)).rejects.toThrow(/unsupported|unrecognized/i);
    });

    it("accepts forward-compatible unknown kinds (kind-agnostic loading)", async () => {
      const zip = new JSZip();
      zip.file(
        "manifest.json",
        JSON.stringify({
          schema_version: "v1",
          schema_id: "viewer_pack_v1",
          created_at_utc: "2026-01-15T00:00:00Z",
          source_capdir: "unknown_kind_test",
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
              relpath: "spectra/points/A1/spectrum.csv",
              sha256: "0".repeat(64),
              bytes: 20,
              mime: "text/csv",
              kind: "spectrogram_v2", // Unknown future kind
            },
          ],
          bundle_sha256: "0".repeat(64),
        })
      );
      zip.file("spectra/points/A1/spectrum.csv", "hz,mag\n100,0.1\n");

      const bytes = await zip.generateAsync({ type: "uint8array" });
      const file = fileFromBytes(bytes, "future_kind.zip");

      // Should NOT throw - loader is kind-agnostic
      const pack = await loadNormalizedPack(file);

      expect(pack.schema_id).toBe("viewer_pack_v1");
      expect(pack.files[0].kind).toBe("spectrogram_v2");
    });

    it("handles the unknown_kind fixture (fallback renderer scenario)", async () => {
      const bytes = readFixtureZip("services/api/tests/fixtures/viewer_packs/session_unknown_kind.zip");
      const file = fileFromBytes(bytes, "session_unknown_kind.zip");

      const pack = await loadNormalizedPack(file);

      expect(pack.schema_id).toBe("viewer_pack_v1");

      // Should have some files with unknown kinds
      const unknownKindFiles = pack.files.filter(
        (f) => !["audio_raw", "spectrum_csv", "session_meta", "provenance"].includes(f.kind)
      );
      expect(unknownKindFiles.length).toBeGreaterThan(0);
    });
  });
});
