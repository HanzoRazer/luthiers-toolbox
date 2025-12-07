<template>
  <div class="p-4 bg-white">
    <!-- Header -->
    <div class="mb-4">
      <h2 class="text-lg font-semibold text-gray-900">CAM Toolbox</h2>
      <p class="text-sm text-gray-600 mt-1">
        N15-N18 Production CAM Modules - G-code Analysis, Adaptive Strategies, and Polygon Processing
      </p>
    </div>

    <!-- Tool Tabs -->
    <div class="border-b border-gray-200 mb-4">
      <nav class="-mb-px flex space-x-2" aria-label="Tabs">
        <button
          v-for="tool in tools"
          :key="tool.id"
          @click="activeTab = tool.id"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
            activeTab === tool.id
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          ]"
        >
          <span class="mr-1">{{ tool.icon }}</span>
          {{ tool.name }}
          <span
            v-if="tool.badge"
            class="ml-2 px-1.5 py-0.5 text-[10px] font-semibold rounded bg-blue-100 text-blue-700"
          >
            {{ tool.badge }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Tool Content -->
    <div class="mt-4">
      <!-- N15: G-code Backplot -->
      <div v-if="activeTab === 'backplot'" class="space-y-3">
        <div class="border-l-4 border-blue-500 bg-blue-50 p-3 rounded">
          <h3 class="text-sm font-semibold text-blue-900 mb-1">
            📊 N15: G-code Backplot & Analysis
          </h3>
          <p class="text-xs text-blue-700">
            Visualize toolpaths from G-code with SVG preview. Analyzes travel distance, cutting length, 
            and estimated machining time. Supports mm/inch units and custom feed rates.
          </p>
        </div>
        <BackplotGcode />
      </div>

      <!-- N16: Adaptive Benchmark -->
      <div v-if="activeTab === 'benchmark'" class="space-y-3">
        <div class="border-l-4 border-green-500 bg-green-50 p-3 rounded">
          <h3 class="text-sm font-semibold text-green-900 mb-1">
            🔬 N16: Adaptive Kernel Benchmark
          </h3>
          <p class="text-xs text-green-700">
            Compare offset spiral vs trochoid corner strategies for rectangular pockets. 
            Benchmarks toolpath efficiency, move count, and cycle time for adaptive clearing operations.
          </p>
        </div>
        <AdaptiveBench />
      </div>

      <!-- N17+N18: Polygon Processing -->
      <div v-if="activeTab === 'polygon'" class="space-y-3">
        <div class="border-l-4 border-purple-500 bg-purple-50 p-3 rounded">
          <h3 class="text-sm font-semibold text-purple-900 mb-1">
            🔺 N17+N18: Polygon Offset & Spiral
          </h3>
          <p class="text-xs text-purple-700">
            Robust polygon offsetting using pyclipper (N17) with multi-pass preview. 
            Generates continuous spiral toolpaths (N18) with adaptive engagement control and G2/G3 arc linking.
          </p>
        </div>
        <AdaptivePoly />
      </div>

      <!-- Documentation Tab -->
      <div v-if="activeTab === 'docs'" class="space-y-4">
        <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 class="text-base font-semibold text-gray-900 mb-3">
            📚 N15-N18 CAM Modules Documentation
          </h3>

          <!-- N15 Section -->
          <div class="mb-4 pb-4 border-b border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900 mb-2 flex items-center">
              <span class="mr-2">📊</span> N15: G-code Backplot & Time Estimation
            </h4>
            <div class="space-y-2 text-xs text-gray-700">
              <p><strong>Purpose:</strong> Visualize and analyze G-code before sending to machine</p>
              <p><strong>Key Features:</strong></p>
              <ul class="list-disc list-inside ml-4 space-y-1">
                <li>SVG toolpath preview from raw G-code</li>
                <li>Travel vs cutting distance analysis</li>
                <li>Realistic time estimation (rapid/feed/plunge aware)</li>
                <li>Units toggle (mm/inch) with geometry scaling</li>
                <li>Downloadable SVG output</li>
              </ul>
              <p><strong>Use Cases:</strong> Pre-flight verification, time estimates, toolpath validation</p>
              <p><strong>Backend:</strong> <code class="bg-gray-200 px-1 rounded">/api/cam/gcode/plot.svg</code>, <code class="bg-gray-200 px-1 rounded">/api/cam/gcode/estimate</code></p>
            </div>
          </div>

          <!-- N16 Section -->
          <div class="mb-4 pb-4 border-b border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900 mb-2 flex items-center">
              <span class="mr-2">🔬</span> N16: Adaptive Kernel Benchmark
            </h4>
            <div class="space-y-2 text-xs text-gray-700">
              <p><strong>Purpose:</strong> Performance testing of adaptive pocketing strategies</p>
              <p><strong>Key Features:</strong></p>
              <ul class="list-disc list-inside ml-4 space-y-1">
                <li>Offset spiral benchmarking (continuous multi-ring paths)</li>
                <li>Trochoid corner benchmarking (circular milling in tight zones)</li>
                <li>Rectangular pocket test cases (width × height)</li>
                <li>Stepover and corner fillet optimization</li>
                <li>SVG toolpath visualization</li>
              </ul>
              <p><strong>Use Cases:</strong> Strategy comparison, performance profiling, algorithm validation</p>
              <p><strong>Backend:</strong> <code class="bg-gray-200 px-1 rounded">/cam/adaptive2/offset_spiral.svg</code>, <code class="bg-gray-200 px-1 rounded">/cam/adaptive2/trochoid_corners.svg</code></p>
            </div>
          </div>

          <!-- N17 Section -->
          <div class="mb-4 pb-4 border-b border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900 mb-2 flex items-center">
              <span class="mr-2">🔺</span> N17: Polygon Offset (Pyclipper Engine)
            </h4>
            <div class="space-y-2 text-xs text-gray-700">
              <p><strong>Purpose:</strong> Production-grade polygon offsetting for arbitrary shapes</p>
              <p><strong>Key Features:</strong></p>
              <ul class="list-disc list-inside ml-4 space-y-1">
                <li>Robust pyclipper-based offset calculation</li>
                <li>Multi-pass lane strategy (discrete offset rings)</li>
                <li>JSON preview with all offset passes</li>
                <li>Arc or linear linking modes (G2/G3 or pure G1)</li>
                <li>Stepover as percentage of tool diameter</li>
              </ul>
              <p><strong>Use Cases:</strong> Complex pocket clearing, irregular boundaries, preview before machining</p>
              <p><strong>Backend:</strong> <code class="bg-gray-200 px-1 rounded">/cam/polygon_offset.preview</code>, <code class="bg-gray-200 px-1 rounded">/cam/polygon_offset.nc</code></p>
            </div>
          </div>

          <!-- N18 Section -->
          <div class="mb-4">
            <h4 class="text-sm font-semibold text-gray-900 mb-2 flex items-center">
              <span class="mr-2">🌀</span> N18: Adaptive Spiral with Arc Linker
            </h4>
            <div class="space-y-2 text-xs text-gray-700">
              <p><strong>Purpose:</strong> Continuous spiral toolpaths for efficient material removal</p>
              <p><strong>Key Features:</strong></p>
              <ul class="list-disc list-inside ml-4 space-y-1">
                <li>True continuous spiral (no retracts between rings)</li>
                <li>Adaptive engagement control (target_engage parameter)</li>
                <li>Automatic arc insertion at corners (G2/G3 smoothing)</li>
                <li>Stepover in absolute mm distance</li>
                <li>Feed rate and depth control</li>
                <li>Ready-to-run G-code output</li>
              </ul>
              <p><strong>Use Cases:</strong> Production pocketing, fastest cycle times, complex guitar body shapes</p>
              <p><strong>Backend:</strong> <code class="bg-gray-200 px-1 rounded">/cam/adaptive3/offset_spiral.nc</code></p>
            </div>
          </div>

          <!-- Quick Start Guide -->
          <div class="mt-4 pt-4 border-t border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900 mb-2">🚀 Quick Start Workflow</h4>
            <div class="space-y-2 text-xs text-gray-700">
              <p><strong>1. Design Phase:</strong></p>
              <ul class="list-disc list-inside ml-4">
                <li>Create boundary geometry in Rosette Designer or upload DXF</li>
                <li>Use N17 Preview to validate offset rings before machining</li>
              </ul>
              <p><strong>2. Strategy Selection:</strong></p>
              <ul class="list-disc list-inside ml-4">
                <li>Simple shapes → N18 Spiral (fastest)</li>
                <li>Complex shapes with islands → N17 Offset (most robust)</li>
                <li>Need comparison → N16 Benchmark both strategies</li>
              </ul>
              <p><strong>3. Verification:</strong></p>
              <ul class="list-disc list-inside ml-4">
                <li>Generate G-code from N17 or N18</li>
                <li>Load into N15 Backplot for visual verification</li>
                <li>Check time estimates and adjust feeds if needed</li>
              </ul>
              <p><strong>4. Production:</strong></p>
              <ul class="list-disc list-inside ml-4">
                <li>Download G-code (.nc file)</li>
                <li>Post-process if needed (see Multi-Post Export)</li>
                <li>Load into machine controller (GRBL, Mach4, etc.)</li>
              </ul>
            </div>
          </div>

          <!-- Related Systems -->
          <div class="mt-4 pt-4 border-t border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900 mb-2">🔗 Related Systems</h4>
            <div class="space-y-1 text-xs text-gray-700">
              <p><strong>Module L:</strong> Adaptive Pocketing Engine (island handling, smoothing, trochoids)</p>
              <p><strong>Module M:</strong> Machine Profiles (feed/speed optimization per CNC platform)</p>
              <p><strong>Helical v16.1:</strong> Spiral ramping for hardwood plunge operations</p>
              <p><strong>Pipeline Lab:</strong> Full CAM workflow orchestration with job history</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BackplotGcode from './BackplotGcode.vue'
import AdaptiveBench from './AdaptiveBench.vue'
import AdaptivePoly from './AdaptivePoly.vue'

interface Tool {
  id: string
  name: string
  icon: string
  badge?: string
}

const tools: Tool[] = [
  {
    id: 'backplot',
    name: 'Backplot',
    icon: '📊',
    badge: 'N15'
  },
  {
    id: 'benchmark',
    name: 'Benchmark',
    icon: '🔬',
    badge: 'N16'
  },
  {
    id: 'polygon',
    name: 'Polygon',
    icon: '🔺',
    badge: 'N17+N18'
  },
  {
    id: 'docs',
    name: 'Documentation',
    icon: '📚'
  }
]

const activeTab = ref<string>('backplot')
</script>

<style scoped>
code {
  font-family: 'Courier New', monospace;
  font-size: 11px;
}
</style>
