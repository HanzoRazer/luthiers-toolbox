/**
 * Switch Validator
 * Validates if pickup combinations are supported by hardware configuration
 */

export interface HardwareConfig {
  selector: '3-way' | '5-way' | '5-way-superswitch';
  push_pull: number;
  mini_toggles: number;
}

export type ValidationResult = Record<string, string>;

/**
 * Validate if requested pickup combinations are supported by hardware
 * @param hardware - Hardware configuration (selector type, push/pull switches, mini toggles)
 * @param combos - Array of requested combinations (e.g., ['N', 'B', 'N+M+B', 'split neck'])
 * @returns Object mapping each combo to validation result
 */
export function validateSwitching(
  hardware: HardwareConfig,
  combos: string[]
): ValidationResult {
  const can = new Set<string>();
  const sel = hardware.selector || '3-way';

  // Standard selector positions
  if (sel === '3-way') {
    can.add('N');
    can.add('B');
    can.add('N+B');
  }

  if (sel === '5-way') {
    ['N', 'N+M', 'M', 'M+B', 'B'].forEach(x => can.add(x));
  }

  if (sel === '5-way-superswitch') {
    ['N', 'N+M', 'M', 'M+B', 'B', 'N+B', 'N+M+B'].forEach(x => can.add(x));
  }

  // Advanced switching options
  let advancedSlots = (hardware.push_pull || 0) + (hardware.mini_toggles || 0);
  const advancedMap = ['split neck', 'split bridge', 'HB series', 'HB parallel', 'phase'];

  const results: ValidationResult = {};

  for (const req of combos) {
    if (can.has(req)) {
      results[req] = 'ok';
      continue;
    }

    if (advancedMap.includes(req) && advancedSlots > 0) {
      results[req] = 'ok (uses aux switch)';
      advancedSlots--;
      continue;
    }

    results[req] = 'not supported with current hardware';
  }

  return results;
}
