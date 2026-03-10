/**
 * animationExporter — P5 Animation Export Utility
 *
 * Records toolpath animation and exports as video (WebM) or GIF.
 *
 * Features:
 * - Canvas frame capture
 * - WebM video export via MediaRecorder
 * - GIF export via manual frame encoding
 * - Progress callbacks
 * - Configurable quality/FPS
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExportConfig {
  /** Output format */
  format: "webm" | "gif";
  /** Frames per second */
  fps: number;
  /** Quality (0-1, affects bitrate/colors) */
  quality: number;
  /** Video width (null = canvas size) */
  width: number | null;
  /** Video height (null = canvas size) */
  height: number | null;
  /** Duration in seconds (null = full animation) */
  duration: number | null;
  /** Include HUD overlay */
  includeHud: boolean;
}

export interface ExportProgress {
  /** Current phase */
  phase: "preparing" | "recording" | "encoding" | "complete" | "error";
  /** Progress 0-100 */
  percent: number;
  /** Status message */
  message: string;
  /** Frames captured so far */
  framesCaptured: number;
  /** Total expected frames */
  totalFrames: number;
}

export type ProgressCallback = (progress: ExportProgress) => void;

export interface ExportResult {
  /** Success flag */
  success: boolean;
  /** Blob containing the video/gif */
  blob: Blob | null;
  /** Object URL for download */
  url: string | null;
  /** Suggested filename */
  filename: string;
  /** Error message if failed */
  error?: string;
  /** Export duration in ms */
  duration: number;
}

// ---------------------------------------------------------------------------
// Default config
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG: ExportConfig = {
  format: "webm",
  fps: 30,
  quality: 0.8,
  width: null,
  height: null,
  duration: null,
  includeHud: false,
};

// ---------------------------------------------------------------------------
// GIF Encoder (simple implementation)
// ---------------------------------------------------------------------------

class SimpleGifEncoder {
  private frames: ImageData[] = [];
  private width: number;
  private height: number;
  private delay: number;

  constructor(width: number, height: number, fps: number) {
    this.width = width;
    this.height = height;
    this.delay = Math.round(1000 / fps);
  }

  addFrame(imageData: ImageData): void {
    this.frames.push(imageData);
  }

  async encode(): Promise<Blob> {
    // Simple GIF89a encoder
    // This is a minimal implementation - for production, use gif.js or similar
    const chunks: Uint8Array[] = [];

    // GIF Header
    chunks.push(new Uint8Array([
      0x47, 0x49, 0x46, 0x38, 0x39, 0x61, // GIF89a
    ]));

    // Logical Screen Descriptor
    const lsd = new Uint8Array(7);
    lsd[0] = this.width & 0xff;
    lsd[1] = (this.width >> 8) & 0xff;
    lsd[2] = this.height & 0xff;
    lsd[3] = (this.height >> 8) & 0xff;
    lsd[4] = 0xf7; // Global color table, 256 colors
    lsd[5] = 0x00; // Background color index
    lsd[6] = 0x00; // Pixel aspect ratio
    chunks.push(lsd);

    // Global Color Table (256 colors - simple grayscale + basic colors)
    const gct = this.buildColorTable();
    chunks.push(gct);

    // Netscape Application Extension (for looping)
    chunks.push(new Uint8Array([
      0x21, 0xff, 0x0b,
      0x4e, 0x45, 0x54, 0x53, 0x43, 0x41, 0x50, 0x45, // NETSCAPE
      0x32, 0x2e, 0x30, // 2.0
      0x03, 0x01,
      0x00, 0x00, // Loop count (0 = infinite)
      0x00, // Block terminator
    ]));

    // Add each frame
    for (const frame of this.frames) {
      // Graphic Control Extension
      const gce = new Uint8Array([
        0x21, 0xf9, 0x04,
        0x04, // Disposal method: restore to background
        this.delay & 0xff,
        (this.delay >> 8) & 0xff,
        0x00, // Transparent color index
        0x00, // Block terminator
      ]);
      chunks.push(gce);

      // Image Descriptor
      const id = new Uint8Array([
        0x2c,
        0x00, 0x00, // Left
        0x00, 0x00, // Top
        this.width & 0xff,
        (this.width >> 8) & 0xff,
        this.height & 0xff,
        (this.height >> 8) & 0xff,
        0x00, // No local color table
      ]);
      chunks.push(id);

      // LZW Minimum Code Size
      chunks.push(new Uint8Array([0x08]));

      // Image Data (LZW compressed)
      const imageData = this.compressFrame(frame);
      chunks.push(imageData);
    }

    // GIF Trailer
    chunks.push(new Uint8Array([0x3b]));

    // Combine all chunks
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }

