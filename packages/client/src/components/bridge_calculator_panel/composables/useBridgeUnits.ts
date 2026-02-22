/**
 * BridgeCalculatorPanel unit conversion composable.
 */
import type { UiFieldKey } from './bridgeCalculatorTypes'

export interface BridgeUnitsReturn {
  mmToIn: (value: number) => number
  inToMm: (value: number) => number
  convertUiToMetric: () => void
  convertUiToImperial: () => void
}

export function useBridgeUnits(
  ui: Record<UiFieldKey, number>
): BridgeUnitsReturn {
  /**
   * Convert millimeters to inches.
   */
  function mmToIn(value: number): number {
    return value / 25.4
  }

  /**
   * Convert inches to millimeters.
   */
  function inToMm(value: number): number {
    return value * 25.4
  }

  /**
   * Convert all UI values to metric (mm).
   */
  function convertUiToMetric(): void {
    ui.scale = inToMm(ui.scale)
    ui.spread = inToMm(ui.spread)
    ui.compTreble = inToMm(ui.compTreble)
    ui.compBass = inToMm(ui.compBass)
    ui.slotWidth = inToMm(ui.slotWidth)
    ui.slotLength = inToMm(ui.slotLength)
  }

  /**
   * Convert all UI values to imperial (inches).
   */
  function convertUiToImperial(): void {
    ui.scale = mmToIn(ui.scale)
    ui.spread = mmToIn(ui.spread)
    ui.compTreble = mmToIn(ui.compTreble)
    ui.compBass = mmToIn(ui.compBass)
    ui.slotWidth = mmToIn(ui.slotWidth)
    ui.slotLength = mmToIn(ui.slotLength)
  }

  return {
    mmToIn,
    inToMm,
    convertUiToMetric,
    convertUiToImperial
  }
}
