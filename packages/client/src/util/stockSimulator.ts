/**
 * StockSimulator — P4.1 Material Removal Simulation
 *
 * Voxel-based 2D stock material representation for toolpath visualization.
 * Shows material removal as toolpath executes, identifies uncut areas.
 *
 * Features:
 * - Configurable stock dimensions and resolution
 * - Real-time material subtraction along toolpath
 * - Efficient typed array storage (Uint8Array)
 * - Depth-aware removal for 2.5D machining
 */

import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StockMaterial {
  /** Stock bounds in mm */
  bounds: SimulateBounds;
  /** Resolution in mm per voxel (smaller = more detail, more memory) */
  resolution: number;
  /** Voxel grid dimensions */
  width: number;
  height: number;
  /** Stock thickness (Z depth) in mm */
  thickness: number;
  /** Voxel data: 0 = air, 255 = full material, 1-254 = partial depth */
  voxels: Uint8Array;
  /** Original voxels for reset */
  originalVoxels: Uint8Array;
}

export interface StockConfig {
  /** Stock width in mm (auto-detect from bounds if not specified) */
  width?: number;
  /** Stock height in mm */
  height?: number;
  /** Stock thickness in mm */
  thickness?: number;
  /** Margin around toolpath bounds in mm */
  margin?: number;
  /** Resolution in mm per voxel (default: 0.5) */
  resolution?: number;
}

export interface RemovalStats {
  /** Total voxels in stock */
  totalVoxels: number;
  /** Voxels removed */
  removedVoxels: number;
  /** Percentage material removed */
  percentRemoved: number;
  /** Estimated volume removed in mm³ */
  volumeRemoved: number;
}

// ---------------------------------------------------------------------------
// StockSimulator Class
// ---------------------------------------------------------------------------

export class StockSimulator {
  private stock: StockMaterial | null = null;
  private toolDiameter: number = 6;
  private currentSegmentIndex: number = -1;

  /**
   * Initialize stock material from toolpath bounds
   */
  initializeFromBounds(bounds: SimulateBounds, config: StockConfig = {}): StockMaterial {
    const margin = config.margin ?? 10;
    const resolution = config.resolution ?? 0.5;
    const thickness = config.thickness ?? Math.abs(bounds.z_min) + 5;

    // Calculate stock dimensions
    const stockWidth = config.width ?? (bounds.x_max - bounds.x_min + margin * 2);
    const stockHeight = config.height ?? (bounds.y_max - bounds.y_min + margin * 2);

    // Voxel grid dimensions
    const gridWidth = Math.ceil(stockWidth / resolution);
    const gridHeight = Math.ceil(stockHeight / resolution);
    const totalVoxels = gridWidth * gridHeight;

    // Initialize full material (255)
    const voxels = new Uint8Array(totalVoxels);
    voxels.fill(255);

    // Store original for reset
    const originalVoxels = new Uint8Array(voxels);

    this.stock = {
      bounds: {
        x_min: bounds.x_min - margin,
        x_max: bounds.x_min - margin + stockWidth,
        y_min: bounds.y_min - margin,
        y_max: bounds.y_min - margin + stockHeight,
        z_min: bounds.z_min,
        z_max: bounds.z_max,
      },
      resolution,
      width: gridWidth,
      height: gridHeight,
      thickness,
      voxels,
      originalVoxels,
    };

    return this.stock;
  }

  /**
   * Set tool diameter for removal calculations
   */
  setToolDiameter(diameter: number): void {
    this.toolDiameter = diameter;
  }

  /**
   * Get current stock state
   */
  getStock(): StockMaterial | null {
    return this.stock;
  }

  /**
   * Reset stock to original state
   */
  reset(): void {
    if (this.stock) {
      this.stock.voxels.set(this.stock.originalVoxels);
      this.currentSegmentIndex = -1;
    }
  }

  /**
   * Simulate material removal up to segment index
   */
  simulateToSegment(segments: MoveSegment[], targetIndex: number): void {
    if (!this.stock) return;

    // If going backwards, reset and replay
    if (targetIndex < this.currentSegmentIndex) {
      this.reset();
    }

    // Process segments from current to target
    const startIdx = Math.max(0, this.currentSegmentIndex + 1);
    for (let i = startIdx; i <= targetIndex && i < segments.length; i++) {
      this.removeAlongSegment(segments[i]);
    }

    this.currentSegmentIndex = targetIndex;
  }

