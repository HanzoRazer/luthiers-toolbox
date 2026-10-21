import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import { describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import HeadstockParametricOutlinePreview from "../HeadstockParametricOutlinePreview.vue"
import {
  HEADSTOCK_OUTLINE_DEFAULTS,
  HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX,
  HEADSTOCK_OUTLINE_PARAMETER_DEFS,
  buildHeadstockOutlinePath,
} from "@/design-utilities/lutherie/headstock/parametricOutline"

const FORBIDDEN_CONTROL = /export|download|dxf|g-code|gcode|\bcam\b|approve|manufacture/i

function pathD(wrapper: ReturnType<typeof mount>) {
  return wrapper.find("path").attributes("d")
}

describe("HeadstockParametricOutlinePreview", () => {
  it("renders the recovered default outline and its notices", () => {
    const wrapper = mount(HeadstockParametricOutlinePreview)
    expect(wrapper.get("h2").text()).toBe("Parametric outline preview")
    expect(wrapper.text()).toContain("Recovered design model")
    expect(wrapper.text()).toContain("Design preview only. This outline is not a manufacturing drawing.")
    expect(wrapper.text()).toContain("Controls use recovered model-space outline units, not millimeters.")
    expect(wrapper.get("svg").attributes("viewBox")).toBe(HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX)
    expect(HEADSTOCK_OUTLINE_DISPLAY_VIEWBOX).not.toBe("0 0 200 320")
    expect(pathD(wrapper)).toBe(buildHeadstockOutlinePath(HEADSTOCK_OUTLINE_DEFAULTS, "rounded"))
    expect(wrapper.find("path").isVisible()).toBe(true)
  })

  it("labels every control", () => {
    const wrapper = mount(HeadstockParametricOutlinePreview)
    expect(wrapper.get("label[for='headstock-tip-style']").text()).toContain("Tip style")
    for (const def of HEADSTOCK_OUTLINE_PARAMETER_DEFS) {
      const label = wrapper.get(`label[for='outline-${def.id}']`)
      expect(label.text()).toContain(def.label)
      expect(wrapper.get(`#outline-${def.id}`).element.tagName).toBe("INPUT")
    }
  })

  it("updates the path for tip style, both parameter groups, and reset", async () => {
    const wrapper = mount(HeadstockParametricOutlinePreview)
    const initial = pathD(wrapper)

    await wrapper.get("#headstock-tip-style").setValue("scroll")
    const scrolled = pathD(wrapper)
    expect(scrolled).not.toBe(initial)
    expect(scrolled).toBe(buildHeadstockOutlinePath(HEADSTOCK_OUTLINE_DEFAULTS, "scroll"))

    await wrapper.get("#outline-nutWidth").setValue("80")
    const wider = pathD(wrapper)
    expect(wider).not.toBe(scrolled)

    await wrapper.get("#outline-bassShoulder").setValue("8")
    expect(pathD(wrapper)).not.toBe(wider)

    await wrapper.get("button").trigger("click")
    expect(pathD(wrapper)).toBe(initial)
    expect((wrapper.get("#headstock-tip-style").element as HTMLSelectElement).value).toBe("rounded")
  })

  it("shows a validation error and hides the path for invalid input", async () => {
    const wrapper = mount(HeadstockParametricOutlinePreview)
    await wrapper.get("#outline-length").setValue("nope")
    expect(wrapper.get("[role='alert']").text()).toMatch(/Length/)
    expect(wrapper.find("path").exists()).toBe(false)
  })

  it("does not fetch, store, export, or import the archive", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch")
    const localBefore = window.localStorage.length
    const sessionBefore = window.sessionStorage.length
    const wrapper = mount(HeadstockParametricOutlinePreview)
    await wrapper.get("#outline-taper").setValue("12")
    await wrapper.get("#headstock-tip-style").setValue("pointed")
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(window.localStorage.length).toBe(localBefore)
    expect(window.sessionStorage.length).toBe(sessionBefore)
    const controls = wrapper.findAll("button, a").map((node) => node.text())
    expect(controls.some((text) => FORBIDDEN_CONTROL.test(text))).toBe(false)
    fetchSpy.mockRestore()

    const componentSource = readFileSync(
      resolve("src/components/art-studio/headstock/HeadstockParametricOutlinePreview.vue"),
      "utf8",
    )
    const kernelSource = readFileSync(
      resolve("src/design-utilities/lutherie/headstock/parametricOutline.ts"),
      "utf8",
    )
    expect(componentSource).not.toContain("v-html")
    expect(componentSource).not.toMatch(/from\s+["'][^"']*archive\//)
    expect(kernelSource).not.toMatch(/from\s+["'][^"']*archive\//)
  })
})
