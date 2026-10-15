import type { HsModel, HsModelName } from '@/types/headstock'

export const HS_MODELS: Record<HsModelName, HsModel> = {
  'Les Paul':   { col:'#7a3d1a', gr:'#4a2010', path:'M65,298 C60,278 52,248 46,216 L42,182 L44,148 L52,114 L66,84 L82,58 L94,38 L100,22 L106,38 L118,58 L134,84 L148,114 L156,148 L158,182 L154,216 C148,248 140,278 135,298 Z', cx:100, nutY:290, nw:70, tuners:[[52,108],[52,158],[52,206],[148,108],[148,158],[148,206]] },
  'Strat':      { col:'#6b4220', gr:'#3a2208', path:'M65,298 C62,285 58,270 54,250 L50,220 L48,188 L48,154 L50,118 L56,86 L66,60 L80,38 C88,26 96,20 100,20 C104,20 112,26 120,38 L134,60 L140,86 L146,118 L148,154 L148,188 L146,220 L142,250 C138,270 134,285 131,298 Z', cx:100, nutY:290, nw:66, tuners:[[52,92],[52,132],[52,172],[52,212],[52,248],[52,270]] },
  'PRS':        { col:'#704824', gr:'#402810', path:'M65,298 C61,276 55,244 50,210 L48,174 L52,136 L64,100 L80,66 L94,38 L100,8 L106,38 L120,66 L136,100 L148,136 L152,174 L150,210 C145,244 139,276 135,298 Z', cx:100, nutY:292, nw:70, tuners:[[55,104],[55,158],[55,206],[145,104],[145,158],[145,206]] },
  'Telecaster': { col:'#6e4218', gr:'#3e2208', path:'M65,298 C62,284 58,268 55,248 L52,214 L52,178 L52,142 L52,106 L56,76 L68,52 C78,36 90,28 100,28 C110,28 122,36 132,52 L144,76 L148,106 L148,142 L148,178 L148,214 L145,248 C142,268 138,284 135,298 Z', cx:100, nutY:290, nw:66, tuners:[[54,96],[54,136],[54,176],[54,216],[54,248],[54,270]] },
  'SG':         { col:'#5c2e10', gr:'#3a1808', path:'M58,298 C54,276 50,252 50,228 L52,196 L60,162 L72,130 L86,100 L98,68 L100,18 L102,68 L114,100 L128,130 L140,162 L148,196 L150,228 C150,252 146,276 142,298 Z', cx:100, nutY:290, nw:60, tuners:[[56,108],[56,158],[56,208],[144,108],[144,158],[144,208]] },
  'Custom':     { col:'#7a5030', gr:'#5a3018', path:'', cx:100, nutY:290, nw:70, tuners:[] },
}

export const PARAM_DEFS = {
  BODY: [
    { id:'nutWidth'    as const, label:'Nut width',   min:54,  max:80,   step:.5,  def:70,   unit:'u' },
    { id:'length'      as const, label:'Length',      min:200, max:310,  step:1,   def:276,  unit:'u' },
    { id:'tipWidth'    as const, label:'Tip width',   min:16,  max:90,   step:.5,  def:58,   unit:'u' },
    { id:'asymmetry'   as const, label:'Asymmetry',   min:-20, max:20,   step:.5,  def:0,    unit:'u' },
    { id:'taper'       as const, label:'Taper',       min:-20, max:30,   step:.5,  def:0,    unit:'u' },
  ],
  SHOULDER: [
    { id:'waistDepth'  as const, label:'Waist depth', min:0,   max:25,   step:.5,  def:2,    unit:'u' },
    { id:'waistPos'    as const, label:'Waist pos',   min:.2,  max:.65,  step:.01, def:.38,  unit:'%', pct:true },
    { id:'bassShoulder'    as const, label:'Bass R',   min:8,   max:60,   step:.5,  def:28,   unit:'u' },
    { id:'trebleShoulder'  as const, label:'Treble R', min:8,   max:60,   step:.5,  def:28,   unit:'u' },
    { id:'tipRounding' as const, label:'Tip round',   min:0,   max:50,   step:1,   def:18,   unit:'u' },
  ],
  TUNER: [
    { id:'pegSpacing'  as const, label:'Peg spacing', min:30,  max:55,   step:.5,  def:44,   unit:'u' },
    { id:'pegInset'    as const, label:'Peg inset',   min:8,   max:20,   step:.5,  def:12,   unit:'u' },
  ],
}

export const TIP_STYLE_LABELS = ['Rounded', 'Squared', 'Pointed', 'Scroll']
export const TUNER_PATTERNS   = ['6L', '6R', '3+3', '4+2', '3+2+1'] as const
