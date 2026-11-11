// SuspenseShells.spec.ts
//
// InlayWorkspaceShell and SoundholeRosetteShell are the only two places in the
// client that combine <Suspense> with defineAsyncComponent. Each stage lives in
// its own Suspense boundary inside a v-show panel, so every boundary mounts when
// the shell mounts. Until now nothing exercised that path: a Vue upgrade that
// broke async-component resolution under Suspense would pass CI and only show up
// as a stage stuck on "Loading…" in the browser.
//
// These tests mount each shell with the REAL stage views (no stubs) and the
// backend offline (fetch rejects), then prove, per stage:
//   1. the boundary is genuinely async: the fallback is on screen at mount;
//   2. the boundary resolves: the fallback is gone and the stage's own view
//      rendered in its place;
//   3. tab switching shows exactly one panel;
//   4. no Vue warning or error was raised along the way.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import InlayWorkspaceShell from "../InlayWorkspaceShell.vue"
import SoundholeRosetteShell from "../SoundholeRosetteShell.vue"

interface StageCase {
  /** data-stage value of the panel and id suffix of its tab. */
  id: string
  /** Text of the panel's Suspense fallback. */
  fallback: string
  /** Selector that only the resolved stage view renders. */
  marker: string
}

interface ShellCase {
  name: string
  component: typeof InlayWorkspaceShell
  /** Stages wrapped in <Suspense> + defineAsyncComponent. */
  asyncStages: StageCase[]
  /** Every tab, in order, including the inline (non-async) stages. */
  allStages: string[]
}

const SHELLS: ShellCase[] = [
  {
    name: "InlayWorkspaceShell",
    component: InlayWorkspaceShell,
    asyncStages: [
      { id: "pattern", fallback: "Loading pattern library…", marker: ".inlay-pattern-view" },
      { id: "fretboard", fallback: "Loading fretboard designer…", marker: "h1" },
      { id: "headstock", fallback: "Loading headstock designer…", marker: ".headstock-designer-view" },
    ],
    allStages: ["headstock-design", "pattern", "fretboard", "headstock", "bom"],
  },
  {
    name: "SoundholeRosetteShell",
    component: SoundholeRosetteShell as typeof InlayWorkspaceShell,
    asyncStages: [
      { id: "rosette", fallback: "Loading rosette designer…", marker: ".rd-root" },
      { id: "soundhole", fallback: "Loading soundhole designer…", marker: ".soundhole-designer-view" },
      { id: "purfling", fallback: "Loading purfling designer…", marker: ".purfling-designer-view" },
      { id: "binding", fallback: "Loading binding designer…", marker: ".binding-designer-view" },
    ],
    allStages: ["rosette", "soundhole", "purfling", "binding"],
  },
]

/** Expected heading of the fretboard stage, whose root has no distinctive class. */
const FRETBOARD_HEADING = "Fretboard Inlay Designer"

/** Stage resolution takes ~1-2 s locally; leave CI headroom above waitFor. */
const RESOLVE_TIMEOUT_MS = 10_000
const TEST_TIMEOUT_MS = 20_000

let vueMessages: string[]

function panel(wrapper: VueWrapper, id: string) {
  return wrapper.get(`[data-stage="${id}"]`)
}

async function waitForAllStagesResolved(wrapper: VueWrapper, stages: StageCase[]) {
  await vi.waitFor(
    async () => {
      await flushPromises()
      for (const s of stages) {
        expect(panel(wrapper, s.id).find(".stage-loading").exists()).toBe(false)
      }
    },
    { timeout: RESOLVE_TIMEOUT_MS, interval: 25 },
  )
}

beforeEach(() => {
  setActivePinia(createPinia())
  // Backend offline: every request fails, as when the API is unreachable.
  // The stages must still render their UI.
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new TypeError("network disabled in SuspenseShells.spec")
    }),
  )
  vueMessages = []
  const capture = (...args: unknown[]) => {
    const text = args.map(String).join(" ")
    if (text.includes("[Vue warn]") || text.includes("[Vue error]")) vueMessages.push(text)
  }
  vi.spyOn(console, "warn").mockImplementation(capture)
  vi.spyOn(console, "error").mockImplementation(capture)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe.each(SHELLS)("$name Suspense stages", (shell) => {
  function mountShell() {
    const errors: unknown[] = []
    const wrapper = mount(shell.component, {
      attachTo: document.body,
      global: {
        config: {
          errorHandler: (err) => {
            errors.push(err)
          },
        },
      },
    })
    return { wrapper, errors }
  }

  it("shows every stage's fallback at mount, then resolves each to its real view", async () => {
    const { wrapper, errors } = mountShell()

    // 1. Genuinely async: each boundary is pending and showing its fallback.
    for (const s of shell.asyncStages) {
      expect(panel(wrapper, s.id).get(".stage-loading").text()).toBe(s.fallback)
    }

    // 2. Every boundary resolves and the stage's own view replaces the fallback.
    await waitForAllStagesResolved(wrapper, shell.asyncStages)
    for (const s of shell.asyncStages) {
      const p = panel(wrapper, s.id)
      expect(p.find(s.marker).exists(), `${s.id}: ${s.marker} rendered`).toBe(true)
      expect(p.findAll("*").length, `${s.id}: rendered content`).toBeGreaterThan(5)
    }
    const fretboard = shell.asyncStages.find((s) => s.id === "fretboard")
    if (fretboard) {
      expect(panel(wrapper, "fretboard").get("h1").text()).toContain(FRETBOARD_HEADING)
    }

    expect(errors).toEqual([])
    expect(vueMessages).toEqual([])
    wrapper.unmount()
  }, TEST_TIMEOUT_MS)

  it("switches tabs so exactly one stage panel is visible", async () => {
    const { wrapper, errors } = mountShell()
    await waitForAllStagesResolved(wrapper, shell.asyncStages)

    for (const active of shell.allStages) {
      await wrapper.get(`#tab-${active}`).trigger("click")
      for (const id of shell.allStages) {
        const visible = (panel(wrapper, id).element as HTMLElement).style.display !== "none"
        expect(visible, `with ${active} active, ${id} visible`).toBe(id === active)
        expect(wrapper.get(`#tab-${id}`).attributes("aria-selected")).toBe(String(id === active))
      }
    }

    expect(errors).toEqual([])
    expect(vueMessages).toEqual([])
    wrapper.unmount()
  }, TEST_TIMEOUT_MS)
})
