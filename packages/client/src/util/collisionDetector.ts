/**
 * CollisionDetector — P4.2 Collision Detection
 *
 * Detects potential machine crashes before they happen:
 * - Rapid moves into material
 * - Tool/holder collisions with fixtures
 * - Excessive plunge rates
 * - Out-of-bounds moves
 *
 * Value: Prevents expensive machine crashes - #1 value proposition
 */

import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";
import type { StockMaterial } from "./stockSimulator";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CollisionSeverity = "critical" | "warning" | "info";

export type CollisionType =
  | "rapid-into-material"
  | "fixture-collision"
  | "holder-collision"
  | "out-of-bounds"
  | "excessive-plunge"
  | "tool-breakage-risk"
  | "spindle-off-cutting";

export interface Collision {
  /** Type of collision */
  type: CollisionType;
  /** Severity level */
  severity: CollisionSeverity;
  /** Human-readable description */
  message: string;
  /** Segment that caused collision */
  segment: MoveSegment;
  /** Segment index */
  segmentIndex: number;
  /** G-code line number */
  lineNumber: number;
  /** Position where collision occurs */
  position: [number, number, number];
  /** Additional context */
  details?: Record<string, unknown>;
}

export interface Fixture {
  /** Fixture name/ID */
  name: string;
  /** Fixture type */
  type: "clamp" | "vise" | "bolt" | "custom";
  /** Bounding box */
  bounds: {
    x_min: number;
    x_max: number;
    y_min: number;
    y_max: number;
    z_min: number;
    z_max: number;
  };
  /** Color for rendering */
  color?: string;
}

export interface CollisionConfig {
  /** Tool diameter in mm */
  toolDiameter: number;
  /** Tool stickout length in mm */
  toolStickout?: number;
  /** Holder diameter in mm */
  holderDiameter?: number;
  /** Holder length in mm */
  holderLength?: number;
  /** Safe Z height in mm */
  safeZ?: number;
  /** Machine bounds (soft limits) */
  machineBounds?: SimulateBounds;
  /** Maximum plunge rate (mm/min) */
  maxPlungeRate?: number;
  /** Fixtures to check against */
  fixtures?: Fixture[];
  /** Stock material for material detection */
  stock?: StockMaterial;
}

export interface CollisionReport {
  /** All detected collisions */
  collisions: Collision[];
  /** Count by severity */
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  /** Summary message */
  summary: string;
  /** Is safe to run? (no critical collisions) */
  isSafe: boolean;
}

// ---------------------------------------------------------------------------
// CollisionDetector Class
// ---------------------------------------------------------------------------

export class CollisionDetector {
  private config: CollisionConfig;

  constructor(config: CollisionConfig) {
    this.config = {
      toolStickout: 50,
      holderDiameter: config.toolDiameter * 2,
      holderLength: 40,
      safeZ: 5,
      maxPlungeRate: 500,
      fixtures: [],
      ...config,
    };
  }

  /**
   * Update configuration
   */
  setConfig(config: Partial<CollisionConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Add a fixture
   */
  addFixture(fixture: Fixture): void {
    this.config.fixtures = this.config.fixtures || [];
    this.config.fixtures.push(fixture);
  }

  /**
   * Clear all fixtures
   */
  clearFixtures(): void {
    this.config.fixtures = [];
  }

  /**
   * Check all segments for collisions
   */
  checkAll(segments: MoveSegment[]): CollisionReport {
    const collisions: Collision[] = [];

    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      const segmentCollisions = this.checkSegment(segment, i, segments);
      collisions.push(...segmentCollisions);
    }

    return this.generateReport(collisions);
  }

  /**
   * Check a single segment for collisions
   */
  checkSegment(
    segment: MoveSegment,
    index: number,
    allSegments?: MoveSegment[]
  ): Collision[] {
    const collisions: Collision[] = [];

    // 1. Rapid into material
    if (segment.type === "rapid") {
      const materialCollision = this.checkRapidIntoMaterial(segment, index);
      if (materialCollision) collisions.push(materialCollision);
    }

    // 2. Fixture collisions
    const fixtureCollisions = this.checkFixtureCollisions(segment, index);
    collisions.push(...fixtureCollisions);

    // 3. Out of bounds
    const boundsCollision = this.checkBounds(segment, index);
    if (boundsCollision) collisions.push(boundsCollision);

    // 4. Excessive plunge rate
    const plungeCollision = this.checkPlungeRate(segment, index);
    if (plungeCollision) collisions.push(plungeCollision);

    // 5. Spindle off while cutting (requires M-code context)
    // This would need machine state tracking

    return collisions;
  }

