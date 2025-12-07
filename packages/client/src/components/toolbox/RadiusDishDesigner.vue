<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-bold">Radius Dish Designer</h1>
      <div class="flex items-center gap-2 text-sm">
        <span class="opacity-70">Guides:</span>
        <a class="underline" href="/radius_dish/Acoustic_Guitar_Radius_Explained.pdf" target="_blank" rel="noopener">
          Radius Explained (PDF)
        </a>
        <span>·</span>
        <a class="underline" href="/radius_dish/Router_Trammel_Radius_Dish_Guide.pdf" target="_blank" rel="noopener">
          Router Trammel Guide (PDF)
        </a>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button 
        v-for="t in tabs" 
        :key="t" 
        class="px-3 py-1 rounded border transition-colors"
        :class="tab === t ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-50'" 
        @click="tab = t"
      >
        {{ t }}
      </button>
    </div>

    <!-- Design Tab -->
    <div v-if="tab === 'Design'" class="space-y-4">
      <div class="grid md:grid-cols-2 gap-4">
        <div class="space-y-2">
          <h3 class="font-semibold text-lg">Radius Selection</h3>
          <p class="text-sm opacity-80">
            Choose radius for archtop guitar tops/backs. 15ft (4572mm) is more curved, 25ft (7620mm) is flatter.
          </p>
          
          <div class="space-y-2">
            <label class="flex items-center gap-2">
              <input 
                type="radio" 
                v-model="selectedRadius" 
                value="15ft"
                class="form-radio"
              />
              <span>15 ft (4572 mm) - Traditional Archtop</span>
            </label>
            <label class="flex items-center gap-2">
              <input 
                type="radio" 
                v-model="selectedRadius" 
                value="25ft"
                class="form-radio"
              />
              <span>25 ft (7620 mm) - Shallow Arch</span>
            </label>
          </div>

          <div class="mt-4 p-4 bg-gray-50 rounded">
            <h4 class="font-medium mb-2">Current Selection:</h4>
            <p><strong>Radius:</strong> {{ selectedRadius === '15ft' ? '15 feet (4572 mm)' : '25 feet (7620 mm)' }}</p>
            <p class="text-sm opacity-70 mt-1">
              {{ selectedRadius === '15ft' 
                ? 'Deeper arch - classic carved-top sound with more projection' 
                : 'Shallow arch - balanced tone with easier construction' }}
            </p>
          </div>
        </div>

        <div class="space-y-2">
          <h3 class="font-semibold text-lg">Preview</h3>
          <div class="border rounded p-4 bg-white" style="min-height: 300px;">
            <img 
              :src="`/radius_dish/Radius_Arc_${selectedRadius}.svg`" 
              :alt="`Radius Arc ${selectedRadius}`"
              class="w-full h-auto"
              style="max-height: 400px; object-fit: contain;"
            />
          </div>
        </div>
      </div>

      <div class="flex gap-2 flex-wrap">
        <button 
          @click="downloadDXF" 
          class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          Download DXF for CAM
        </button>
        <button 
          @click="downloadGCode" 
          class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
        >
          Download G-code (GRBL)
        </button>
        <button 
          @click="viewSVG" 
          class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors"
        >
          View SVG in Gallery
        </button>
      </div>
    </div>

    <!-- Calculator Tab -->
    <div v-else-if="tab === 'Calculator'" class="space-y-4">
      <div class="grid md:grid-cols-2 gap-4">
        <div class="space-y-4">
          <h3 class="font-semibold text-lg">Dish Depth Calculator</h3>
          <p class="text-sm opacity-80">
            Calculate the depth of dish for a given width and radius.
          </p>

          <div class="space-y-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Dish Width (inches)</span>
              <input 
                v-model.number="calc.width" 
                type="number" 
                step="0.125"
                class="border p-2 rounded" 
                placeholder="e.g., 16"
              />
            </label>

            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Radius (feet)</span>
              <select v-model.number="calc.radius" class="border p-2 rounded">
                <option :value="15">15 ft (4572 mm)</option>
                <option :value="25">25 ft (7620 mm)</option>
                <option :value="12">12 ft (3658 mm) - Custom</option>
                <option :value="20">20 ft (6096 mm) - Custom</option>
              </select>
            </label>

            <button 
              @click="calculateDepth" 
              class="w-full px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Calculate Depth
            </button>
          </div>
        </div>

        <div class="space-y-2">
          <h3 class="font-semibold text-lg">Results</h3>
          <div v-if="calcResult" class="p-4 bg-gray-50 rounded space-y-2">
            <div>
              <strong>Dish Width:</strong> {{ calcResult.width_in }} inches ({{ calcResult.width_mm }} mm)
            </div>
            <div>
              <strong>Radius:</strong> {{ calcResult.radius_ft }} feet ({{ calcResult.radius_mm }} mm)
            </div>
            <div class="text-lg font-bold text-blue-600">
              <strong>Dish Depth:</strong> {{ calcResult.depth_in }} inches ({{ calcResult.depth_mm }} mm)
            </div>
            <div class="text-sm opacity-70 mt-3">
              <strong>Formula:</strong> depth = R - √(R² - (W/2)²)
              <br/>
              Where R = radius, W = width
            </div>
          </div>
          <div v-else class="p-4 bg-gray-50 rounded text-sm opacity-70">
            Enter values and click Calculate to see results.
          </div>
        </div>
      </div>
    </div>

    <!-- CNC Setup Tab -->
    <div v-else-if="tab === 'CNC Setup'" class="space-y-4">
      <h3 class="font-semibold text-lg">CNC Machining Instructions</h3>
      
      <div class="space-y-3">
        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">1. Material Setup</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Mount blank securely to spoilboard with screws or T-track clamps</li>
            <li>Ensure material is flat and level</li>
            <li>Set Z-zero to top surface of workpiece</li>
          </ul>
        </div>

        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">2. Tool Selection</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Bit: 1/2" or 3/4" ball nose router bit</li>
            <li>Speed: 12,000-18,000 RPM (depending on material)</li>
            <li>Feed Rate: 60-100 inches/min for softwoods, 40-60 for hardwoods</li>
            <li>DOC (Depth of Cut): 0.060" to 0.125" per pass</li>
          </ul>
        </div>

        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">3. G-code Configuration</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Machine: GRBL-compatible (Arduino-based CNC)</li>
            <li>Units: Inches (G20)</li>
            <li>Work Coordinate System: G54</li>
            <li>Included files: Pre-generated toolpaths for 15ft and 25ft radius</li>
          </ul>
        </div>

        <div class="p-4 border rounded bg-yellow-50">
          <h4 class="font-medium mb-2">⚠️ Safety Notes</h4>
          <ul class="list-disc list-inside text-sm space-y-1">
            <li>Always run air cuts first (Z above workpiece) to verify toolpath</li>
            <li>Use dust collection - routing generates significant dust</li>
            <li>Secure material properly - it will vibrate during routing</li>
            <li>Check bit sharpness - dull bits cause tearout in figured wood</li>
          </ul>
        </div>
      </div>

      <div class="mt-4">
        <button 
          @click="downloadGCode" 
          class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
        >
          Download G-code ({{ selectedRadius }})
        </button>
      </div>
    </div>

    <!-- Docs Tab -->
    <div v-else-if="tab === 'Docs'" class="space-y-4">
      <h3 class="font-semibold text-lg">Documentation & Theory</h3>
      
      <div class="grid md:grid-cols-2 gap-4">
        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">📄 Acoustic Guitar Radius Explained</h4>
          <p class="text-sm opacity-80 mb-3">
            Comprehensive guide to radius arches in acoustic guitar construction. 
            Covers theory, measurements, and acoustic impact.
          </p>
          <a 
            href="/radius_dish/Acoustic_Guitar_Radius_Explained.pdf" 
            target="_blank" 
            class="text-blue-600 underline text-sm"
          >
            Open PDF →
          </a>
        </div>

        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">🛠️ Router Trammel Guide</h4>
          <p class="text-sm opacity-80 mb-3">
            Step-by-step instructions for building and using a router trammel 
            to create radius dishes by hand (alternative to CNC).
          </p>
          <a 
            href="/radius_dish/Router_Trammel_Radius_Dish_Guide.pdf" 
            target="_blank" 
            class="text-blue-600 underline text-sm"
          >
            Open PDF →
          </a>
        </div>
      </div>

      <div class="mt-4 p-4 bg-gray-50 rounded">
        <h4 class="font-medium mb-2">Quick Reference</h4>
        <div class="text-sm space-y-2 opacity-80">
          <p><strong>15 ft radius:</strong> Traditional carved archtop guitars (Gibson L-5, Super 400)</p>
          <p><strong>25 ft radius:</strong> Flatter arch, easier for beginners, modern jazz guitars</p>
          <p><strong>Common widths:</strong> 14-17 inches for guitar tops, 15-18 inches for backs</p>
          <p><strong>Typical depth:</strong> 0.5-0.75 inches for 15ft, 0.3-0.5 inches for 25ft</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const tabs = ['Design', 'Calculator', 'CNC Setup', 'Docs']