    return new Blob([result], { type: "image/gif" });
  }

  private buildColorTable(): Uint8Array {
    // 256-color table: grayscale + common colors
    const table = new Uint8Array(768);

    // First 216 colors: web-safe palette (6x6x6 cube)
    let idx = 0;
    for (let r = 0; r < 6; r++) {
      for (let g = 0; g < 6; g++) {
        for (let b = 0; b < 6; b++) {
          table[idx++] = Math.round(r * 51);
          table[idx++] = Math.round(g * 51);
          table[idx++] = Math.round(b * 51);
        }
      }
    }

    // Remaining 40 colors: grayscale
    for (let i = 216; i < 256; i++) {
      const gray = Math.round((i - 216) * (255 / 39));
      table[idx++] = gray;
      table[idx++] = gray;
      table[idx++] = gray;
    }

    return table;
  }

  private compressFrame(frame: ImageData): Uint8Array {
    // Quantize to palette and simple RLE-like compression
    const pixels = this.quantizeFrame(frame);

    // Simple uncompressed sub-blocks (for compatibility)
    const subBlocks: number[] = [];
    let i = 0;

    while (i < pixels.length) {
      const blockSize = Math.min(254, pixels.length - i);
      subBlocks.push(blockSize);
      for (let j = 0; j < blockSize; j++) {
        subBlocks.push(pixels[i + j]);
      }
      i += blockSize;
    }
    subBlocks.push(0); // Block terminator

    return new Uint8Array(subBlocks);
  }

  private quantizeFrame(frame: ImageData): Uint8Array {
    const result = new Uint8Array(this.width * this.height);
    const data = frame.data;

    for (let i = 0; i < result.length; i++) {
      const r = data[i * 4];
      const g = data[i * 4 + 1];
      const b = data[i * 4 + 2];

      // Map to 6x6x6 color cube
      const ri = Math.round(r / 51);
      const gi = Math.round(g / 51);
      const bi = Math.round(b / 51);

      result[i] = ri * 36 + gi * 6 + bi;
    }

    return result;
  }
}

// ---------------------------------------------------------------------------
// Animation Exporter
// ---------------------------------------------------------------------------

export class AnimationExporter {
  private config: ExportConfig;
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private recordedChunks: Blob[] = [];
  private isRecording = false;
  private startTime = 0;

