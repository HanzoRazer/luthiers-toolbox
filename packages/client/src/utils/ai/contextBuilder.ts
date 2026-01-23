import type { AIContextPacketV1, EvidenceSelection, EvidenceRef } from "./types";
import { pickDefaultRefs, pointIdFromRelpath } from "./relpathUtils";
import { extractPeaks, extractSpectrumRow, extractWsiRow } from "./excerptExtractors";

function nowUtcIso(): string {
  const d = new Date();
  d.setMilliseconds(0);
  return d.toISOString().replace(/\.\d{3}Z$/, "Z");
}

export type BuildContextArgs = {
  packSchemaId?: string | null;
  bundleSha256?: string | null;

  activeRelpath: string | null;
  selection: EvidenceSelection | null;

  files: Array<{ relpath: string; kind?: string; sha256?: string; bytes?: number }>;

  activeBytes?: Uint8Array | null;
  siblingPeaksBytes?: Uint8Array | null;
  wsiCurveBytes?: Uint8Array | null;

  notes?: string;
};

export function buildAIContextPacket(args: BuildContextArgs): AIContextPacketV1 {
  const sel = args.selection ?? {};
  const activeRelpath = args.activeRelpath ?? sel.activeRelpath ?? null;

  const pointId = (sel.pointId ?? pointIdFromRelpath(activeRelpath ?? "")) ?? null;
  const freqHz = typeof sel.freqHz === "number" ? sel.freqHz : null;

  const refs = pickDefaultRefs(args.files, activeRelpath).map((f) => ({
    relpath: f.relpath,
    kind: f.kind,
    sha256: f.sha256,
    bytes: f.bytes,
  } satisfies EvidenceRef));

  const packet: AIContextPacketV1 = {
    schema_id: "ai_context_packet_v1",
    created_at_utc: nowUtcIso(),
    request: {
      kind: "explanation",
      template_id: "explain_selection",
      template_version: "1.0.0",
      notes: args.notes,
    },
    evidence: {
      schema_id: args.packSchemaId ?? undefined,
      bundle_sha256: args.bundleSha256 ?? undefined,
      selection: {
        pointId,
        freqHz,
        activeRelpath,
        source: (sel.source ?? null) as any,
      },
      refs,
    },
  };

  if (freqHz != null) {
    const excerpts: any = {};
    if (args.wsiCurveBytes) excerpts.wsiRow = extractWsiRow(args.wsiCurveBytes, freqHz);
    if (args.activeBytes) excerpts.spectrumRow = extractSpectrumRow(args.activeBytes, freqHz);
    if (args.siblingPeaksBytes) excerpts.peaks = extractPeaks(args.siblingPeaksBytes);
    if (Object.values(excerpts).some((v) => v != null)) packet.excerpts = excerpts;
  }

  return packet;
}
