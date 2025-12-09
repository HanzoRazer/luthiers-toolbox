import { z } from "zod"

/** A loop of points */
export const LoopSchema = z.object({
  pts: z.array(z.tuple([z.number(), z.number()])).min(3),
})

/** Toolpath move (supports multiple backends) */
export const MoveSchema = z.union([
  z.object({
    x: z.number(),
    y: z.number(),
    z: z.number().optional(),
    rapid: z.boolean().optional(),
    kind: z.string().optional(),
  }),
  z.object({
    pt: z.array(z.number()).min(2),
    rapid: z.boolean().optional(),
    kind: z.string().optional(),
  }),
  z.tuple([z.number(), z.number()]),
])

export const BaselineSchema = z.object({
  id: z.string(),
  name: z.string().default("Unnamed Baseline"),
  units: z.enum(["mm", "inch"]).default("mm"),
  machine_id: z.string().optional(),
  post_id: z.string().optional(),
  preset_id: z.string().optional(),
  created_at: z.string().optional(),
  svg: z.string().optional(),
  dxf_key: z.string().optional(),
  moves: z.array(MoveSchema).optional(),
  moves_key: z.string().optional(),
  gcode_key: z.string().optional(),
  loops: z.array(LoopSchema).optional(),
})

export const CandidateSchema = z.object({
  id: z.string(),
  name: z.string().default("Unnamed Candidate"),
  units: z.enum(["mm", "inch"]).default("mm"),
  machine_id: z.string().optional(),
  post_id: z.string().optional(),
  preset_id: z.string().optional(),
  created_at: z.string().optional(),
  svg: z.string().optional(),
  dxf_key: z.string().optional(),
  moves: z.array(MoveSchema).optional(),
  moves_key: z.string().optional(),
  gcode_key: z.string().optional(),
  loops: z.array(LoopSchema).optional(),
})

export const DiffResultSchema = z.object({
  ok: z.boolean().default(true),
  tolerance: z.number().default(0.10),
  added_count: z.number().optional(),
  removed_count: z.number().optional(),
  changed_count: z.number().optional(),
  overlay_svg: z.string().optional(),
})

export type CompareBaseline = z.infer<typeof BaselineSchema>
export type CompareCandidate = z.infer<typeof CandidateSchema>
export type CompareDiffResult = z.infer<typeof DiffResultSchema>

export function parseBaseline(raw: unknown): CompareBaseline {
  const out = BaselineSchema.safeParse(raw)
  if (!out.success) throw new Error(out.error.message)
  return out.data
}

export function parseCandidate(raw: unknown): CompareCandidate {
  const out = CandidateSchema.safeParse(raw)
  if (!out.success) throw new Error(out.error.message)
  return out.data
}

export function parseDiffResult(raw: unknown): CompareDiffResult {
  const out = DiffResultSchema.safeParse(raw)
  if (!out.success) throw new Error(out.error.message)
  return out.data
}
