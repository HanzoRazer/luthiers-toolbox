<script setup lang="ts">
/**
 * ToolpathAudioPanel — P5 Machine Sound Controls
 *
 * Audio settings panel for toolpath playback:
 * - Master volume control
 * - Spindle sound toggle + frequency
 * - Cutting noise toggle + intensity
 * - Rapid sound toggle
 * - Depth modulation toggle
 * - Presets for quick configuration
 */

import { ref, watch, onMounted, onUnmounted } from "vue";
import {
  getAudioEngine,
  AUDIO_PRESETS,
  DEFAULT_AUDIO_SETTINGS,
  type AudioSettings,
} from "@/util/toolpathAudio";

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const emit = defineEmits<{
  (e: "close"): void;
}>();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const audioEngine = getAudioEngine();
const settings = ref<AudioSettings>({ ...DEFAULT_AUDIO_SETTINGS });
const activePreset = ref<string>("realistic");
const isInitialized = ref(false);
const isPlaying = ref(false);

// Test tone state
const isTestPlaying = ref(false);

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  // Load current settings from engine
  settings.value = audioEngine.getSettings();
  isInitialized.value = audioEngine.isInitialized();
  isPlaying.value = audioEngine.isPlaying();
});

onUnmounted(() => {
  // Stop test tone if playing
  if (isTestPlaying.value) {
    stopTestTone();
  }
});

// ---------------------------------------------------------------------------
// Settings Sync
// ---------------------------------------------------------------------------

watch(
  settings,
  (newSettings) => {
    audioEngine.updateSettings(newSettings);
    // Clear preset when manually changing settings
    activePreset.value = "";
  },
  { deep: true }
);

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function initializeAudio(): Promise<void> {
  const success = await audioEngine.initialize();
  isInitialized.value = success;
}

function applyPreset(presetId: string): void {
  activePreset.value = presetId;
  audioEngine.applyPreset(presetId);
  settings.value = audioEngine.getSettings();
}

function resetToDefaults(): void {
  settings.value = { ...DEFAULT_AUDIO_SETTINGS };
  activePreset.value = "realistic";
}

// Test tone
let testInterval: number | null = null;

async function playTestTone(): Promise<void> {
  if (!isInitialized.value) {
    await initializeAudio();
  }

  if (!audioEngine.isInitialized()) return;

  isTestPlaying.value = true;
  audioEngine.start();

  // Simulate a cutting move
  const fakeSegment = {
    type: "cut" as const,
    from_pos: [0, 0, 0] as [number, number, number],
    to_pos: [100, 0, -5] as [number, number, number],
    feed: 1500,
    duration_ms: 4000,
  };

  let progress = 0;
  audioEngine.setBounds(-10, 5, 100, 3000);

  testInterval = window.setInterval(() => {
    progress += 0.02;
    if (progress >= 1) {
      progress = 0;
    }
    audioEngine.updateForSegment(fakeSegment, progress);
  }, 50);
}

function stopTestTone(): void {
  isTestPlaying.value = false;
  if (testInterval) {
    clearInterval(testInterval);
    testInterval = null;
  }
  audioEngine.stop();
}

function toggleTestTone(): void {
  if (isTestPlaying.value) {
    stopTestTone();
  } else {
    playTestTone();
  }
}
</script>