const tab = ref('Design')

// Design tab
const selectedRadius = ref<'15ft' | '25ft'>('15ft')

function downloadDXF() {
  const url = `/radius_dish/Radius_Arc_${selectedRadius.value}.dxf`
  const link = document.createElement('a')
  link.href = url
  link.download = `Radius_Arc_${selectedRadius.value}.dxf`
  link.click()
}

function downloadGCode() {
  const radiusNum = selectedRadius.value === '15ft' ? '15ft' : '25ft'
  // Check if G-code files exist in Fusion_GRBL_Kit
  const url = `/radius_dish/radius_dish_${radiusNum}_grbl.nc`
  const link = document.createElement('a')
  link.href = url
  link.download = `radius_dish_${radiusNum}_grbl.nc`
  link.click()
}

function viewSVG() {
  window.open(`/radius_dish/Radius_Arc_${selectedRadius.value}.svg`, '_blank')
}

// Calculator tab
const calc = ref({
  width: 16,
  radius: 15
})

const calcResult = ref<{
  width_in: string;
  width_mm: string;
  radius_ft: number;
  radius_mm: string;
  depth_in: string;
  depth_mm: string;
} | null>(null)

function calculateDepth() {
  const width_in = calc.value.width
  const radius_ft = calc.value.radius
  
  // Convert to same units (inches)
  const radius_in = radius_ft * 12
  const half_width = width_in / 2
  
  // Calculate depth using circular segment formula
  // depth = R - sqrt(R^2 - (W/2)^2)
  const depth_in = radius_in - Math.sqrt(Math.pow(radius_in, 2) - Math.pow(half_width, 2))
  
  // Convert to mm
  const width_mm = width_in * 25.4
  const radius_mm = radius_ft * 304.8
  const depth_mm = depth_in * 25.4
  
  calcResult.value = {
    width_in: width_in.toFixed(3),
    width_mm: width_mm.toFixed(1),
    radius_ft: radius_ft,
    radius_mm: radius_mm.toFixed(0),
    depth_in: depth_in.toFixed(4),
    depth_mm: depth_mm.toFixed(2)
  }
}
</script>

<style scoped>
/* Additional component-specific styles */
</style>
