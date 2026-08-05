/**
 * BR-044A — component-level witness for the frontend radiation-ratio collapse.
 *
 * EVIDENCE ONLY. These CHARACTERISATION assertions record rendered behaviour
 * on the shipped component. They are not desired-behaviour contracts and may
 * be inverted by the separately authorized BR-044B repair.
 */

import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import StiffnessIndexPanel from '../StiffnessIndexPanel.vue'

function renderedRadiationRatioValues(wrapper: ReturnType<typeof mount>): number[] {
  return wrapper
    .findAll('tbody .sip-row')
    .map((row) => row.findAll('td')[4]?.text())
    .filter((value): value is string => Boolean(value) && value !== '—')
    .map(Number)
}

describe('BR-044A · StiffnessIndexPanel component witness', () => {
  it('TC-07 CHARACTERISATION: renders the thousand-scaled radiation ratio', () => {
    const wrapper = mount(StiffnessIndexPanel)

    const selectedValue = wrapper.find('.sip-indices-grid .sip-idx-val')
    const rendered = Number(selectedValue.text())

    expect(rendered).toBeGreaterThan(1000)
    expect(rendered).toBeCloseTo((5074 / 435) * 1000, 2)
    expect(wrapper.find('.sip-indices-grid .sip-idx-unit').text()).toBe('c/ρ ×10³')
  })

  it('TC-08 CHARACTERISATION: every visible soundboard row renders the Excellent rating', async () => {
    const wrapper = mount(StiffnessIndexPanel)
    const rows = wrapper.findAll('tbody .sip-row')

    expect(rows.length).toBeGreaterThan(3)

    const ratings = new Set<string>()
    for (const row of rows) {
      await row.trigger('click')
      await nextTick()
      ratings.add(wrapper.find('.sip-soundboard-rating').text())
    }

    expect(ratings).toEqual(new Set(['Soundboard quality: Excellent']))
  })

  it('TC-09 CHARACTERISATION: all visible radiation-ratio values collapse to one color band', () => {
    const wrapper = mount(StiffnessIndexPanel)
    const valueNodes = wrapper.findAll('tbody .sip-row td:nth-child(5) .sip-val')

    expect(valueNodes.length).toBeGreaterThan(3)

    const colors = new Set(valueNodes.map((node) => node.attributes('style')))
    expect(colors.size).toBe(1)
    expect([...colors][0]).toContain('color')
  })

  it('TC-10 CHARACTERISATION: visible labels publish the same ×10³ profile', () => {
    const wrapper = mount(StiffnessIndexPanel)
    const text = wrapper.text()

    expect(wrapper.find('th[title*="Radiation ratio"]').text()).toBe('c/ρ ×10³')
    expect(text).toContain('Radiation ratio')
    expect(text).toContain('c/ρ ×10³')
  })

  it('records that every rendered soundboard value is above the highest 12.0 threshold', () => {
    const wrapper = mount(StiffnessIndexPanel)
    const values = renderedRadiationRatioValues(wrapper)

    expect(values.length).toBeGreaterThan(3)
    expect(values.every((value) => value > 12.0)).toBe(true)
    expect(values.every((value) => value > 1000)).toBe(true)
  })
})