<template>
  <div class="audio-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3>Machine Sounds</h3>
      <button class="close-btn" @click="emit('close')" title="Close">
        &times;
      </button>
    </div>

    <!-- Initialize Warning -->
    <div v-if="!isInitialized" class="init-warning">
      <p>Audio requires user interaction to initialize.</p>
      <button class="init-btn" @click="initializeAudio">
        Enable Audio
      </button>
    </div>

    <!-- Main Controls -->
    <div v-else class="panel-content">
      <!-- Presets -->
      <section class="settings-section">
        <h4>Presets</h4>
        <div class="preset-grid">
          <button
            v-for="preset in AUDIO_PRESETS"
            :key="preset.id"
            class="preset-btn"
            :class="{ active: activePreset === preset.id }"
            :title="preset.description"
            @click="applyPreset(preset.id)"
          >
            {{ preset.name }}
          </button>
        </div>
      </section>

      <!-- Master Volume -->
      <section class="settings-section">
        <h4>Master Volume</h4>
        <div class="slider-row">
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            v-model.number="settings.masterVolume"
          />
          <span class="slider-value">{{ Math.round(settings.masterVolume * 100) }}%</span>
        </div>
      </section>

      <!-- Spindle Sound -->
      <section class="settings-section">
        <h4>Spindle Sound</h4>
        <label class="toggle-row">
          <input type="checkbox" v-model="settings.spindleEnabled" />
          <span>Enabled</span>
        </label>
        <div v-if="settings.spindleEnabled" class="sub-settings">
          <div class="slider-row">
            <span class="slider-label">Frequency</span>
            <input
              type="range"
              min="200"
              max="800"
              step="20"
              v-model.number="settings.spindleFrequency"
            />
            <span class="slider-value">{{ settings.spindleFrequency }}Hz</span>
          </div>
        </div>
      </section>

      <!-- Cutting Sound -->
      <section class="settings-section">
        <h4>Cutting Sound</h4>
        <label class="toggle-row">
          <input type="checkbox" v-model="settings.cuttingEnabled" />
          <span>Enabled</span>
        </label>
        <div v-if="settings.cuttingEnabled" class="sub-settings">
          <div class="slider-row">
            <span class="slider-label">Intensity</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              v-model.number="settings.cuttingIntensity"
            />
            <span class="slider-value">{{ Math.round(settings.cuttingIntensity * 100) }}%</span>
          </div>
        </div>
      </section>

      <!-- Rapid Sound -->
      <section class="settings-section">
        <h4>Rapid Move Sound</h4>
        <label class="toggle-row">
          <input type="checkbox" v-model="settings.rapidEnabled" />
          <span>Enabled</span>
        </label>
      </section>

      <!-- Depth Modulation -->
      <section class="settings-section">
        <h4>Depth Modulation</h4>
        <label class="toggle-row">
          <input type="checkbox" v-model="settings.depthModulation" />
          <span>Modulate volume by Z depth</span>
        </label>
        <p class="setting-hint">
          Deeper cuts sound louder when enabled
        </p>
      </section>

      <!-- Test & Reset -->
      <section class="settings-section actions-section">
        <button
          class="action-btn test-btn"
          :class="{ playing: isTestPlaying }"
          @click="toggleTestTone"
        >
          {{ isTestPlaying ? "Stop Test" : "Test Sound" }}
        </button>
        <button class="action-btn reset-btn" @click="resetToDefaults">
          Reset to Defaults
        </button>
      </section>

      <!-- Info -->
      <section class="info-section">
        <p class="info-text">
          Audio plays automatically during toolpath playback. Sounds simulate
          spindle RPM, cutting intensity, and rapid moves.
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.audio-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background: var(--bg-primary, #1e1e2e);
  border-left: 1px solid var(--border-color, #333);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #333);
  background: #1a1a2a;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #e9a840;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

/* Initialize Warning */
.init-warning {
  padding: 24px 16px;
  text-align: center;
}

.init-warning p {
  margin: 0 0 16px 0;
  color: #aaa;
  font-size: 13px;
}

.init-btn {
  background: #e9a840;
  color: #000;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
}

.init-btn:hover {
  background: #f0b555;
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.settings-section {
  margin-bottom: 20px;
}

.settings-section h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Preset Grid */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.preset-btn {
  background: #2a2a3a;
  border: 1px solid #444;
  color: #ccc;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-btn:hover {
  background: #3a3a4a;
  border-color: #555;
}

.preset-btn.active {
  background: rgba(233, 168, 64, 0.2);
  border-color: #e9a840;
  color: #e9a840;
}

/* Slider Row */
.slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.slider-label {
  font-size: 12px;
  color: #888;
  min-width: 70px;
}

.slider-row input[type="range"] {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  background: #333;
  border-radius: 3px;
  outline: none;
}

.slider-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  background: #e9a840;
  border-radius: 50%;
  cursor: pointer;
}

.slider-row input[type="range"]::-moz-range-thumb {
  width: 14px;
  height: 14px;
  background: #e9a840;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.slider-value {
  font-size: 11px;
  color: #aaa;
  min-width: 50px;
  text-align: right;
  font-family: "JetBrains Mono", monospace;
}

/* Toggle Row */
.toggle-row {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #ccc;
}

.toggle-row input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #e9a840;
}

.sub-settings {
  margin-top: 12px;
  padding-left: 26px;
}

.setting-hint {
  margin: 6px 0 0 26px;
  font-size: 11px;
  color: #666;
}

/* Actions Section */
.actions-section {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #333;
}

.action-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.test-btn {
  background: #3a3a4a;
  border: 1px solid #555;
  color: #ccc;
}

.test-btn:hover {
  background: #4a4a5a;
}

.test-btn.playing {
  background: rgba(233, 168, 64, 0.2);
  border-color: #e9a840;
  color: #e9a840;
}

.reset-btn {
  background: #2a2a3a;
  border: 1px solid #444;
  color: #888;
}

.reset-btn:hover {
  background: #3a3a4a;
  color: #ccc;
}

/* Info Section */
.info-section {
  padding-top: 16px;
  border-top: 1px solid #333;
}

.info-text {
  margin: 0;
  font-size: 11px;
  color: #666;
  line-height: 1.5;
}

/* Scrollbar */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
