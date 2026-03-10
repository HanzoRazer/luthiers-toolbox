/**
 * measurementTool — P5 Distance Measurement Utility
 *
 * Click two points on the toolpath to measure:
 * - Linear distance (2D and 3D)
 * - X/Y/Z deltas
 * - Angle from horizontal
 *
 * Features:
 * - Multi-measurement support
 * - Unit conversion (mm/inch)
 * - Measurement history
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Point3D {
  x: number;
  y: number;
  z: number;
}

export interface Measurement {
  /** Unique ID */
  id: string;
  /** Start point */
  start: Point3D;
  /** End point */
  end: Point3D;
  /** Linear distance in mm */
  distance: number;
  /** X delta */
  deltaX: number;
  /** Y delta */
  deltaY: number;
  /** Z delta */
  deltaZ: number;
  /** 2D distance (XY plane) */
  distance2D: number;
  /** Angle from X axis in degrees (XY plane) */
  angleXY: number;
  /** Angle from XY plane (elevation) */
  angleZ: number;
  /** Timestamp */
  createdAt: number;
  /** Optional label */
  label?: string;
}

export interface MeasurementConfig {
  /** Unit system */
  units: "mm" | "inch";
  /** Decimal precision */
  precision: number;
  /** Show Z measurements */
  show3D: boolean;
  /** Max measurements to keep */
  maxHistory: number;
}

// ---------------------------------------------------------------------------
// Default config
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG: MeasurementConfig = {
  units: "mm",
  precision: 2,
  show3D: true,
  maxHistory: 10,
};

// ---------------------------------------------------------------------------
// Conversion constants
// ---------------------------------------------------------------------------

const MM_TO_INCH = 0.03937007874;

// ---------------------------------------------------------------------------
// Measurement Tool
// ---------------------------------------------------------------------------

export class MeasurementTool {
  private config: MeasurementConfig;
  private measurements: Measurement[] = [];
  private pendingStart: Point3D | null = null;
  private idCounter = 0;

  constructor(config: Partial<MeasurementConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Set first point of measurement
   */
  setStart(point: Point3D): void {
    this.pendingStart = { ...point };
  }

  /**
   * Check if we have a pending start point
   */
  hasPendingStart(): boolean {
    return this.pendingStart !== null;
  }

  /**
   * Get the pending start point
   */
  getPendingStart(): Point3D | null {
    return this.pendingStart;
  }

  /**
   * Complete measurement with end point
   */
  complete(end: Point3D): Measurement | null {
    if (!this.pendingStart) return null;

    const start = this.pendingStart;
    this.pendingStart = null;

    const measurement = this.calculate(start, end);
    this.measurements.unshift(measurement);

    // Trim history
    if (this.measurements.length > this.config.maxHistory) {
      this.measurements = this.measurements.slice(0, this.config.maxHistory);
    }

    return measurement;
  }

  /**
   * Cancel pending measurement
   */
  cancel(): void {
    this.pendingStart = null;
  }

  /**
   * Calculate measurement between two points
   */
  private calculate(start: Point3D, end: Point3D): Measurement {
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;
    const deltaZ = end.z - start.z;

    const distance2D = Math.sqrt(deltaX ** 2 + deltaY ** 2);
    const distance = Math.sqrt(deltaX ** 2 + deltaY ** 2 + deltaZ ** 2);

    // Angle in XY plane (from positive X axis)
    const angleXY = Math.atan2(deltaY, deltaX) * (180 / Math.PI);

    // Elevation angle (from XY plane)
    const angleZ = Math.atan2(deltaZ, distance2D) * (180 / Math.PI);

    return {
      id: `m-${++this.idCounter}`,
      start: { ...start },
      end: { ...end },
      distance,
      deltaX,
      deltaY,
      deltaZ,
      distance2D,
      angleXY,
      angleZ,
      createdAt: Date.now(),
    };
  }

  /**
   * Get all measurements
   */
  getMeasurements(): Measurement[] {
    return [...this.measurements];
  }

  /**
   * Get latest measurement
   */
  getLatest(): Measurement | null {
    return this.measurements[0] || null;
  }

  /**
   * Remove a measurement by ID
   */
  remove(id: string): void {
    this.measurements = this.measurements.filter((m) => m.id !== id);
  }

  /**
   * Clear all measurements
   */
  clear(): void {
    this.measurements = [];
    this.pendingStart = null;
  }

  /**
   * Format distance with units
   */
  formatDistance(mm: number): string {
    const value = this.config.units === "inch" ? mm * MM_TO_INCH : mm;
    const unit = this.config.units === "inch" ? "in" : "mm";
    return `${value.toFixed(this.config.precision)} ${unit}`;
  }

  /**
   * Format angle
   */
  formatAngle(degrees: number): string {
    return `${degrees.toFixed(1)}°`;
  }

  /**
   * Get formatted measurement summary
   */
  formatMeasurement(m: Measurement): string {
    const dist = this.formatDistance(m.distance);
    if (!this.config.show3D || Math.abs(m.deltaZ) < 0.001) {
      return `${dist} @ ${this.formatAngle(m.angleXY)}`;
    }
    return `${dist} (2D: ${this.formatDistance(m.distance2D)})`;
  }

  /**
   * Update configuration
   */
  setConfig(config: Partial<MeasurementConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration
   */
  getConfig(): MeasurementConfig {
    return { ...this.config };
  }
}

// ---------------------------------------------------------------------------
// Colors for measurement rendering
// ---------------------------------------------------------------------------

export const MEASUREMENT_COLORS = {
  line: "#00ffff",
  lineHex: 0x00ffff,
  point: "#ff00ff",
  pointHex: 0xff00ff,
  text: "#ffffff",
  pending: "#ffff00",
  pendingHex: 0xffff00,
};

export default MeasurementTool;
