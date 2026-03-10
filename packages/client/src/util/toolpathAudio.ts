/**
 * toolpathAudio — P5 Machine Sound Simulation
 *
 * Web Audio API-based sound synthesis for toolpath playback:
 * - Spindle tone (continuous during operation)
 * - Cutting sound (varies with feed rate and depth)
 * - Rapid move sound (light whir)
 * - Z plunge/retract sounds
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MoveSegment {
  type: "rapid" | "linear" | "cut" | "arc_cw" | "arc_ccw";
  from_pos: [number, number, number];
  to_pos: [number, number, number];
  feed: number;
  duration_ms: number;
}

export interface AudioSettings {
  /** Master volume (0-1) */
  masterVolume: number;
  /** Spindle tone enabled */
  spindleEnabled: boolean;
  /** Spindle base frequency (Hz) - simulates RPM */
  spindleFrequency: number;
  /** Cutting sound enabled */
  cuttingEnabled: boolean;
  /** Cutting noise intensity (0-1) */
  cuttingIntensity: number;
  /** Rapid sound enabled */
  rapidEnabled: boolean;
  /** Depth variation - modulate sound with Z depth */
  depthModulation: boolean;
}

export interface AudioState {
  /** Audio context initialized */
  initialized: boolean;
  /** Currently playing */
  playing: boolean;
  /** Current move type */
  currentMoveType: string | null;
  /** Current feed rate */
  currentFeed: number;
  /** Current Z depth */
  currentZ: number;
}

// ---------------------------------------------------------------------------
// Default Settings
// ---------------------------------------------------------------------------

export const DEFAULT_AUDIO_SETTINGS: AudioSettings = {
  masterVolume: 0.3,
  spindleEnabled: true,
  spindleFrequency: 440, // A4 - represents ~18000 RPM
  cuttingEnabled: true,
  cuttingIntensity: 0.5,
  rapidEnabled: true,
  depthModulation: true,
};

// ---------------------------------------------------------------------------
// Audio Presets
// ---------------------------------------------------------------------------

export interface AudioPreset {
  id: string;
  name: string;
  description: string;
  settings: Partial<AudioSettings>;
}

export const AUDIO_PRESETS: AudioPreset[] = [
  {
    id: "realistic",
    name: "Realistic",
    description: "Balanced spindle and cutting sounds",
    settings: {
      masterVolume: 0.3,
      spindleEnabled: true,
      spindleFrequency: 440,
      cuttingEnabled: true,
      cuttingIntensity: 0.5,
      rapidEnabled: true,
      depthModulation: true,
    },
  },
  {
    id: "spindle-only",
    name: "Spindle Only",
    description: "Just the spindle tone, no cutting noise",
    settings: {
      spindleEnabled: true,
      cuttingEnabled: false,
      rapidEnabled: false,
    },
  },
  {
    id: "aggressive",
    name: "Aggressive",
    description: "Heavy cutting simulation",
    settings: {
      masterVolume: 0.4,
      spindleEnabled: true,
      spindleFrequency: 520,
      cuttingEnabled: true,
      cuttingIntensity: 0.8,
      rapidEnabled: true,
      depthModulation: true,
    },
  },
  {
    id: "subtle",
    name: "Subtle",
    description: "Quiet background audio",
    settings: {
      masterVolume: 0.15,
      spindleEnabled: true,
      spindleFrequency: 380,
      cuttingEnabled: true,
      cuttingIntensity: 0.3,
      rapidEnabled: false,
      depthModulation: false,
    },
  },
  {
    id: "silent",
    name: "Silent",
    description: "No audio",
    settings: {
      masterVolume: 0,
      spindleEnabled: false,
      cuttingEnabled: false,
      rapidEnabled: false,
    },
  },
];

// ---------------------------------------------------------------------------
// Audio Engine Class
// ---------------------------------------------------------------------------

export class ToolpathAudioEngine {
  private audioContext: AudioContext | null = null;
  private masterGain: GainNode | null = null;

  // Spindle oscillator (continuous tone)
  private spindleOsc: OscillatorNode | null = null;
  private spindleGain: GainNode | null = null;

  // Cutting noise (filtered noise)
  private noiseBuffer: AudioBuffer | null = null;
  private noiseSource: AudioBufferSourceNode | null = null;
  private noiseGain: GainNode | null = null;
  private noiseFilter: BiquadFilterNode | null = null;

