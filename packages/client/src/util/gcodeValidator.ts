/**
 * G-code Validator — pre-simulation syntax checker.
 *
 * Validates common G-code errors without running a full simulation.
 * Used by ToolpathPlayer to show issues before sending to the backend.
 */

export interface ValidationIssue {
  line: number;
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  suggestion?: string;
}

export interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
  stats: {
    totalLines: number;
    moveCount: number;
    hasArcs: boolean;
    hasToolChanges: boolean;
  };
}

export function validateGcode(gcode: string): ValidationResult {
  const issues: ValidationIssue[] = [];
  const lines = gcode.split("\n");
  let moveCount = 0;
  let hasArcs = false;
  let hasToolChanges = false;
  let feedSet = false;
  let unitsSet = false;

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i].trim();
    if (!raw || raw.startsWith("(") || raw.startsWith(";") || raw.startsWith("%")) continue;

    const ln = i + 1;
    const upper = raw.toUpperCase();

    // Track state
    if (/F\d/.test(upper)) feedSet = true;
    if (/G20|G21/.test(upper)) unitsSet = true;
    if (/G0?[23]/.test(upper)) hasArcs = true;
    if (/T\d/.test(upper)) hasToolChanges = true;
    if (/G[0-3]\b/.test(upper)) moveCount++;

    // Arc without I/J/R
    if (/G0?[23]\b/.test(upper) && !/[IJR]/.test(upper)) {
      issues.push({
        line: ln,
        severity: "error",
        code: "ARC_NO_PARAMS",
        message: "Arc command without I, J, or R parameters",
        suggestion: "Add I/J offsets or R radius",
      });
    }

    // Zero feed
    if (/F0(?!\.)/.test(upper)) {
      issues.push({
        line: ln,
        severity: "error",
        code: "FEED_ZERO",
        message: "Feed rate set to zero",
        suggestion: "Set a positive feed rate for cutting moves",
      });
    }

    // Negative spindle speed
    if (/S-\d/.test(upper)) {
      issues.push({
        line: ln,
        severity: "error",
        code: "SPINDLE_NEG",
        message: "Negative spindle speed",
        suggestion: "Use M03/M04 for direction, S for positive speed",
      });
    }

    // Conflicting unit modes on same line
    if (/G20/.test(upper) && /G21/.test(upper)) {
      issues.push({
        line: ln,
        severity: "error",
        code: "UNITS_CONFLICT",
        message: "G20 and G21 on the same line",
      });
    }
  }

  // Global checks
  if (moveCount > 0 && !feedSet) {
    issues.push({
      line: 0,
      severity: "warning",
      code: "NO_FEED",
      message: "No feed rate (F) set — default will be used",
      suggestion: "Add F<rate> before cutting moves",
    });
  }
  if (moveCount > 0 && !unitsSet) {
    issues.push({
      line: 0,
      severity: "info",
      code: "NO_UNITS",
      message: "Units not specified (G20/G21) — assuming mm",
    });
  }

  return {
    valid: issues.filter((i) => i.severity === "error").length === 0,
    issues,
    stats: { totalLines: lines.length, moveCount, hasArcs, hasToolChanges },
  };
}