  /**
   * Check if rapid move goes into material
   */
  private checkRapidIntoMaterial(
    segment: MoveSegment,
    index: number
  ): Collision | null {
    const { stock, toolDiameter } = this.config;
    if (!stock) return null;

    const [x1, y1, z1] = segment.from_pos;
    const [x2, y2, z2] = segment.to_pos;

    // Check if rapid moves below safe Z
    const safeZ = this.config.safeZ ?? 5;
    if (z2 >= safeZ && z1 >= safeZ) return null;

    // Check if path intersects stock
    const intersects = this.lineIntersectsStock(
      segment.from_pos,
      segment.to_pos,
      toolDiameter / 2,
      stock
    );

    if (intersects) {
      return {
        type: "rapid-into-material",
        severity: "critical",
        message: `Rapid move crashes into material at Z=${z2.toFixed(2)}mm`,
        segment,
        segmentIndex: index,
        lineNumber: segment.line_number,
        position: [x2, y2, z2],
        details: {
          safeZ,
          targetZ: z2,
        },
      };
    }

    return null;
  }

  /**
   * Check for fixture collisions
   */
  private checkFixtureCollisions(
    segment: MoveSegment,
    index: number
  ): Collision[] {
    const collisions: Collision[] = [];
    const fixtures = this.config.fixtures || [];

    for (const fixture of fixtures) {
      // Check tool collision
      const toolCollision = this.checkToolFixtureCollision(segment, index, fixture);
      if (toolCollision) collisions.push(toolCollision);

      // Check holder collision (if holder defined)
      if (this.config.holderDiameter && this.config.holderLength) {
        const holderCollision = this.checkHolderFixtureCollision(segment, index, fixture);
        if (holderCollision) collisions.push(holderCollision);
      }
    }

    return collisions;
  }

  /**
   * Check tool vs fixture collision
   */
  private checkToolFixtureCollision(
    segment: MoveSegment,
    index: number,
    fixture: Fixture
  ): Collision | null {
    const toolRadius = this.config.toolDiameter / 2;
    const [x, y, z] = segment.to_pos;

    // Expand fixture bounds by tool radius
    const fb = fixture.bounds;
    if (
      x + toolRadius > fb.x_min &&
      x - toolRadius < fb.x_max &&
      y + toolRadius > fb.y_min &&
      y - toolRadius < fb.y_max &&
      z < fb.z_max &&
      z > fb.z_min
    ) {
      return {
        type: "fixture-collision",
        severity: "critical",
        message: `Tool collides with fixture "${fixture.name}"`,
        segment,
        segmentIndex: index,
        lineNumber: segment.line_number,
        position: [x, y, z],
        details: {
          fixture: fixture.name,
          fixtureType: fixture.type,
        },
      };
    }

    return null;
  }

  /**
   * Check holder vs fixture collision
   */
  private checkHolderFixtureCollision(
    segment: MoveSegment,
    index: number,
    fixture: Fixture
  ): Collision | null {
    const holderRadius = (this.config.holderDiameter || 20) / 2;
    const holderLength = this.config.holderLength || 40;
    const toolStickout = this.config.toolStickout || 50;
    const [x, y, z] = segment.to_pos;

    // Holder Z range (above tool tip)
    const holderZMin = z + toolStickout;
    const holderZMax = z + toolStickout + holderLength;

    const fb = fixture.bounds;
    if (
      x + holderRadius > fb.x_min &&
      x - holderRadius < fb.x_max &&
      y + holderRadius > fb.y_min &&
      y - holderRadius < fb.y_max &&
      holderZMin < fb.z_max &&
      holderZMax > fb.z_min
    ) {
      return {
        type: "holder-collision",
        severity: "warning",
        message: `Tool holder may collide with fixture "${fixture.name}"`,
        segment,
        segmentIndex: index,
        lineNumber: segment.line_number,
        position: [x, y, z],
        details: {
          fixture: fixture.name,
          holderZ: [holderZMin, holderZMax],
        },
      };
    }

    return null;
  }

  /**
   * Check if move is out of machine bounds
   */
  private checkBounds(segment: MoveSegment, index: number): Collision | null {
    const bounds = this.config.machineBounds;
    if (!bounds) return null;

    const [x, y, z] = segment.to_pos;

    if (
      x < bounds.x_min ||
      x > bounds.x_max ||
      y < bounds.y_min ||
      y > bounds.y_max ||
      z < bounds.z_min ||
      z > bounds.z_max
    ) {
      return {
        type: "out-of-bounds",
        severity: "critical",
        message: `Move exceeds machine limits at (${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)})`,
        segment,
        segmentIndex: index,
        lineNumber: segment.line_number,
        position: [x, y, z],
        details: {
          machineBounds: bounds,
        },
      };
    }

    return null;
  }

