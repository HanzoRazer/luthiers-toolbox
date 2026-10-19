export interface HsModel {
  col: string; gr: string; path: string
  cx: number; nutY: number; nw: number
  tuners: [number, number][]
}
export type HsModelName = 'Les Paul' | 'Strat' | 'PRS' | 'Telecaster' | 'SG' | 'Custom'
export type InlayType = 'dot' | 'diamond' | 'block' | 'crown' | 'oval' | 'star' | 'hex' | 'text'
export interface InlayLayer {
  id: string; name: string; type: InlayType; pip: string
  visible: boolean; x: number; y: number; scaleX: number; rotation: number; fill: string
}
export type HandoffSource = 'svg-import' | 'dxf-import' | 'parametric'
export type HandoffUseAs = 'template' | 'inlay'
export interface CustomShape { path: string; label: string; source: HandoffSource; useAs: HandoffUseAs }
export interface RawPath { id: string; d: string; label: string; color: string; visible: boolean; layer?: string }
export interface BBox { minX: number; minY: number; maxX: number; maxY: number; w: number; h: number }
export type FitMode = 'contain' | 'width' | 'height' | 'stretch'
export type FlipYMode = 'auto' | 'yes' | 'no'
export interface NormalizeOptions {
  fitMode: FitMode; alignH: 'center' | 'left' | 'right'
  alignV: 'center' | 'top' | 'bottom'; padding: number; flipY: FlipYMode
}
export type PipelineStep = 'idle' | 'load' | 'parse' | 'normalize' | 'done' | 'error'
export type TipStyle = 0 | 1 | 2 | 3
export type TunerPattern = '6L' | '6R' | '3+3' | '4+2' | '3+2+1'
export interface HeadstockParams {
  nutWidth: number; length: number; tipWidth: number; asymmetry: number; taper: number
  waistDepth: number; waistPos: number; bassShoulder: number; trebleShoulder: number
  tipRounding: number; pegSpacing: number; pegInset: number
}
export interface ParamDef {
  id: keyof HeadstockParams; label: string; min: number; max: number
  step: number; def: number; unit: string; pct?: boolean; tip?: string
}
export type GateStatus = 'pass' | 'warn' | 'fail'
export interface Gate { name: string; detail: string; pass: GateStatus }
export interface NoveltyResult { score: number; minDist: number; closestTo: string; corpusDists: Record<string, number> }
export interface ScoreResult { novelty: NoveltyResult; gates: Gate[] }
export type ActiveTab = 'workspace' | 'import' | 'parametric'
