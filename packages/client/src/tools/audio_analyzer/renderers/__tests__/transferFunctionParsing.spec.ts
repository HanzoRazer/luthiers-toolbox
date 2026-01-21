/**
 * @vitest-environment jsdom
 *
 * Tests for TransferFunctionRenderer JSON parsing logic.
 *
 * Tests the multiple JSON format parsing without mounting Vue component.
 */
import { describe, it, expect } from "vitest";

/**
 * Transfer function point structure
 */
interface TransferFunctionPoint {
  freq: number;
  mag: number;
  phase: number;
}

interface ParsedODS {
  points: TransferFunctionPoint[];
  metadata?: {
    analysisType?: string;
    nModes?: number;
    freqMin?: number;
    freqMax?: number;
  };
}

/**
 * Parser logic (mirrors TransferFunctionRenderer.vue)
 */
function parseTransferFunction(json: unknown): ParsedODS {
  if (!json || typeof json !== "object") {
    throw new Error("Invalid JSON: expected object");
  }

  const obj = json as Record<string, unknown>;
  let points: TransferFunctionPoint[] = [];
  const metadata: ParsedODS["metadata"] = {};

  // Format 1: Parallel Arrays
  if (Array.isArray(obj.frequencies) || Array.isArray(obj.freq)) {
    const freqs = (obj.frequencies || obj.freq || obj.f) as number[];
    const mags = (obj.magnitude || obj.mag || obj.H_mag || obj.amplitude) as number[];
    const phases = (obj.phase || obj.phase_deg || obj.phi) as number[];

    if (!Array.isArray(freqs) || !Array.isArray(mags)) {
      throw new Error("Missing frequency or magnitude arrays");
    }

    points = freqs.map((freq, i) => ({
      freq,
      mag: mags[i] ?? 0,
      phase: phases?.[i] ?? 0,
    }));
  }

  // Format 2: Array of Objects
  else if (Array.isArray(obj.data) || Array.isArray(obj.points) || Array.isArray(obj.transfer_function)) {
    const arr = (obj.data || obj.points || obj.transfer_function) as Record<string, unknown>[];

    points = arr.map((item) => ({
      freq: Number(item.freq ?? item.frequency ?? item.f ?? 0),
      mag: Number(item.mag ?? item.magnitude ?? item.H_mag ?? item.amplitude ?? 0),
      phase: Number(item.phase ?? item.phase_deg ?? item.phi ?? 0),
    }));
  }

  // Format 3: ODS Modal
  else if (obj.modes && Array.isArray(obj.modes)) {
    const modes = obj.modes as Record<string, unknown>[];
    points = modes.map((mode) => ({
      freq: Number(mode.freq ?? mode.frequency ?? 0),
      mag: Number(mode.amplitude ?? mode.mag ?? mode.H ?? 1),
      phase: Number(mode.phase ?? 0),
    }));

    metadata.analysisType = "ODS Modal";
    metadata.nModes = modes.length;
  }

  // Format 4: Complex FRF
  else if (obj.frf || obj.H) {
    const frf = (obj.frf || obj.H) as Record<string, unknown>;
    if (Array.isArray(frf.real) && Array.isArray(frf.imag)) {
      const real = frf.real as number[];
      const imag = frf.imag as number[];
      const freqs = (frf.freq || obj.freq || obj.frequencies) as number[];

      if (!Array.isArray(freqs)) {
        throw new Error("FRF format requires frequencies array");
      }

      points = freqs.map((freq, i) => {
        const r = real[i] ?? 0;
        const im = imag[i] ?? 0;
        return {
          freq,
          mag: Math.sqrt(r * r + im * im),
          phase: Math.atan2(im, r) * (180 / Math.PI),
        };
      });
    }
  }

  // Extract metadata if present
  if (obj.analysis_type) metadata.analysisType = String(obj.analysis_type);
  if (obj.n_modes) metadata.nModes = Number(obj.n_modes);
  if (obj.freq_min) metadata.freqMin = Number(obj.freq_min);
  if (obj.freq_max) metadata.freqMax = Number(obj.freq_max);

  // Filter invalid and sort
  points = points
    .filter((p) => !isNaN(p.freq) && !isNaN(p.mag) && p.freq > 0)
    .sort((a, b) => a.freq - b.freq);

  return { points, metadata };
}

/**
 * dB conversion (mirrors TransferFunctionRenderer.vue)
 */