  // Rapid tone (higher pitch, quieter)
  private rapidOsc: OscillatorNode | null = null;
  private rapidGain: GainNode | null = null;

  // State
  private settings: AudioSettings = { ...DEFAULT_AUDIO_SETTINGS };
  private state: AudioState = {
    initialized: false,
    playing: false,
    currentMoveType: null,
    currentFeed: 0,
    currentZ: 0,
  };

  // Bounds for normalization
  private zMin = 0;
  private zMax = 0;
  private feedMin = 0;
  private feedMax = 3000;

  // ---------------------------------------------------------------------------
  // Initialization
  // ---------------------------------------------------------------------------

  /**
   * Initialize the audio context (must be called after user interaction)
   */
  async initialize(): Promise<boolean> {
    if (this.state.initialized) return true;

    try {
      this.audioContext = new (window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();

      // Create master gain
      this.masterGain = this.audioContext.createGain();
      this.masterGain.gain.value = this.settings.masterVolume;
      this.masterGain.connect(this.audioContext.destination);

      // Create spindle oscillator
      this.spindleOsc = this.audioContext.createOscillator();
      this.spindleOsc.type = "sawtooth";
      this.spindleOsc.frequency.value = this.settings.spindleFrequency;

      this.spindleGain = this.audioContext.createGain();
      this.spindleGain.gain.value = 0;

      this.spindleOsc.connect(this.spindleGain);
      this.spindleGain.connect(this.masterGain);
      this.spindleOsc.start();

      // Create noise buffer for cutting sound
      await this.createNoiseBuffer();

      // Create rapid oscillator
      this.rapidOsc = this.audioContext.createOscillator();
      this.rapidOsc.type = "sine";
      this.rapidOsc.frequency.value = 880; // Higher pitch for rapids

      this.rapidGain = this.audioContext.createGain();
      this.rapidGain.gain.value = 0;

      this.rapidOsc.connect(this.rapidGain);
      this.rapidGain.connect(this.masterGain);
      this.rapidOsc.start();

      this.state.initialized = true;
      return true;
    } catch (err) {
      console.error("Failed to initialize audio:", err);
      return false;
    }
  }

  /**
   * Create white noise buffer for cutting sounds
   */
  private async createNoiseBuffer(): Promise<void> {
    if (!this.audioContext) return;

    const bufferSize = this.audioContext.sampleRate * 2; // 2 seconds
    this.noiseBuffer = this.audioContext.createBuffer(
      1,
      bufferSize,
      this.audioContext.sampleRate
    );

    const output = this.noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      output[i] = Math.random() * 2 - 1;
    }
  }

  /**
   * Start the noise source (looping)
   */
  private startNoiseSource(): void {
    if (!this.audioContext || !this.noiseBuffer || !this.masterGain) return;

    // Create new noise source
    this.noiseSource = this.audioContext.createBufferSource();
    this.noiseSource.buffer = this.noiseBuffer;
    this.noiseSource.loop = true;

    // Create filter for shaping the noise
    this.noiseFilter = this.audioContext.createBiquadFilter();
    this.noiseFilter.type = "bandpass";
    this.noiseFilter.frequency.value = 2000;
    this.noiseFilter.Q.value = 1;

    // Create gain for noise
    this.noiseGain = this.audioContext.createGain();
    this.noiseGain.gain.value = 0;

    this.noiseSource.connect(this.noiseFilter);
    this.noiseFilter.connect(this.noiseGain);
    this.noiseGain.connect(this.masterGain);

    this.noiseSource.start();
  }

  /**
   * Stop the noise source
   */
  private stopNoiseSource(): void {
    if (this.noiseSource) {
      try {
        this.noiseSource.stop();
      } catch {
        // Already stopped
      }
      this.noiseSource.disconnect();
      this.noiseSource = null;
    }
    if (this.noiseGain) {
      this.noiseGain.disconnect();
      this.noiseGain = null;
    }
    if (this.noiseFilter) {
      this.noiseFilter.disconnect();
      this.noiseFilter = null;
    }
  }

  // ---------------------------------------------------------------------------
  // Settings
  // ---------------------------------------------------------------------------