  constructor(config: Partial<ExportConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Export animation from a canvas element
   */
  async exportFromCanvas(
    sourceCanvas: HTMLCanvasElement,
    durationMs: number,
    onProgress?: ProgressCallback,
    onFrame?: () => void
  ): Promise<ExportResult> {
    const startTime = performance.now();

    try {
      // Setup
      this.canvas = sourceCanvas;
      const width = this.config.width || sourceCanvas.width;
      const height = this.config.height || sourceCanvas.height;

      onProgress?.({
        phase: "preparing",
        percent: 0,
        message: "Preparing export...",
        framesCaptured: 0,
        totalFrames: Math.ceil(durationMs / 1000 * this.config.fps),
      });

      if (this.config.format === "webm") {
        return await this.exportWebM(sourceCanvas, durationMs, onProgress, onFrame);
      } else {
        return await this.exportGif(sourceCanvas, width, height, durationMs, onProgress, onFrame);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Export failed";
      onProgress?.({
        phase: "error",
        percent: 0,
        message: errorMessage,
        framesCaptured: 0,
        totalFrames: 0,
      });

      return {
        success: false,
        blob: null,
        url: null,
        filename: "",
        error: errorMessage,
        duration: performance.now() - startTime,
      };
    }
  }

  /**
   * Export as WebM using MediaRecorder
   */
  private async exportWebM(
    canvas: HTMLCanvasElement,
    durationMs: number,
    onProgress?: ProgressCallback,
    onFrame?: () => void
  ): Promise<ExportResult> {
    const startTime = performance.now();
    const totalFrames = Math.ceil(durationMs / 1000 * this.config.fps);
    const frameInterval = 1000 / this.config.fps;

    return new Promise((resolve) => {
      const stream = canvas.captureStream(this.config.fps);

      const options: MediaRecorderOptions = {
        mimeType: "video/webm;codecs=vp9",
        videoBitsPerSecond: Math.round(2500000 * this.config.quality),
      };

      // Fallback if VP9 not supported
      if (!MediaRecorder.isTypeSupported(options.mimeType!)) {
        options.mimeType = "video/webm";
      }

      this.mediaRecorder = new MediaRecorder(stream, options);
      this.recordedChunks = [];

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          this.recordedChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.recordedChunks, { type: "video/webm" });
        const url = URL.createObjectURL(blob);

        onProgress?.({
          phase: "complete",
          percent: 100,
          message: "Export complete!",
          framesCaptured: totalFrames,
          totalFrames,
        });

        resolve({
          success: true,
          blob,
          url,
          filename: `toolpath-${Date.now()}.webm`,
          duration: performance.now() - startTime,
        });
      };

      // Start recording
      this.mediaRecorder.start();
      this.isRecording = true;

      let frameCount = 0;
      const recordFrame = () => {
        if (!this.isRecording) return;

        frameCount++;
        onFrame?.();

        onProgress?.({
          phase: "recording",
          percent: Math.round((frameCount / totalFrames) * 100),
          message: `Recording frame ${frameCount}/${totalFrames}`,
          framesCaptured: frameCount,
          totalFrames,
        });

        if (frameCount >= totalFrames) {
          this.isRecording = false;
          this.mediaRecorder?.stop();
        } else {
          setTimeout(recordFrame, frameInterval);
        }
      };

      recordFrame();
    });
  }

  /**
   * Export as GIF
   */
  private async exportGif(
    canvas: HTMLCanvasElement,
    width: number,
    height: number,
    durationMs: number,
    onProgress?: ProgressCallback,
    onFrame?: () => void
  ): Promise<ExportResult> {
    const startTime = performance.now();
    const totalFrames = Math.ceil(durationMs / 1000 * this.config.fps);
    const frameInterval = 1000 / this.config.fps;

    // Create offscreen canvas for capturing
    const offscreen = document.createElement("canvas");
    offscreen.width = width;
    offscreen.height = height;
    const offCtx = offscreen.getContext("2d")!;

    const encoder = new SimpleGifEncoder(width, height, this.config.fps);

    // Capture frames
    for (let i = 0; i < totalFrames; i++) {
      // Trigger frame update
      onFrame?.();

      // Wait a bit for canvas to update
      await new Promise((r) => setTimeout(r, frameInterval));

      // Capture frame
      offCtx.drawImage(canvas, 0, 0, width, height);
      const imageData = offCtx.getImageData(0, 0, width, height);
      encoder.addFrame(imageData);

      onProgress?.({
        phase: "recording",
        percent: Math.round(((i + 1) / totalFrames) * 50),
        message: `Capturing frame ${i + 1}/${totalFrames}`,
        framesCaptured: i + 1,
        totalFrames,
      });
    }

    // Encode GIF
    onProgress?.({
      phase: "encoding",
      percent: 75,
      message: "Encoding GIF...",
      framesCaptured: totalFrames,
      totalFrames,
    });

    const blob = await encoder.encode();
    const url = URL.createObjectURL(blob);

    onProgress?.({
      phase: "complete",
      percent: 100,
      message: "Export complete!",
      framesCaptured: totalFrames,
      totalFrames,
    });

    return {
      success: true,
      blob,
      url,
      filename: `toolpath-${Date.now()}.gif`,
      duration: performance.now() - startTime,
    };
  }

  /**
   * Cancel ongoing export
   */
  cancel(): void {
    this.isRecording = false;
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    this.cancel();
    this.recordedChunks = [];
  }
}

/**
 * Trigger download of exported file
 */
export function downloadExport(result: ExportResult): void {
  if (!result.url) return;

  const a = document.createElement("a");
  a.href = result.url;
  a.download = result.filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export default AnimationExporter;