function toDb(linear: number): number {
  if (linear <= 0) return -100;
  return 20 * Math.log10(linear);
}

describe("parseTransferFunction", () => {
  describe("Format 1: Parallel Arrays", () => {
    it("parses frequencies + magnitude + phase arrays", () => {
      const json = {
        frequencies: [100, 200, 500, 1000],
        magnitude: [0.1, 0.5, 0.2, 0.05],
        phase: [-10, -45, -90, -135],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(4);
      expect(result.points[0]).toEqual({ freq: 100, mag: 0.1, phase: -10 });
      expect(result.points[3]).toEqual({ freq: 1000, mag: 0.05, phase: -135 });
    });

    it("accepts freq alias for frequencies", () => {
      const json = {
        freq: [100, 200],
        magnitude: [0.1, 0.2],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(2);
      expect(result.points[0].freq).toBe(100);
    });

    it("accepts mag alias for magnitude", () => {
      const json = {
        frequencies: [100, 200],
        mag: [0.1, 0.2],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0].mag).toBe(0.1);
    });

    it("defaults phase to 0 when missing", () => {
      const json = {
        frequencies: [100, 200],
        magnitude: [0.1, 0.2],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0].phase).toBe(0);
      expect(result.points[1].phase).toBe(0);
    });
  });

  describe("Format 2: Array of Objects", () => {
    it("parses data array", () => {
      const json = {
        data: [
          { freq: 100, mag: 0.1, phase: -10 },
          { freq: 200, mag: 0.5, phase: -45 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(2);
      expect(result.points[0]).toEqual({ freq: 100, mag: 0.1, phase: -10 });
    });

    it("parses points array", () => {
      const json = {
        points: [
          { frequency: 100, magnitude: 0.1, phase_deg: -10 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0]).toEqual({ freq: 100, mag: 0.1, phase: -10 });
    });

    it("parses transfer_function array", () => {
      const json = {
        transfer_function: [
          { f: 100, H_mag: 0.1, phi: -10 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0]).toEqual({ freq: 100, mag: 0.1, phase: -10 });
    });
  });

  describe("Format 3: ODS Modal", () => {
    it("parses modes array", () => {
      const json = {
        modes: [
          { freq: 82.4, amplitude: 1.0, phase: 0 },
          { freq: 165.0, amplitude: 0.8, phase: -30 },
          { freq: 330.0, amplitude: 0.4, phase: -60 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(3);
      expect(result.points[0]).toEqual({ freq: 82.4, mag: 1.0, phase: 0 });
      expect(result.metadata?.analysisType).toBe("ODS Modal");
      expect(result.metadata?.nModes).toBe(3);
    });

    it("accepts frequency alias in modes", () => {
      const json = {
        modes: [
          { frequency: 100, amplitude: 1.0 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0].freq).toBe(100);
    });
  });

  describe("Format 4: Complex FRF", () => {
    it("parses real + imag arrays", () => {
      // Note: frequencies must be inside frf object to avoid triggering Format 1
      const json = {
        frf: {
          freq: [100, 200],
          real: [0.1, 0.0],
          imag: [0.0, 0.1],
        },
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(2);
      // First point: real=0.1, imag=0 → mag=0.1, phase=0
      expect(result.points[0].mag).toBeCloseTo(0.1);
      expect(result.points[0].phase).toBeCloseTo(0);
      // Second point: real=0, imag=0.1 → mag=0.1, phase=90
      expect(result.points[1].mag).toBeCloseTo(0.1);
      expect(result.points[1].phase).toBeCloseTo(90);
    });

    it("accepts H alias for frf", () => {
      // Note: frequencies must be inside H object to avoid triggering Format 1
      const json = {
        H: {
          freq: [100],
          real: [0.1],
          imag: [0.1],
        },
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(1);
      // mag = sqrt(0.01 + 0.01) = sqrt(0.02) ≈ 0.1414
      expect(result.points[0].mag).toBeCloseTo(Math.SQRT2 * 0.1);
    });

    it("throws when frequencies missing for FRF", () => {
      const json = {
        frf: {
          real: [0.1],
          imag: [0.1],
        },
      };

      expect(() => parseTransferFunction(json)).toThrow("frequencies");
    });
  });

  describe("metadata extraction", () => {
    it("extracts analysis_type", () => {
      const json = {
        analysis_type: "Operational Modal Analysis",
        data: [{ freq: 100, mag: 0.1 }],
      };

      const result = parseTransferFunction(json);
      expect(result.metadata?.analysisType).toBe("Operational Modal Analysis");
    });

    it("extracts n_modes", () => {
      const json = {
        n_modes: 5,
        data: [{ freq: 100, mag: 0.1 }],
      };

      const result = parseTransferFunction(json);
      expect(result.metadata?.nModes).toBe(5);
    });

    it("extracts freq_min and freq_max", () => {
      const json = {
        freq_min: 20,
        freq_max: 2000,
        data: [{ freq: 100, mag: 0.1 }],
      };

      const result = parseTransferFunction(json);
      expect(result.metadata?.freqMin).toBe(20);
      expect(result.metadata?.freqMax).toBe(2000);
    });
  });

  describe("data validation", () => {
    it("filters out points with freq <= 0", () => {
      const json = {
        data: [
          { freq: -10, mag: 0.1 },
          { freq: 0, mag: 0.2 },
          { freq: 100, mag: 0.3 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(1);
      expect(result.points[0].freq).toBe(100);
    });

    it("filters out points with NaN values", () => {
      const json = {
        data: [
          { freq: NaN, mag: 0.1 },
          { freq: 100, mag: NaN },
          { freq: 200, mag: 0.3 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(1);
      expect(result.points[0].freq).toBe(200);
    });

    it("sorts points by frequency", () => {
      const json = {
        data: [
          { freq: 500, mag: 0.1 },
          { freq: 100, mag: 0.2 },
          { freq: 300, mag: 0.3 },
        ],
      };

      const result = parseTransferFunction(json);
      expect(result.points[0].freq).toBe(100);
      expect(result.points[1].freq).toBe(300);
      expect(result.points[2].freq).toBe(500);
    });
  });

  describe("error handling", () => {
    it("throws for null input", () => {
      expect(() => parseTransferFunction(null)).toThrow("Invalid JSON");
    });

    it("throws for non-object input", () => {
      expect(() => parseTransferFunction("string")).toThrow("Invalid JSON");
      expect(() => parseTransferFunction(123)).toThrow("Invalid JSON");
    });

    it("returns empty points for unrecognized format", () => {
      const json = { someOtherField: "value" };
      const result = parseTransferFunction(json);
      expect(result.points).toHaveLength(0);
    });
  });
});

describe("toDb", () => {
  it("converts linear magnitude to dB", () => {
    expect(toDb(1)).toBeCloseTo(0);
    expect(toDb(10)).toBeCloseTo(20);
    expect(toDb(0.1)).toBeCloseTo(-20);
    expect(toDb(0.01)).toBeCloseTo(-40);
  });

  it("handles very small values", () => {
    expect(toDb(0.001)).toBeCloseTo(-60);
    expect(toDb(0.0001)).toBeCloseTo(-80);
  });

  it("floors zero and negative values to -100 dB", () => {
    expect(toDb(0)).toBe(-100);
    expect(toDb(-1)).toBe(-100);
  });
});

describe("typical tap_tone_pi ODS data", () => {
  /**
   * Simulated ODS snapshot from tap_tone_pi
   */
  it("parses typical ods_snapshot.json structure", () => {
    const odsSnapshot = {
      analysis_type: "ODS",
      n_modes: 4,
      freq_min: 30,
      freq_max: 1000,
      modes: [
        { freq: 82.4, amplitude: 0.95, phase: 0, damping: 0.02 },
        { freq: 165.0, amplitude: 0.72, phase: -15, damping: 0.025 },
        { freq: 247.5, amplitude: 0.58, phase: -30, damping: 0.03 },
        { freq: 330.0, amplitude: 0.41, phase: -45, damping: 0.035 },
      ],
    };

    const result = parseTransferFunction(odsSnapshot);

    expect(result.points).toHaveLength(4);
    // Note: analysis_type from JSON overrides the default "ODS Modal" from Format 3
    expect(result.metadata?.analysisType).toBe("ODS");
    expect(result.metadata?.nModes).toBe(4);

    // Verify first mode (fundamental)
    expect(result.points[0].freq).toBe(82.4);
    expect(result.points[0].mag).toBe(0.95);
    expect(result.points[0].phase).toBe(0);

    // Verify second harmonic
    expect(result.points[1].freq).toBe(165.0);
    expect(result.points[1].mag).toBe(0.72);
  });
});