  /**
   * Update audio settings
   */
  updateSettings(newSettings: Partial<AudioSettings>): void {
    this.settings = { ...this.settings, ...newSettings };

    if (this.masterGain) {
      this.masterGain.gain.value = this.settings.masterVolume;
    }

    if (this.spindleOsc) {
      this.spindleOsc.frequency.value = this.settings.spindleFrequency;
    }
  }

  /**
   * Apply a preset
   */
  applyPreset(presetId: string): void {
    const preset = AUDIO_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      this.updateSettings(preset.settings);
    }
  }

  /**
   * Get current settings
   */
  getSettings(): AudioSettings {
    return { ...this.settings };
  }

  /**
   * Set bounds for normalization
   */
  setBounds(zMin: number, zMax: number, feedMin: number, feedMax: number): void {
    this.zMin = zMin;
    this.zMax = zMax;
    this.feedMin = feedMin;
    this.feedMax = Math.max(feedMax, 1);
  }

  // ---------------------------------------------------------------------------
  // Playback Control
  // ---------------------------------------------------------------------------

  /**
   * Start audio playback
   */
  start(): void {
    if (!this.state.initialized) return;

    if (this.audioContext?.state === "suspended") {
      this.audioContext.resume();
    }

    this.startNoiseSource();
    this.state.playing = true;
  }

  /**
   * Stop audio playback
   */
  stop(): void {
    this.state.playing = false;

    // Fade out all sounds
    const now = this.audioContext?.currentTime ?? 0;
    const fadeTime = 0.05;

    if (this.spindleGain) {
      this.spindleGain.gain.linearRampToValueAtTime(0, now + fadeTime);
    }
    if (this.rapidGain) {
      this.rapidGain.gain.linearRampToValueAtTime(0, now + fadeTime);
    }
    if (this.noiseGain) {
      this.noiseGain.gain.linearRampToValueAtTime(0, now + fadeTime);
    }

    // Stop noise source after fade
    setTimeout(() => this.stopNoiseSource(), fadeTime * 1000 + 50);
  }

  /**
   * Pause audio (keep context but mute)
   */
  pause(): void {
    this.stop();
  }

  /**
   * Resume audio
   */
  resume(): void {
    this.start();
  }

  // ---------------------------------------------------------------------------
  // Real-time Updates
  // ---------------------------------------------------------------------------

  /**
   * Update audio based on current segment
   */
  updateForSegment(segment: MoveSegment, progress: number): void {
    if (!this.state.initialized || !this.state.playing) return;
    if (!this.audioContext) return;

    const now = this.audioContext.currentTime;
    const rampTime = 0.02; // 20ms ramp for smooth transitions

    // Calculate current Z (interpolated)
    const currentZ =
      segment.from_pos[2] + (segment.to_pos[2] - segment.from_pos[2]) * progress;

    this.state.currentMoveType = segment.type;
    this.state.currentFeed = segment.feed;
    this.state.currentZ = currentZ;

    // Normalize values
    const zRange = this.zMax - this.zMin || 1;
    const zNorm = (currentZ - this.zMin) / zRange; // 0 = deepest, 1 = shallowest
    const feedNorm = Math.min(1, segment.feed / this.feedMax);

    const isRapid = segment.type === "rapid";
    const isCutting = !isRapid;

    // --- Spindle ---
    if (this.settings.spindleEnabled && this.spindleGain) {
      let spindleVol = 0.15;

      if (isCutting) {
        // Louder spindle during cutting
        spindleVol = 0.2 + feedNorm * 0.15;

        // Depth modulation - deeper = louder
        if (this.settings.depthModulation) {
          spindleVol *= 0.7 + (1 - zNorm) * 0.3;
        }
      } else {
        // Quieter during rapids
        spindleVol = 0.08;
      }

      this.spindleGain.gain.linearRampToValueAtTime(spindleVol, now + rampTime);

      // Modulate frequency slightly based on load
      if (this.spindleOsc && isCutting) {
        const freqMod = 1 - feedNorm * 0.05; // Slight drop under load
        this.spindleOsc.frequency.linearRampToValueAtTime(
          this.settings.spindleFrequency * freqMod,
          now + rampTime
        );
      }
    } else if (this.spindleGain) {
      this.spindleGain.gain.linearRampToValueAtTime(0, now + rampTime);
    }

    // --- Cutting Noise ---
    if (this.settings.cuttingEnabled && this.noiseGain && this.noiseFilter) {
      if (isCutting) {
        // Volume based on feed rate and depth
        let noiseVol = this.settings.cuttingIntensity * feedNorm * 0.3;

        if (this.settings.depthModulation) {
          noiseVol *= 0.5 + (1 - zNorm) * 0.5;
        }

        this.noiseGain.gain.linearRampToValueAtTime(noiseVol, now + rampTime);

        // Filter frequency based on feed rate (higher feed = higher pitch)
        const filterFreq = 1500 + feedNorm * 2500;
        this.noiseFilter.frequency.linearRampToValueAtTime(filterFreq, now + rampTime);
      } else {
        this.noiseGain.gain.linearRampToValueAtTime(0, now + rampTime);
      }
    } else if (this.noiseGain) {
      this.noiseGain.gain.linearRampToValueAtTime(0, now + rampTime);
    }

    // --- Rapid Sound ---
    if (this.settings.rapidEnabled && this.rapidGain) {
      if (isRapid) {
        this.rapidGain.gain.linearRampToValueAtTime(0.05, now + rampTime);
      } else {
        this.rapidGain.gain.linearRampToValueAtTime(0, now + rampTime);
      }
    } else if (this.rapidGain) {
      this.rapidGain.gain.linearRampToValueAtTime(0, now + rampTime);
    }
  }

  /**
   * Trigger a one-shot sound (e.g., for plunge or retract)
   */
  triggerPlungeSound(): void {
    if (!this.state.initialized || !this.audioContext || !this.masterGain) return;

    const osc = this.audioContext.createOscillator();
    osc.type = "sine";
    osc.frequency.value = 300;

    const gain = this.audioContext.createGain();
    const now = this.audioContext.currentTime;

    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);

    osc.frequency.exponentialRampToValueAtTime(150, now + 0.2);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.3);
  }

  /**
   * Trigger retract sound
   */
  triggerRetractSound(): void {
    if (!this.state.initialized || !this.audioContext || !this.masterGain) return;

    const osc = this.audioContext.createOscillator();
    osc.type = "sine";
    osc.frequency.value = 200;

    const gain = this.audioContext.createGain();
    const now = this.audioContext.currentTime;

    gain.gain.setValueAtTime(0.05, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);

    osc.frequency.exponentialRampToValueAtTime(400, now + 0.15);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + 0.2);
  }

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  /**
   * Get current audio state
   */
  getState(): AudioState {
    return { ...this.state };
  }

  /**
   * Check if initialized
   */
  isInitialized(): boolean {
    return this.state.initialized;
  }

  /**
   * Check if playing
   */
  isPlaying(): boolean {
    return this.state.playing;
  }

  // ---------------------------------------------------------------------------
  // Cleanup
  // ---------------------------------------------------------------------------

  /**
   * Destroy audio engine and release resources
   */
  destroy(): void {
    this.stop();

    if (this.spindleOsc) {
      this.spindleOsc.stop();
      this.spindleOsc.disconnect();
    }
    if (this.rapidOsc) {
      this.rapidOsc.stop();
      this.rapidOsc.disconnect();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }

    this.audioContext = null;
    this.masterGain = null;
    this.spindleOsc = null;
    this.spindleGain = null;
    this.rapidOsc = null;
    this.rapidGain = null;
    this.noiseBuffer = null;
    this.state.initialized = false;
  }
}

// ---------------------------------------------------------------------------
// Singleton Instance
// ---------------------------------------------------------------------------

let audioEngineInstance: ToolpathAudioEngine | null = null;

export function getAudioEngine(): ToolpathAudioEngine {
  if (!audioEngineInstance) {
    audioEngineInstance = new ToolpathAudioEngine();
  }
  return audioEngineInstance;
}

export function destroyAudioEngine(): void {
  if (audioEngineInstance) {
    audioEngineInstance.destroy();
    audioEngineInstance = null;
  }
}

export default {
  ToolpathAudioEngine,
  getAudioEngine,
  destroyAudioEngine,
  AUDIO_PRESETS,
  DEFAULT_AUDIO_SETTINGS,
};
