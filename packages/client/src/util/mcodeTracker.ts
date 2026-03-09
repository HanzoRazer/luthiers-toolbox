/**
 * M-code tracker — extracts machine state from G-code lines.
 *
 * Tracks spindle on/off/direction, coolant, tool changes, and program control
 * so the HUD can display current machine state during playback.
 */

export interface MachineState {
  spindleOn: boolean;
  spindleDir: "cw" | "ccw";
  spindleSpeed: number;
  coolant: "flood" | "mist" | "off";
  currentTool: number;
}

const INITIAL: MachineState = {
  spindleOn: false,
  spindleDir: "cw",
  spindleSpeed: 0,
  coolant: "off",
  currentTool: 0,
};

/**
 * Parse one G-code line and return updated machine state.
 * Non-mutating — returns a new object if anything changed.
 */
export function updateMachineState(
  line: string,
  prev: MachineState,
): MachineState {
  const upper = line.toUpperCase();
  let next = prev;

  function clone(): MachineState {
    if (next === prev) next = { ...prev };
    return next;
  }

  // Spindle
  if (/M0?3\b/.test(upper)) {
    clone().spindleOn = true;
    next.spindleDir = "cw";
  }
  if (/M0?4\b/.test(upper)) {
    clone().spindleOn = true;
    next.spindleDir = "ccw";
  }
  if (/M0?5\b/.test(upper)) {
    clone().spindleOn = false;
  }

  // Spindle speed
  const sMatch = upper.match(/S(\d+)/);
  if (sMatch) {
    clone().spindleSpeed = parseInt(sMatch[1], 10);
  }

  // Coolant
  if (/M0?7\b/.test(upper)) clone().coolant = "mist";
  if (/M0?8\b/.test(upper)) clone().coolant = "flood";
  if (/M0?9\b/.test(upper)) clone().coolant = "off";

  // Tool
  const tMatch = upper.match(/T(\d+)/);
  if (tMatch) {
    clone().currentTool = parseInt(tMatch[1], 10);
  }

  return next;
}

/**
 * Build a machine-state snapshot array aligned with segments.
 * Each element is the machine state *entering* that segment.
 */
export function buildMachineStates(
  segments: { line_text: string }[],
): MachineState[] {
  const states: MachineState[] = [];
  let state: MachineState = { ...INITIAL };
  for (const seg of segments) {
    state = updateMachineState(seg.line_text, state);
    states.push(state);
  }
  return states;
}