  /**
   * Remove material along a single segment
   */
  private removeAlongSegment(segment: MoveSegment): void {
    if (!this.stock) return;

    // Only remove material on cutting moves
    if (segment.type === "rapid") return;

    const { from_pos, to_pos } = segment;
    const [x1, y1, z1] = from_pos;
    const [x2, y2, z2] = to_pos;

    // Skip if above material
    if (z1 > 0 && z2 > 0) return;

    // Interpolate along segment
    const dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
    const steps = Math.max(1, Math.ceil(dist / (this.stock.resolution * 0.5)));

    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const x = x1 + (x2 - x1) * t;
      const y = y1 + (y2 - y1) * t;
      const z = z1 + (z2 - z1) * t;

      this.removeCircle(x, y, z);
    }
  }

  /**
   * Remove material in a circle (tool footprint)
   */
  private removeCircle(cx: number, cy: number, z: number): void {
    if (!this.stock) return;

    const { bounds, resolution, width, height, thickness, voxels } = this.stock;
    const radius = this.toolDiameter / 2;
    const radiusVoxels = Math.ceil(radius / resolution);

    // Calculate depth factor (0-255 based on Z depth)
    const depthFactor = Math.min(255, Math.max(0, Math.round((-z / thickness) * 255)));
    if (depthFactor <= 0) return;

    // Grid position of center
    const gx = Math.round((cx - bounds.x_min) / resolution);
    const gy = Math.round((cy - bounds.y_min) / resolution);

    // Remove voxels in circle
    for (let dy = -radiusVoxels; dy <= radiusVoxels; dy++) {
      for (let dx = -radiusVoxels; dx <= radiusVoxels; dx++) {
        const px = gx + dx;
        const py = gy + dy;

        // Bounds check
        if (px < 0 || px >= width || py < 0 || py >= height) continue;

        // Circle check
        const distSq = dx * dx + dy * dy;
        if (distSq > radiusVoxels * radiusVoxels) continue;

        // Remove material (subtract from current value)
        const idx = py * width + px;
        const current = voxels[idx];
        const newValue = Math.max(0, current - depthFactor);
        voxels[idx] = newValue;
      }
    }
  }

  /**
   * Get removal statistics
   */
  getStats(): RemovalStats {
    if (!this.stock) {
      return { totalVoxels: 0, removedVoxels: 0, percentRemoved: 0, volumeRemoved: 0 };
    }

    const { voxels, originalVoxels, resolution, thickness } = this.stock;
    let totalOriginal = 0;
    let totalCurrent = 0;

    for (let i = 0; i < voxels.length; i++) {
      totalOriginal += originalVoxels[i];
      totalCurrent += voxels[i];
    }

    const removedValue = totalOriginal - totalCurrent;
    const percentRemoved = (removedValue / totalOriginal) * 100;

    // Volume calculation: each voxel is resolution² mm² × (value/255) × thickness
    const voxelArea = resolution * resolution;
    const volumePerFullVoxel = voxelArea * thickness;
    const volumeRemoved = (removedValue / 255) * volumePerFullVoxel;

    return {
      totalVoxels: voxels.length,
      removedVoxels: Math.round(removedValue / 255),
      percentRemoved: Math.round(percentRemoved * 10) / 10,
      volumeRemoved: Math.round(volumeRemoved * 100) / 100,
    };
  }

  /**
   * Render stock to canvas
   */
  renderToCanvas(
    ctx: CanvasRenderingContext2D,
    viewTransform: {
      scale: number;
      offsetX: number;
      offsetY: number;
      canvasWidth: number;
      canvasHeight: number;
    },
    options: {
      showRemoved?: boolean;
      materialColor?: string;
      removedColor?: string;
      opacity?: number;
    } = {}
  ): void {
    if (!this.stock) return;

    const {
      showRemoved = true,
      materialColor = "#8B4513", // SaddleBrown (wood)
      removedColor = "#1a1a2e",  // Dark (air)
      opacity = 0.6,
    } = options;

    const { bounds, resolution, width, height, voxels } = this.stock;

    // Save context
    ctx.save();
    ctx.globalAlpha = opacity;

    // Render each voxel
    const voxelSizePx = resolution * viewTransform.scale;

    // Skip rendering if voxels are too small
    if (voxelSizePx < 0.5) {
      // Render simplified bounding box instead
      const x1 = (bounds.x_min) * viewTransform.scale + viewTransform.offsetX;
      const y1 = viewTransform.canvasHeight - ((bounds.y_max) * viewTransform.scale + viewTransform.offsetY);
      const w = (bounds.x_max - bounds.x_min) * viewTransform.scale;
      const h = (bounds.y_max - bounds.y_min) * viewTransform.scale;

      ctx.fillStyle = materialColor;
      ctx.fillRect(x1, y1, w, h);
      ctx.restore();
      return;
    }

    // Render pixel by pixel (or skip some for performance)
    const step = Math.max(1, Math.floor(2 / voxelSizePx));

    for (let gy = 0; gy < height; gy += step) {
      for (let gx = 0; gx < width; gx += step) {
        const idx = gy * width + gx;
        const value = voxels[idx];

        // Skip fully removed if not showing
        if (value === 0 && !showRemoved) continue;

        // World position
        const wx = bounds.x_min + gx * resolution;
        const wy = bounds.y_min + gy * resolution;

        // Canvas position
        const cx = wx * viewTransform.scale + viewTransform.offsetX;
        const cy = viewTransform.canvasHeight - (wy * viewTransform.scale + viewTransform.offsetY);

        // Color based on material remaining
        if (value > 0) {
          // Blend material color with depth
          const brightness = 0.5 + (value / 255) * 0.5;
          ctx.fillStyle = this.adjustBrightness(materialColor, brightness);
        } else {
          ctx.fillStyle = removedColor;
        }

        ctx.fillRect(cx, cy - voxelSizePx * step, voxelSizePx * step, voxelSizePx * step);
      }
    }

    ctx.restore();
  }

  /**
   * Adjust color brightness
   */
  private adjustBrightness(hex: string, factor: number): string {
    // Parse hex color
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    // Adjust
    const nr = Math.min(255, Math.round(r * factor));
    const ng = Math.min(255, Math.round(g * factor));
    const nb = Math.min(255, Math.round(b * factor));

    return `rgb(${nr}, ${ng}, ${nb})`;
  }
}

// ---------------------------------------------------------------------------
// Export singleton for simple usage
// ---------------------------------------------------------------------------

export const stockSimulator = new StockSimulator();
export default StockSimulator;
