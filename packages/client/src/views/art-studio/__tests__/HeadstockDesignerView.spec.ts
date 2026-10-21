import { beforeEach, describe, expect, it, vi } from "vitest"
import { mount, flushPromises } from "@vue/test-utils"
import { createRouter, createMemoryHistory } from "vue-router"
import { routes } from "@/router/index"
import HeadstockDesignerView from "../HeadstockDesignerView.vue"

const listHeadstockTemplates = vi.fn(async () => [
  {
    id: "lp",
    name: "Les Paul",
    description: "",
    headstock_style: "3x3",
    inlay_design: "dove",
    headstock_wood: "mahogany",
    inlay_material: "mother_of_pearl",
    tuner_style: "3x3",
  },
])

const generateHeadstockPrompt = vi.fn(async (_request: {
  style: string
  headstock_wood: string
  inlay_design: string
  inlay_material: string
}) => ({ prompt: "PROMPT-TEXT" }))

vi.mock("@/api/art-studio", () => ({
  listHeadstockTemplates: () => listHeadstockTemplates(),
  generateHeadstockPrompt: (request: {
    style: string
    headstock_wood: string
    inlay_design: string
    inlay_material: string
  }) => generateHeadstockPrompt(request),
}))

const PROMPT_PAYLOAD = {
  style: "les_paul",
  headstock_wood: "mahogany",
  inlay_design: "dove",
  inlay_material: "mother_of_pearl",
}

describe("HeadstockDesignerView prompt workflow", () => {
  beforeEach(() => {
    listHeadstockTemplates.mockClear()
    generateHeadstockPrompt.mockClear()
    vi.stubGlobal("alert", vi.fn())
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn(async () => undefined) },
    })
  })

  it("keeps /art-studio/headstock on HeadstockDesignerView", () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const resolved = router.resolve("/art-studio/headstock")
    expect(resolved.name).toBe("ArtStudioHeadstock")
    expect(String(resolved.matched[0]?.components?.default)).toContain("HeadstockDesignerView.vue")
    expect(String(resolved.matched[0]?.components?.default)).not.toContain("art_studio_headstock/ArtStudioHeadstock.vue")
  })

  it("loads templates and sends the original prompt payload", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch")
    const wrapper = mount(HeadstockDesignerView)
    await flushPromises()

    expect(listHeadstockTemplates).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain("Les Paul")
    expect(wrapper.text()).toContain("Length (mm)")

    const callsBeforeOutline = generateHeadstockPrompt.mock.calls.length
    const fetchesBeforeOutline = fetchSpy.mock.calls.length
    await wrapper.get("#outline-nutWidth").setValue("60")
    await wrapper.get("#headstock-tip-style").setValue("pointed")
    expect(generateHeadstockPrompt).toHaveBeenCalledTimes(callsBeforeOutline)
    expect(fetchSpy).toHaveBeenCalledTimes(fetchesBeforeOutline)

    await wrapper.get("button.btn-primary").trigger("click")
    await flushPromises()
    expect(generateHeadstockPrompt).toHaveBeenCalledTimes(1)
    expect(generateHeadstockPrompt).toHaveBeenCalledWith(PROMPT_PAYLOAD)
    expect(wrapper.text()).toContain("PROMPT-TEXT")

    await wrapper.get("button.btn-secondary").trigger("click")
    await flushPromises()
    expect(generateHeadstockPrompt).toHaveBeenCalledTimes(2)
    expect(generateHeadstockPrompt).toHaveBeenLastCalledWith(PROMPT_PAYLOAD)
    fetchSpy.mockRestore()
  })
})
