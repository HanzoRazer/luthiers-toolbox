import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ActiveTab, HsModelName, InlayLayer, CustomShape,
  RawPath, BBox, NormalizeOptions, PipelineStep,
  HeadstockParams, TipStyle, TunerPattern,
} from '@/types/headstock'

// ─── Corpus parameter vectors ─────────────────────────────────────────────────
export const CORPUS: Record<string, HeadstockParams> = {
  'Les Paul':   { nutWidth:70, length:276, tipWidth:58, asymmetry:0,  taper:0,  waistDepth:2, waistPos:.38, bassShoulder:28, trebleShoulder:28, tipRounding:18, pegSpacing:44, pegInset:12 },
  'Strat':      { nutWidth:66, length:278, tipWidth:52, asymmetry:-6, taper:3,  waistDepth:0, waistPos:.40, bassShoulder:15, trebleShoulder:22, tipRounding:8,  pegSpacing:42, pegInset:12 },
  'PRS':        { nutWidth:70, length:290, tipWidth:46, asymmetry:0,  taper:-4, waistDepth:4, waistPos:.42, bassShoulder:22, trebleShoulder:22, tipRounding:30, pegSpacing:46, pegInset:13 },
  'Telecaster': { nutWidth:66, length:278, tipWidth:66, asymmetry:0,  taper:6,  waistDepth:0, waistPos:.40, bassShoulder:10, trebleShoulder:10, tipRounding:4,  pegSpacing:42, pegInset:11 },
  'SG':         { nutWidth:60, length:280, tipWidth:38, asymmetry:0,  taper:-8, waistDepth:6, waistPos:.44, bassShoulder:18, trebleShoulder:18, tipRounding:22, pegSpacing:40, pegInset:12 },
}

const DEFAULT_PARAMS: HeadstockParams = { ...CORPUS['Les Paul'] }

export const useHeadstockStore = defineStore('headstock', () => {

  // ── Navigation ─────────────────────────────────────────────────────────────
  const activeTab = ref<ActiveTab>('workspace')
  function setTab(tab: ActiveTab) { activeTab.value = tab }

  // ── Workspace ──────────────────────────────────────────────────────────────
  const currentModel  = ref<HsModelName>('Les Paul')
  const inlays        = ref<InlayLayer[]>([])
  const customShape   = ref<CustomShape | null>(null)

  // Canvas display options
  const showGrid      = ref(true)
  const showCL        = ref(true)
  const showNut       = ref(true)
  const snapOn        = ref(true)
  const boundaryOn    = ref(true)

  function setModel(name: HsModelName) { currentModel.value = name }

  function loadCustomShape(shape: CustomShape) {
    customShape.value = shape
    currentModel.value = 'Custom'
  }

  function addInlay(layer: InlayLayer) {
    inlays.value.push(layer)
  }

  function removeInlay(id: string) {
    inlays.value = inlays.value.filter(l => l.id !== id)
  }

  function updateInlay(id: string, patch: Partial<InlayLayer>) {
    const idx = inlays.value.findIndex(l => l.id === id)
    if (idx !== -1) Object.assign(inlays.value[idx], patch)
  }

  function toggleInlayVisibility(id: string) {
    const layer = inlays.value.find(l => l.id === id)
    if (layer) layer.visible = !layer.visible
  }

  function clearInlays() { inlays.value = [] }

  const inlayCount = computed(() => inlays.value.length)

  // ── Import ─────────────────────────────────────────────────────────────────
  const rawPaths     = ref<RawPath[]>([])
  const normPaths    = ref<RawPath[]>([])
  const rawBBox      = ref<BBox | null>(null)
  const iFileType    = ref<'svg' | 'dxf' | null>(null)
  const iFileName    = ref('')
  const iFileSize    = ref(0)
  const pipelineStep = ref<PipelineStep>('idle')
  const iUseAs       = ref<'template' | 'inlay'>('template')

  const normOptions = ref<NormalizeOptions>({
    fitMode:  'contain',
    alignH:   'center',
    alignV:   'center',
    padding:  8,
    flipY:    'auto',
  })

  function setRawPaths(paths: RawPath[], bbox: BBox | null, fileType: 'svg' | 'dxf', fileName: string, fileSize: number) {
    rawPaths.value  = paths
    rawBBox.value   = bbox
    iFileType.value = fileType
    iFileName.value = fileName
    iFileSize.value = fileSize
  }

  function setNormPaths(paths: RawPath[]) { normPaths.value = paths }
  function toggleRawPathVisibility(id: string) {
    const p = rawPaths.value.find(x => x.id === id)
    if (p) p.visible = !p.visible
  }

  // ── Parametric ─────────────────────────────────────────────────────────────
  const params     = ref<HeadstockParams>({ ...DEFAULT_PARAMS })
  const tipStyle   = ref<TipStyle>(0)
  const tunerPat   = ref<TunerPattern>('3+3')
  const toolDia    = ref(2.0)
  const showOverlay = ref(false)

  function setParam<K extends keyof HeadstockParams>(key: K, value: number) {
    params.value[key] = value
  }

  function loadPreset(name: string) {
    const preset = CORPUS[name]
    if (preset) Object.assign(params.value, preset)
  }

  function randomizeParams(defs: Array<{ id: keyof HeadstockParams; min: number; max: number; step: number }>) {
    defs.forEach(d => {
      const raw = d.min + Math.random() * (d.max - d.min)
      params.value[d.id] = Math.round(raw / d.step) * d.step as never
    })
  }

  // ── Handoff helpers ────────────────────────────────────────────────────────
  function sendImportToWorkspace() {
    if (!normPaths.value.length) return
    const combined = normPaths.value.filter(p => p.visible && p.d).map(p => p.d).join(' ')
    const shape: CustomShape = {
      path:   combined,
      label:  `${iFileType.value?.toUpperCase()} import — ${iFileName.value}`,
      source: iFileType.value === 'dxf' ? 'dxf-import' : 'svg-import',
      useAs:  iUseAs.value,
    }
    loadCustomShape(shape)
    setTab('workspace')
    return shape
  }

  function sendParametricToWorkspace(path: string) {
    const shape: CustomShape = {
      path,
      label:  `Parametric`,
      source: 'parametric',
      useAs:  'template',
    }
    loadCustomShape(shape)
    setTab('workspace')
    return shape
  }

  return {
    // nav
    activeTab, setTab,
    // workspace
    currentModel, inlays, customShape,
    showGrid, showCL, showNut, snapOn, boundaryOn,
    setModel, loadCustomShape,
    addInlay, removeInlay, updateInlay, toggleInlayVisibility, clearInlays,
    inlayCount,
    // import
    rawPaths, normPaths, rawBBox, iFileType, iFileName, iFileSize,
    pipelineStep, iUseAs, normOptions,
    setRawPaths, setNormPaths, toggleRawPathVisibility,
    sendImportToWorkspace,
    // parametric
    params, tipStyle, tunerPat, toolDia, showOverlay,
    setParam, loadPreset, randomizeParams,
    sendParametricToWorkspace,
  }
})