  /**
   * Check for excessive plunge rate
   */
  private checkPlungeRate(segment: MoveSegment, index: number): Collision | null {
    if (segment.type === "rapid") return null;

    const [x1, y1, z1] = segment.from_pos;
    const [x2, y2, z2] = segment.to_pos;

    // Only check if plunging (Z decreasing)
    if (z2 >= z1) return null;

    const zDelta = z1 - z2;
    const xyDist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);

    // Pure plunge (no XY movement)
    if (xyDist < 0.1 && segment.feed) {
      const plungeRate = segment.feed;
      const maxPlunge = this.config.maxPlungeRate || 500;

      if (plungeRate > maxPlunge) {
        return {
          type: "excessive-plunge",
          severity: "warning",
          message: `Plunge rate ${plungeRate}mm/min exceeds recommended ${maxPlunge}mm/min`,
          segment,
          segmentIndex: index,
          lineNumber: segment.line_number,
          position: [x2, y2, z2],
          details: {
            actualRate: plungeRate,
            recommendedMax: maxPlunge,
            plungeDepth: zDelta,
          },
        };
      }
    }

    return null;
  }

  /**
   * Check if line intersects stock material
   */
  private lineIntersectsStock(
    from: [number, number, number],
    to: [number, number, number],
    radius: number,
    stock: StockMaterial
  ): boolean {
    const [x1, y1, z1] = from;
    const [x2, y2, z2] = to;

    // Quick bounds check
    const minX = Math.min(x1, x2) - radius;
    const maxX = Math.max(x1, x2) + radius;
    const minY = Math.min(y1, y2) - radius;
    const maxY = Math.max(y1, y2) + radius;
    const minZ = Math.min(z1, z2);

    // Check if line overlaps stock bounds
    if (
      maxX < stock.bounds.x_min ||
      minX > stock.bounds.x_max ||
      maxY < stock.bounds.y_min ||
      minY > stock.bounds.y_max ||
      minZ > 0 // Above stock top
    ) {
      return false;
    }

    // Sample along line and check voxels
    const dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2);
    const steps = Math.max(1, Math.ceil(dist / stock.resolution));

    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const x = x1 + (x2 - x1) * t;
      const y = y1 + (y2 - y1) * t;
      const z = z1 + (z2 - z1) * t;

      // Check if point is inside stock
      if (this.pointInStock(x, y, z, radius, stock)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Check if point (with radius) is inside stock material
   */
  private pointInStock(
    x: number,
    y: number,
    z: number,
    radius: number,
    stock: StockMaterial
  ): boolean {
    // Z check: below stock top
    if (z > 0) return false;

    // Convert to grid coordinates
    const gx = Math.round((x - stock.bounds.x_min) / stock.resolution);
    const gy = Math.round((y - stock.bounds.y_min) / stock.resolution);

    // Bounds check
    if (gx < 0 || gx >= stock.width || gy < 0 || gy >= stock.height) {
      return false;
    }

    // Check voxel value
    const idx = gy * stock.width + gx;
    return stock.voxels[idx] > 0;
  }

  /**
   * Generate collision report
   */
  private generateReport(collisions: Collision[]): CollisionReport {
    const criticalCount = collisions.filter((c) => c.severity === "critical").length;
    const warningCount = collisions.filter((c) => c.severity === "warning").length;
    const infoCount = collisions.filter((c) => c.severity === "info").length;

    let summary: string;
    if (collisions.length === 0) {
      summary = "No collisions detected - safe to run";
    } else if (criticalCount > 0) {
      summary = `${criticalCount} critical collision(s) detected - DO NOT RUN`;
    } else if (warningCount > 0) {
      summary = `${warningCount} warning(s) detected - review before running`;
    } else {
      summary = `${infoCount} minor issue(s) detected`;
    }

    return {
      collisions,
      criticalCount,
      warningCount,
      infoCount,
      summary,
      isSafe: criticalCount === 0,
    };
  }
}

// ---------------------------------------------------------------------------
// Factory function
// ---------------------------------------------------------------------------

export function createCollisionDetector(config: CollisionConfig): CollisionDetector {
  return new CollisionDetector(config);
}

export default CollisionDetector;
