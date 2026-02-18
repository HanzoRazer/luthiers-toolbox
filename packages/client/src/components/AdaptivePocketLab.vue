<template>
  <div class="p-3 space-y-3 border rounded">
    <h3 class="text-lg font-semibold">
      Adaptive Pocket Lab
    </h3>

    <div class="grid md:grid-cols-3 gap-3">
      <div class="space-y-2">
        <label class="block text-sm font-medium">Tool Ø (mm)</label>
        <input
          v-model.number="toolD"
          type="number"
          step="0.1"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Step-over (%)</label>
        <input
          v-model.number="stepoverPct"
          type="number"
          step="1"
          min="5"
          max="95"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Step-down (mm)</label>
        <input
          v-model.number="stepdown"
          type="number"
          step="0.1"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Margin (mm)</label>
        <input
          v-model.number="margin"
          type="number"
          step="0.1"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Strategy</label>
        <select
          v-model="strategy"
          class="border px-2 py-1 rounded w-full"
        >
          <option>Spiral</option>
          <option>Lanes</option>
        </select>
        
        <label class="block text-sm font-medium">Corner Radius Min (mm) <span class="text-xs text-gray-500">L.2</span></label>
        <input
          v-model.number="cornerRadiusMin"
          type="number"
          step="0.1"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Slowdown Feed (%) <span class="text-xs text-gray-500">L.2</span></label>
        <input
          v-model.number="slowdownFeedPct"
          type="number"
          step="5"
          min="30"
          max="100"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="flex items-center gap-2 text-sm">
          <input
            v-model="climb"
            type="checkbox"
          >
          <span>Climb milling</span>
        </label>
        
        <label class="block text-sm font-medium">Feed XY (mm/min)</label>
        <input
          v-model.number="feedXY"
          type="number"
          step="100"
          class="border px-2 py-1 rounded w-full"
        >
        
        <label class="block text-sm font-medium">Units</label>
        <select
          v-model="units"
          class="border px-2 py-1 rounded w-full"
        >
          <option value="mm">
            mm (G21)
          </option>
          <option value="inch">
            inch (G20)
          </option>
        </select>
        
        <!-- M.1 Machine Selector (extracted component) -->
        <MachineSelector
          v-model="machineId"
          :machines="machines"
          :disabled="false"
          @edit="openMachineEditor"
          @compare="compareMachinesFunc"
        />
        
        <!-- Post-Processor & Adaptive Feed (extracted component) -->
        <PostProcessorConfig
          v-model:post-id="postId"
          v-model:af-mode="afMode"
          v-model:af-inline-min-f="afInlineMinF"
          v-model:af-m-start="afMStart"
          v-model:af-m-end="afMEnd"
          :posts="posts"
          :disabled="false"
          @save-preset="savePresetForPost(postId)"
          @load-preset="loadPresetForPost(postId)"
          @reset-preset="resetPresetForPost(postId)"
        />
        
        <div class="flex gap-2 pt-2 flex-wrap">
          <button
            class="px-3 py-1 border rounded bg-blue-50"
            @click="plan"
          >
            Plan
          </button>
          <button
            class="px-3 py-1 border rounded bg-purple-50"
            :disabled="!moves.length"
            @click="previewNc"
          >
            Preview NC
          </button>
          <button
            class="px-3 py-1 border rounded"
            :disabled="!moves.length"
            aria-label="Open compare modes"
            @click="openCompare"
          >
            Compare modes
          </button>
          <CompareModeButton
            v-if="moves.length"
            :baseline-id="jobName || 'baseline'"
            :candidate-id="'candidate'"
            class="ml-2"
            aria-label="Go to Compare Lab"
          >
            Compare in Lab
          </CompareModeButton>
          <button
            class="px-3 py-1 border rounded bg-green-50"
            :disabled="!moves.length"
            aria-label="Export G-code"
            @click="exportProgram"
          >
            Export G-code
          </button>
        </div>
        
        <div class="space-y-2 pt-2 border-t">
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium">Job name:</label>
            <input
              v-model="jobName" 
              placeholder="e.g., LP_top_pocket_R3" 
              class="border px-2 py-1 rounded w-56 text-sm"
            >
            <span class="text-xs text-gray-500">(optional filename stem)</span>
          </div>
          
          <div class="flex items-center gap-3 flex-wrap">
            <div class="flex items-center gap-2">
              <label class="text-sm font-medium">Export modes:</label>
              <label class="text-xs flex items-center gap-1">
                <input
                  v-model="exportModes.comment"
                  type="checkbox"
                  class="w-3 h-3"
                >
                comment
              </label>
              <label class="text-xs flex items-center gap-1">
                <input
                  v-model="exportModes.inline_f"
                  type="checkbox"
                  class="w-3 h-3"
                >
                inline_f
              </label>
              <label class="text-xs flex items-center gap-1">
                <input
                  v-model="exportModes.mcode"
                  type="checkbox"
                  class="w-3 h-3"
                >
                mcode
              </label>
            </div>
            <button
              class="px-3 py-1 border rounded bg-orange-50"
              :disabled="!moves.length"
              @click="batchExport"
            >
              Batch Export (subset ZIP)
            </button>
          </div>
        </div>
        
        <!-- HUD Overlays (extracted component) -->
        <HudOverlayControls
          v-model:show-tight="showTight"
          v-model:show-slow="showSlow"
          v-model:show-fillets="showFillets"
          :disabled="false"
        />
        
        <!-- Trochoid Settings (extracted component) -->
        <TrochoidSettings
          v-model:use-trochoids="useTrochoids"
          v-model:trochoid-radius="trochoidRadius"
          v-model:trochoid-pitch="trochoidPitch"
          :disabled="false"
        />
        
        <!-- Jerk-Aware Settings (extracted component) -->
        <JerkAwareSettings
          v-model:jerk-aware="jerkAware"
          v-model:machine-accel="machineAccel"
          v-model:machine-jerk="machineJerk"
          v-model:corner-tol="cornerTol"
          :disabled="false"
        />
        
        <!-- M.2: Optimize for Machine -->
        <div class="mt-4 border rounded-xl p-3 bg-gradient-to-br from-blue-50 to-indigo-50">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sm">
              Optimize for Machine
            </h3>
            <div class="flex gap-2">
              <button
                class="px-3 py-1 text-sm border rounded bg-white hover:bg-gray-50 disabled:opacity-50" 
                :disabled="!moves.length || !machineId" 
                @click="runWhatIf"
              >
                Run What-If
              </button>
              <button
                class="px-3 py-1 text-sm border rounded bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50" 
                :disabled="!optOut" 
                @click="openCompareSettings"
              >
                Compare Settings
              </button>
            </div>
          </div>
          
          <div class="grid grid-cols-3 gap-3 text-xs">
            <div>
              <label class="block mb-1">Feed (mm/min)</label>
              <div class="flex gap-1">
                <input
                  v-model.number="optFeedLo"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
                <input
                  v-model.number="optFeedHi"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
              </div>
            </div>
            <div>
              <label class="block mb-1">Stepover (0..1)</label>
              <div class="flex gap-1">
                <input
                  v-model.number="optStpLo"
                  type="number"
                  step="0.01"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
                <input
                  v-model.number="optStpHi"
                  type="number"
                  step="0.01"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
              </div>
            </div>
            <div>
              <label class="block mb-1">RPM</label>
              <div class="flex gap-1">
                <input
                  v-model.number="optRpmLo"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
                <input
                  v-model.number="optRpmHi"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
              </div>
            </div>
            <div>
              <label class="block mb-1">Flutes</label>
              <input
                v-model.number="optFlutes"
                type="number"
                class="border px-1 py-1 rounded w-full text-xs"
              >
            </div>
            <div>
              <label class="block mb-1">Chipload (mm)</label>
              <input
                v-model.number="optChip"
                type="number"
                step="0.005"
                class="border px-1 py-1 rounded w-full text-xs"
              >
            </div>
            <div>
              <label class="block mb-1">Grid (F×S)</label>
              <div class="flex gap-1">
                <input
                  v-model.number="optGridF"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
                <input
                  v-model.number="optGridS"
                  type="number"
                  class="border px-1 py-1 rounded w-full text-xs"
                >
              </div>
            </div>
          </div>
          
          <!-- M.3 Chipload enforcement controls -->
          <div class="flex items-center gap-3 mt-2 text-xs">
            <label class="flex items-center gap-1">
              <input
                v-model="enforceChip"
                type="checkbox"
              >
              <span>Enforce chipload</span>
            </label>
            <label class="flex items-center gap-1">
              <span>Tolerance (mm/tooth)</span>
              <input
                v-model.number="chipTol"
                type="number"
                step="0.005"
                class="border px-2 py-1 rounded w-20"
                :disabled="!enforceChip"
              >
            </label>
          </div>

          <div
            v-if="optOut"
            class="mt-3 grid md:grid-cols-3 gap-2 text-xs"
          >
            <div class="border rounded p-2 bg-white">
              <div class="font-medium mb-1">
                Baseline
              </div>
              <div><b>Time:</b> {{ optOut.baseline.time_s }} s</div>
              <div class="text-gray-600">
                Passes: {{ optOut.baseline.passes }}
              </div>
              <div class="text-gray-600">
                Hops: {{ optOut.baseline.hop_count }}
              </div>
            </div>
            <div class="border rounded p-2 bg-white">
              <div class="font-medium mb-1">
                Recommended
              </div>
              <ul class="space-y-0.5">
                <li><b>Feed:</b> {{ optOut.opt.best.feed_mm_min }} mm/min</li>
                <li><b>Stepover:</b> {{ (optOut.opt.best.stepover*100).toFixed(1) }}%</li>
                <li><b>RPM:</b> {{ optOut.opt.best.rpm }}</li>
                <li><b>Time:</b> {{ optOut.opt.best.time_s }} s</li>
              </ul>
              <button
                class="mt-2 px-2 py-1 border rounded text-xs bg-blue-600 text-white hover:bg-blue-700" 
                @click="applyRecommendation"
              >
                Apply to Job
              </button>
            </div>
            <div class="border rounded p-2 bg-white">
              <div class="font-medium mb-1">
                Sensitivity (near best)
              </div>
              <table class="w-full mt-1">
                <thead>
                  <tr>
                    <th class="text-left">
                      Feed
                    </th><th class="text-left">
                      Stp%
                    </th><th class="text-left">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="n in optOut.opt.neighbors.slice(0,4)"
                    :key="n.feed_mm_min+'-'+n.stepover"
                    class="text-xs"
                  >
                    <td>{{ n.feed_mm_min }}</td>
                    <td>{{ (n.stepover*100).toFixed(0) }}</td>
                    <td>{{ n.time_s }}s</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- M.3: Energy & Heat -->
        <div class="mt-4 border rounded-xl p-3">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sm">
              Energy & Heat
            </h3>
            <div class="flex items-center gap-2">
              <select
                v-model="materialId"
                class="border px-2 py-1 rounded text-xs"
              >
                <option value="maple_hard">
                  Maple (hard)
                </option>
                <option value="mahogany">
                  Mahogany
                </option>
                <option value="al_6061">
                  Al 6061
                </option>
                <option value="custom">
                  Custom
                </option>
              </select>
              <button
                class="px-3 py-1 border rounded text-xs bg-emerald-600 text-white hover:bg-emerald-700" 
                :disabled="!moves.length" 
                @click="runEnergy"
              >
                Compute
              </button>
              <button
                class="px-3 py-1 border rounded text-xs bg-white hover:bg-gray-50" 
                :disabled="!energyOut" 
                @click="exportEnergyCsv"
              >
                Export CSV
              </button>
            </div>
          </div>

          <div
            v-if="energyOut"
            class="mt-3 grid md:grid-cols-3 gap-3"
          >
            <!-- Totals Card -->
            <div class="border rounded p-2 text-sm bg-white">
              <div class="font-medium mb-2">
                Totals
              </div>
              <div>Volume: <b>{{ energyOut.totals.volume_mm3.toFixed(0) }} mm³</b></div>
              <div>Energy: <b>{{ energyOut.totals.energy_j.toFixed(1) }} J</b></div>
              <div class="mt-2 text-xs text-gray-600">
                <div>Heat (J):</div>
                <div>• chip {{ energyOut.totals.heat.chip_j.toFixed(1) }}</div>
                <div>• tool {{ energyOut.totals.heat.tool_j.toFixed(1) }}</div>
                <div>• work {{ energyOut.totals.heat.work_j.toFixed(1) }}</div>
              </div>
            </div>

            <!-- Heat Partition Bar -->
            <div class="border rounded p-2 bg-white">
              <div class="text-sm font-medium mb-2">
                Heat Partition
              </div>
              <div class="w-full h-5 bg-slate-100 rounded overflow-hidden flex">
                <div
                  :style="{width: chipPct+'%'}"
                  class="bg-amber-400"
                  :title="`Chip: ${chipPct.toFixed(1)}%`"
                />
                <div
                  :style="{width: toolPct+'%'}"
                  class="bg-rose-400"
                  :title="`Tool: ${toolPct.toFixed(1)}%`"
                />
                <div
                  :style="{width: workPct+'%'}"
                  class="bg-emerald-400"
                  :title="`Work: ${workPct.toFixed(1)}%`"
                />
              </div>
              <div class="text-xs mt-2 flex gap-3">
                <span class="inline-flex items-center gap-1">
                  <i class="w-3 h-3 bg-amber-400 inline-block rounded" />
                  chip {{ chipPct.toFixed(0) }}%
                </span>
                <span class="inline-flex items-center gap-1">
                  <i class="w-3 h-3 bg-rose-400 inline-block rounded" />
                  tool {{ toolPct.toFixed(0) }}%
                </span>
                <span class="inline-flex items-center gap-1">
                  <i class="w-3 h-3 bg-emerald-400 inline-block rounded" />
                  work {{ workPct.toFixed(0) }}%
                </span>
              </div>
            </div>

            <!-- Cumulative Energy Chart -->
            <div class="border rounded p-2 bg-white">
              <div class="text-sm font-medium mb-2">
                Cumulative Energy
              </div>
              <svg
                viewBox="0 0 300 120"
                class="w-full h-28"
              >
                <polyline
                  :points="energyPolyline"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- M.3 Heat over Time Card -->
      <div class="border rounded-lg p-4 bg-white shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold">
            Heat over Time
          </h2>
          <div class="space-y-2">
            <div class="flex gap-2">
              <button
                class="px-3 py-1 rounded bg-purple-600 text-white text-sm hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!planOut?.moves || !materialId || !profileId"
                @click="runHeatTS"
              >
                Compute
              </button>
              <button
                class="px-3 py-1 rounded border border-purple-600 text-purple-600 text-sm hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!planOut?.moves"
                title="Export Thermal Report (Markdown)"
                @click="exportThermalReport"
              >
                Export Report (MD)
              </button>
            </div>
            <label class="text-xs flex items-center gap-2">
              <input
                v-model="includeCsvLinks"
                type="checkbox"
              >
              Include CSV download links in report
            </label>
            <div class="flex gap-2">
              <button
                class="px-3 py-1 rounded border border-blue-600 text-blue-600 text-sm hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!planOut?.moves"
                title="Export Thermal Bundle (MD + moves.json ZIP)"
                @click="exportThermalBundle"
              >
                Export Bundle (ZIP)
              </button>
              <button
                class="px-3 py-1 rounded border border-green-600 text-green-600 text-sm hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!planOut?.moves"
                title="Log this plan to database"
                @click="logCurrentRun()"
              >
                Log Plan
              </button>
              <button
                class="px-3 py-1 rounded border border-orange-600 text-orange-600 text-sm hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!profileId"
                title="Train feed overrides from logged runs"
                @click="trainOverrides"
              >
                Train Overrides
              </button>
            </div>
            <label class="text-xs flex items-center gap-2">
              <input
                v-model="adoptOverrides"
                type="checkbox"
              >
              Adopt learned feed overrides
            </label>
            
            <!-- Live Learn Controls -->
            <div class="mt-3 pt-3 border-t border-gray-200 space-y-2">
              <div class="flex items-center gap-3">
                <label class="text-xs flex items-center gap-2">
                  <input 
                    v-model="liveLearnApplied" 
                    type="checkbox" 
                    :disabled="!sessionOverrideFactor"
                    title="Apply session-only feed override from measured runtime"
                  >
                  Live learn (session only)
                </label>
                <span 
                  v-if="sessionOverrideFactor" 
                  class="text-xs px-2 py-0.5 border rounded bg-amber-50 text-amber-900 font-mono"
                  title="Session feed scale factor (actual/estimated time)"
                >
                  ×{{ sessionOverrideFactor.toFixed(3) }}
                </span>
                <button
                  v-if="sessionOverrideFactor"
                  class="text-xs px-2 py-0.5 rounded border border-gray-400 text-gray-600 hover:bg-gray-50"
                  title="Reset session override"
                  @click="() => { liveLearnApplied = false; sessionOverrideFactor = null; measuredSeconds = null }"
                >
                  Reset
                </button>
              </div>
              <div class="flex items-center gap-2">
                <input 
                  v-model.number="measuredSeconds" 
                  type="number" 
                  step="0.1" 
                  placeholder="Actual sec"
                  class="px-2 py-1 border rounded text-xs w-28"
                  title="Enter measured runtime in seconds"
                >
                <button
                  class="px-3 py-1 rounded border border-amber-600 text-amber-600 text-xs hover:bg-amber-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="!planOut?.moves || !measuredSeconds"
                  title="Log plan with measured runtime (computes session override)"
                  @click="logCurrentRun(measuredSeconds ?? undefined)"
                >
                  Log with actual time
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div
          v-if="heatTS"
          class="space-y-3"
        >
          <!-- Summary -->
          <div class="grid grid-cols-3 gap-3 text-sm p-2 bg-purple-50 rounded">
            <div>
              <div class="text-xs text-gray-600">
                Total Time
              </div>
              <div class="font-medium">
                {{ heatTS.total_s?.toFixed(1) || 0 }} s
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-600">
                Peak Chip Power
              </div>
              <div class="font-medium">
                {{ Math.max(...(heatTS.p_chip || [0])).toFixed(1) }} W
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-600">
                Peak Tool Power
              </div>
              <div class="font-medium">
                {{ Math.max(...(heatTS.p_tool || [0])).toFixed(1) }} W
              </div>
            </div>
          </div>

          <!-- Power Chart -->
          <div class="border rounded p-2 bg-white">
            <div class="text-sm font-medium mb-2">
              Power over Time
            </div>
            <svg
              viewBox="0 0 300 120"
              class="w-full h-32"
            >
              <polyline
                :points="tsPolyline('p_chip')"
                fill="none"
                stroke="#f59e0b"
                stroke-width="2"
                opacity="0.9"
              />
              <polyline
                :points="tsPolyline('p_tool')"
                fill="none"
                stroke="#ef4444"
                stroke-width="2"
                opacity="0.9"
              />
              <polyline
                :points="tsPolyline('p_work')"
                fill="none"
                stroke="#14b8a6"
                stroke-width="2"
                opacity="0.9"
              />
            </svg>
            <div class="text-xs mt-2 flex items-center gap-3">
              <span class="flex items-center gap-1">
                <i
                  class="inline-block w-3 h-3 rounded"
                  style="background:#f59e0b"
                />
                Chip heat
              </span>
              <span class="flex items-center gap-1">
                <i
                  class="inline-block w-3 h-3 rounded"
                  style="background:#ef4444"
                />
                Tool heat
              </span>
              <span class="flex items-center gap-1">
                <i
                  class="inline-block w-3 h-3 rounded"
                  style="background:#14b8a6"
                />
                Work heat
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="md:col-span-2">
        <!-- M.1.1 Bottleneck Map Toggle -->
        <div class="flex items-center gap-4 mb-2">
          <label class="text-sm flex items-center gap-2">
            <input
              v-model="showBottleneckMap"
              type="checkbox"
            > Bottleneck Map
          </label>
          <div
            v-if="showBottleneckMap"
            class="text-xs text-gray-600 flex items-center gap-3"
          >
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#f59e0b"
              />
              feed cap
            </span>
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#14b8a6"
              />
              accel
            </span>
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#ec4899"
              />
              jerk
            </span>
          </div>
          
          <!-- M.3 Export Bottleneck CSV -->
          <button
            v-if="showBottleneckMap && planOut?.moves"
            class="ml-auto px-3 py-1 rounded bg-slate-600 text-white text-xs hover:bg-slate-700"
            @click="exportBottleneckCsv"
          >
            Export CSV
          </button>
          
          <!-- M.3 Bottleneck Pie Chart -->
          <div
            v-if="showBottleneckMap && planOut?.stats?.caps"
            class="ml-auto border rounded p-2 bg-white"
          >
            <div class="text-sm font-medium mb-1">
              Bottleneck Share
            </div>
            <svg
              viewBox="0 0 120 120"
              class="w-28 h-28 mx-auto"
            >
              <g transform="translate(60,60)">
                <template
                  v-for="(s, i) in capsPie"
                  :key="i"
                >
                  <path
                    :d="arcPath(i)"
                    :fill="s.color"
                    :title="s.label + ': ' + Math.round(s.pct*100) + '%'"
                  />
                </template>
                <circle
                  cx="0"
                  cy="0"
                  r="26"
                  fill="#fff"
                />
              </g>
            </svg>
            <div class="text-xs mt-2 grid grid-cols-2 gap-1">
              <div
                v-for="s in capsPie"
                :key="s.label"
                class="flex items-center gap-1"
              >
                <i
                  class="inline-block w-3 h-3 rounded"
                  :style="{background: s.color}"
                />
                <span>{{ s.label }} {{ Math.round(s.pct*100) }}%</span>
              </div>
            </div>
          </div>
        </div>
        
        <canvas
          ref="cv"
          class="w-full h-[420px] border rounded bg-gray-50"
        />
        <div
          v-if="stats"
          class="text-sm mt-2 p-2 bg-slate-100 rounded"
        >
          <div class="grid grid-cols-2 gap-2">
            <div><b>Length:</b> {{ stats.length_mm }} mm</div>
            <div><b>Area:</b> {{ stats.area_mm2 }} mm²</div>
            <div><b>Time (Classic):</b> {{ stats.time_s_classic }} s ({{ (stats.time_s_classic/60).toFixed(1) }} min)</div>
            <div v-if="stats.time_s_jerk !== null">
              <b>Time (Jerk):</b> {{ stats.time_s_jerk }} s ({{ (stats.time_s_jerk/60).toFixed(1) }} min)
            </div>
            <div><b>Moves:</b> {{ stats.move_count }}</div>
            <div><b>Volume:</b> {{ stats.volume_mm3 }} mm³</div>
            <div><b>Tight Segments:</b> {{ stats.tight_segments || 0 }}</div>
            <div><b>Trochoid Arcs:</b> {{ stats.trochoid_arcs || 0 }}</div>
          </div>
          <div class="mt-2 flex items-center gap-3 text-xs text-gray-600">
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#0ea5e9"
              />
              Normal speed
            </span>
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#f59e0b"
              />
              Moderate slowdown
            </span>
            <span class="flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#ef4444"
              />
              Heavy slowdown
            </span>
            <span class="ml-4 flex items-center gap-1">
              <span
                class="inline-block w-3 h-3 rounded"
                style="background:#7c3aed"
              />
              Trochoid arcs
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- NC Preview Drawer -->
    <PreviewNcDrawer
      :open="ncOpen"
      :gcode-text="ncText"
      @close="ncOpen = false"
    />
    <CompareAfModes
      v-model="compareOpen"
      :request-body="buildBaseExportBody()"
      @make-default="handleMakeDefault"
    />
  
    <!-- M.1.1 Machine Editor & Compare Modals -->
    <MachineEditorModal
      v-model="machineEditorOpen"
      :profile="selMachine"
      @saved="onMachineSaved"
    />
    <CompareMachines
      v-model="compareMachinesOpen"
      :machines="machines"
      :body="buildBaseExportBody()"
    />
  
    <!-- M.3 Compare Settings Modal -->
    <CompareSettings 
      v-model="compareSettingsOpen" 
      :baseline-nc="compareData.baselineNc" 
      :opt-nc="compareData.optNc" 
      :baseline-time="compareData.tb" 
      :opt-time="compareData.topt" 
    />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted, watch, computed, reactive } from 'vue'
import { usePocketSettings } from './adaptive/composables/usePocketSettings'

import PreviewNcDrawer from './PreviewNcDrawer.vue'
import CompareAfModes from './CompareAfModes.vue'
import MachineEditorModal from './MachineEditorModal.vue'
import CompareMachines from './CompareMachines.vue'
import CompareSettings from './CompareSettings.vue'
import CompareModeButton from '@/components/compare/CompareModeButton.vue'
import { MachineSelector, PostProcessorConfig, TrochoidSettings, JerkAwareSettings, HudOverlayControls } from './adaptive'

const cv = ref<HTMLCanvasElement|null>(null)

// Pocket settings (from composable)
const {
  toolD,
  stepoverPct,
  stepdown,
  margin,
  strategy,
  climb,
  cornerRadiusMin,
  slowdownFeedPct,
  feedXY,
  units,
} = usePocketSettings()

const overlays = ref<any[]>([])
const showTight = ref(true)
const showSlow = ref(true)
const showFillets = ref(true)
const postId = ref('GRBL')

// L.3 state
const useTrochoids = ref(false)
const trochoidRadius = ref(1.5)
const trochoidPitch = ref(3.0)

const jerkAware = ref(false)
const machineAccel = ref(800)
const machineJerk = ref(2000)
const cornerTol = ref(0.2)

// M.1 machine profiles state
const machines = ref<any[]>([])
const machineId = ref<string>(localStorage.getItem('toolbox.machine') || 'Mach4_Router_4x8')
const selMachine = computed(() => machines.value.find(m => m.id === machineId.value))

// M.3 Energy & Heat computed properties
const chipPct = computed(() => !energyOut.value ? 0 : 100 * energyOut.value.totals.heat.chip_j / energyOut.value.totals.energy_j)
const toolPct = computed(() => !energyOut.value ? 0 : 100 * energyOut.value.totals.heat.tool_j / energyOut.value.totals.energy_j)
const workPct = computed(() => !energyOut.value ? 0 : 100 * energyOut.value.totals.heat.work_j / energyOut.value.totals.energy_j)

const energyPolyline = computed(() => {
  if (!energyOut.value) return ''
  const seg = energyOut.value.segments
  const cum: number[] = []
  let s = 0
  for (const k of seg) {
    s += k.energy_j
    cum.push(s)
  }
  if (!cum.length) return ''
  const maxY = cum[cum.length - 1]
  const W = 300, H = 120
  return cum.map((v, i) => {
    const x = (i / (cum.length - 1)) * W
    const y = H - (v / maxY) * H
    return `${x},${y}`
  }).join(' ')
})

// M.3 Bottleneck pie chart data
const capsPie = computed(() => {
  const c = planOut.value?.stats?.caps || {feed_cap: 0, accel: 0, jerk: 0, none: 0}
  const total = Math.max(1, c.feed_cap + c.accel + c.jerk + c.none)
  return [
    {label: 'Feed cap', v: c.feed_cap, color: '#f59e0b'},
    {label: 'Accel', v: c.accel, color: '#14b8a6'},
    {label: 'Jerk', v: c.jerk, color: '#ec4899'},
    {label: 'None', v: c.none, color: '#9ca3af'}
  ].map(s => ({...s, pct: s.v / total}))
})

watch(machineId, (v: string) => {
  localStorage.setItem('toolbox.machine', v || '')
  // Auto-select matching post if profile has default
  const m = selMachine.value
  if (m?.post_id_default) {
    postId.value = m.post_id_default
  }
})

// Adaptive feed override state
const afMode = ref<'inherit'|'comment'|'inline_f'|'mcode'>('inherit')
const afInlineMinF = ref(600)
const afMStart = ref('M52 P')
const afMEnd = ref('M52 P100')

// NC preview drawer state
const ncOpen = ref(false)
const ncText = ref('')

// Compare modal state
const compareOpen = ref(false)

// M.1.1 Machine editor and compare state
const machineEditorOpen = ref(false)
const compareMachinesOpen = ref(false)
const showBottleneckMap = ref(true)

// M.3 Compare settings modal state
const compareSettingsOpen = ref(false)
const compareData = reactive({
  baselineNc: '',
  optNc: '',
  tb: 0,
  topt: 0
})

// M.3 Chipload enforcement state
const enforceChip = ref(true)
const chipTol = ref(0.02)

// M.2 Optimizer state
const optFeedLo = ref(600)
const optFeedHi = ref(9000)
const optStpLo = ref(0.25)
const optStpHi = ref(0.85)
const optRpmLo = ref(8000)
const optRpmHi = ref(24000)
const optFlutes = ref(2)
const optChip = ref(0.05)
const optGridF = ref(6)
const optGridS = ref(6)
const optOut = ref<any>(null)

// M.3 Energy & Heat state
const materialId = ref('maple_hard')
const energyOut = ref<any>(null)
const heatTS = ref<any>(null)
const includeCsvLinks = ref(true)  // Include CSV download links in thermal report

// M.4 CAM Logs & Learning state
const adoptOverrides = ref(true)  // Apply learned feed overrides
const sessionOverrideFactor = ref<number | null>(null)  // Live learn session-only feed scale
const liveLearnApplied = ref(false)  // Enable/disable live learn factor
const measuredSeconds = ref<number | null>(null)  // Actual runtime for live learn

// Live learn clamps (safety)
const LL_MIN = 0.80  // -20%
const LL_MAX = 1.25  // +25%

// Batch export mode selection state (localStorage persisted)
const exportModes = ref<{comment: boolean, inline_f: boolean, mcode: boolean}>((() => {
  try {
    return JSON.parse(localStorage.getItem('toolbox.af.modes') || '')
  } catch {
    return {comment: true, inline_f: true, mcode: true}
  }
})())

watch(exportModes, () => {
  localStorage.setItem('toolbox.af.modes', JSON.stringify(exportModes.value))
}, { deep: true })

// Job name for filename stem (localStorage persisted)
const jobName = ref(localStorage.getItem('toolbox.job_name') || '')
watch(jobName, (v: string) => {
  localStorage.setItem('toolbox.job_name', v || '')
})

// Demo outer rectangle - can be replaced with real geometry from upload
const loops = ref([ 
  { pts: [ [0,0],[100,0],[100,60],[0,60] ] } 
])

const moves = ref<any[]>([])
const stats = ref<any|null>(null)
const posts = ref<string[]>(['GRBL','Mach4','LinuxCNC','PathPilot','MASSO'])

// Computed aliases for template compatibility
const planOut = computed(() => ({
  moves: moves.value,
  stats: stats.value
}))
const profileId = computed(() => machineId.value)

// Per-post adaptive-feed preset store (localStorage)
type AfPreset = {
  mode: 'inherit'|'comment'|'inline_f'|'mcode'
  slowdown_threshold?: number|null
  inline_min_f?: number|null
  mcode_start?: string|null
  mcode_end?: string|null
}

const PRESETS_KEY = 'toolbox.af.presets'
function readPresets(): Record<string,AfPreset> {
  try { return JSON.parse(localStorage.getItem(PRESETS_KEY) || '{}') } catch { return {} }
}
function writePresets(p: Record<string,AfPreset>) {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(p))
}

function savePresetForPost(pid: string) {
  if (!pid) return
  const presets = readPresets()
  presets[pid] = {
    mode: afMode.value,
    slowdown_threshold: undefined,
    inline_min_f: afMode.value==='inline_f' ? afInlineMinF.value : undefined,
    mcode_start: afMode.value==='mcode' ? afMStart.value : undefined,
    mcode_end:   afMode.value==='mcode' ? afMEnd.value   : undefined
  }
  writePresets(presets)
}

function loadPresetForPost(pid: string) {
  if (!pid) return false
  const p = readPresets()[pid]
  if (!p) return false
  afMode.value = (p.mode || 'inherit') as any
  if (p.inline_min_f != null) afInlineMinF.value = p.inline_min_f
  if (p.mcode_start) afMStart.value = p.mcode_start
  if (p.mcode_end)   afMEnd.value   = p.mcode_end
  return true
}

function resetPresetForPost(pid: string) {
  if (!pid) return
  const presets = readPresets()
  delete presets[pid]
  writePresets(presets)
  afMode.value = 'inherit'
}

// Auto-load per-post preset when user changes post
watch(postId, (pid: string)=>{ if (!pid) return; loadPresetForPost(pid) })

function buildBaseExportBody(){
  return {
    loops: loops.value,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepoverPct.value/100.0,
    stepdown: stepdown.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.8,
    climb: climb.value,
    feed_xy: feedXY.value,
    safe_z: 5,
    z_rough: -stepdown.value,
    post_id: postId.value,
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: jerkAware.value,
    machine_feed_xy: 1200,
    machine_rapid: 3000,
    machine_accel: machineAccel.value,
    machine_jerk: machineJerk.value,
    corner_tol_mm: cornerTol.value
  }
}

function openCompare(){ compareOpen.value = true }

function handleMakeDefault(mode: string){
  afMode.value = mode as any
  // persist for current post
  savePresetForPost(postId.value)
  compareOpen.value = false
}

function selectedModes(): string[] {
  const sel: string[] = []
  if (exportModes.value.comment) sel.push('comment')
  if (exportModes.value.inline_f) sel.push('inline_f')
  if (exportModes.value.mcode) sel.push('mcode')
  return sel
}

async function batchExport(){
  const base = buildBaseExportBody()
  const body: any = {
    ...base,
    post_id: postId.value,
    modes: selectedModes(),
    job_name: jobName.value || undefined  // Include job_name if provided
  }
  
  try {
    const r = await api('/api/cam/pocket/adaptive/batch_export', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    
    // Use job_name if provided, else fallback to mode-based name
    const stem = (jobName.value && jobName.value.trim()) 
      ? jobName.value.trim().replace(/\s+/g, '_')
      : `ToolBox_MultiMode_${selectedModes().join('-') || 'all'}`
    a.download = `${stem}.zip`
    
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (err) {
    console.error('Batch export failed:', err)
    alert('Failed to batch export: ' + err)
  }
}

function draw(){
  const c = cv.value!
  const ctx = c.getContext('2d')!
  const dpr = window.devicePixelRatio||1
  c.width = c.clientWidth*dpr
  c.height = c.clientHeight*dpr
  ctx.setTransform(dpr,0,0,dpr,0,0)
  ctx.clearRect(0,0,c.clientWidth,c.clientHeight)

  // Simple fit to canvas
  const W=c.clientWidth, H=c.clientHeight
  const box = {minx:0,miny:0,maxx:100,maxy:60}
  const sx = W/(box.maxx-box.minx+20), sy=H/(box.maxy-box.miny+20)
  const s = Math.min(sx,sy)*0.9
  const ox=10, oy=H-10
  ctx.translate(ox,oy)
  ctx.scale(s,-s)

  // Draw geometry outline
  ctx.strokeStyle='#94a3b8'
  ctx.lineWidth=1/s
  ctx.beginPath()
  ctx.rect(0,0,100,60)
  ctx.stroke()

  // Draw toolpath with conditional visualization
  // M.1.1: Bottleneck map OR heatmap coloring (user toggle)
  if (moves.value.length > 0) {
    let last:any=null  // Shared across passes
    if (showBottleneckMap.value) {
      // M.1.1 Pass 1: Bottleneck map - color by meta.limit
      last=null
      for (const m of moves.value){
        if ((m.code==='G1'||m.code==='G2'||m.code==='G3') && 'x' in m && 'y' in m){
          if (last){
            const lim = m.meta?.limit || 'none'
            const col = lim==='feed_cap' ? '#f59e0b' :   // orange (amber-500)
                        lim==='accel'    ? '#14b8a6' :   // teal (teal-500)
                        lim==='jerk'     ? '#ec4899' :   // pink (pink-500)
                        null
            if (col) {
              ctx.strokeStyle = col
              ctx.lineWidth = 2/s
              ctx.beginPath()
              ctx.moveTo(last.x, last.y)
              ctx.lineTo(m.x, m.y)
              ctx.stroke()
            }
          }
          last = {x:m.x,y:m.y}
        } else if ('x' in m && 'y' in m){
          last = {x:m.x,y:m.y}
        }
      }
    } else {
      // Pass 1: slowdown heatmap for non-trochoid segments (G0/G1)
      last=null
      for (const m of moves.value){
        if ((m.code==='G0'||m.code==='G1') && 'x' in m && 'y' in m){
          if (last && m.code === 'G1' && !m.meta?.trochoid){ 
          // Color-code by slowdown factor
          const slowdown = m.meta?.slowdown ?? 1.0
          // Map slowdown [0.4..1.0] to color gradient [red..blue]
          // slowdown 1.0 = blue (full speed), 0.4 = red (heavy slowdown)
          const t = Math.min(1, Math.max(0, (1.0 - slowdown) / 0.6))  // 0=normal, 1=heavy
          
          let r, g, b
          if (t < 0.5) {
            // Blue (#0ea5e9) → Orange (#f59e0b)
            const t2 = t * 2  // 0..1
            r = Math.round(14 + (245 - 14) * t2)
            g = Math.round(165 + (158 - 165) * t2)
            b = Math.round(233 + (11 - 233) * t2)
          } else {
            // Orange (#f59e0b) → Red (#ef4444)
            const t2 = (t - 0.5) * 2  // 0..1
            r = Math.round(245 + (239 - 245) * t2)
            g = Math.round(158 + (68 - 158) * t2)
            b = Math.round(11 + (68 - 11) * t2)
          }
          
          ctx.strokeStyle = `rgb(${r},${g},${b})`
          ctx.lineWidth = 1.2/s
          ctx.beginPath()
          ctx.moveTo(last.x, last.y)
          ctx.lineTo(m.x, m.y)
          ctx.stroke()
        }
        last = {x:m.x,y:m.y}
      } else if ('x' in m && 'y' in m) {
        last = {x:m.x,y:m.y}
      }
    }
    }  // End if/else bottleneck map toggle
    
    // Pass 2: trochoid arcs in **distinct purple** (L.3)
    last = null
    for (const m of moves.value){
      if ((m.code==='G2' || m.code==='G3') && m.meta?.trochoid && 'x' in m && 'y' in m){
        if (last){
          ctx.strokeStyle = '#7c3aed'  // purple (violet-600)
          ctx.lineWidth = 1.5/s
          ctx.beginPath()
          ctx.moveTo(last.x, last.y)
          ctx.lineTo(m.x, m.y)
          ctx.stroke()
        }
        last = {x:m.x,y:m.y}
      } else if ('x' in m && 'y' in m){
        last = {x:m.x,y:m.y}
      }
    }

    // Draw entry point (green)
    if (moves.value.length > 0) {
      const first = moves.value.find((m: any) => 'x' in m && 'y' in m)
      if (first) {
        ctx.fillStyle='#10b981'
        ctx.beginPath()
        ctx.arc(first.x, first.y, 2/s, 0, Math.PI*2)
        ctx.fill()
      }
    }
  }
  
  // Draw HUD overlays
  for (const ovl of overlays.value) {
    if (!('x' in ovl && 'y' in ovl)) continue
    const x = ovl.x, y = ovl.y
    
    if (ovl.kind === 'tight_radius' && showTight.value) {
      // Red circle for tight radius zones
      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 1.5/s
      ctx.beginPath()
      ctx.arc(x, y, ovl.r || 2, 0, Math.PI*2)
      ctx.stroke()
    } else if (ovl.kind === 'slowdown' && showSlow.value) {
      // Orange square for slowdown zones
      ctx.fillStyle = '#f97316'
      ctx.beginPath()
      const sz = 2/s
      ctx.rect(x - sz, y - sz, sz*2, sz*2)
      ctx.fill()
    } else if (ovl.kind === 'fillet' && showFillets.value) {
      // Green circle for fillet points
      ctx.fillStyle = '#10b981'
      ctx.beginPath()
      ctx.arc(x, y, 1.5/s, 0, Math.PI*2)
      ctx.fill()
    }
  }
}

// M.3 Bottleneck pie chart arc path generator
function arcPath(index: number): string {
  const slices = capsPie.value
  const tau = Math.PI * 2
  let a0 = 0
  for (let i = 0; i < index; i++) {
    a0 += slices[i].pct * tau
  }
  const a1 = a0 + slices[index].pct * tau
  const R = 50
  const x0 = Math.cos(a0) * R
  const y0 = Math.sin(a0) * R
  const x1 = Math.cos(a1) * R
  const y1 = Math.sin(a1) * R
  const large = (a1 - a0) > Math.PI ? 1 : 0
  return `M0,0 L${x0},${y0} A${R},${R} 0 ${large} 1 ${x1},${y1} Z`
}

async function plan(){
  const baseBody = {
    loops: loops.value,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepoverPct.value/100.0,
    stepdown: stepdown.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.8,
    climb: climb.value,
    feed_xy: feedXY.value,
    safe_z: 5,
    z_rough: -stepdown.value,
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value/100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    // L.3 parameters
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: jerkAware.value,
    machine_feed_xy: feedXY.value,
    machine_rapid: 3000.0,
    machine_accel: machineAccel.value,
    machine_jerk: machineJerk.value,
    corner_tol_mm: cornerTol.value,
    // M.1 parameters
    machine_profile_id: machineId.value || undefined
  }
  
  // M.4: Apply session override and learned rules
  const body = patchBodyWithSessionOverride(baseBody)
  
  try {
    const r = await api('/api/cam/pocket/adaptive/plan', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(body) 
    })
    const out = await r.json()
    moves.value = out.moves || []
    stats.value = out.stats || null
    overlays.value = out.overlays || []
    draw()
  } catch (err) {
    console.error('Plan failed:', err)
    alert('Failed to plan pocket: ' + err)
  }
}

function buildAdaptiveOverride() {
  if (afMode.value === 'inherit') {
    return null
  }
  
  const override: any = { mode: afMode.value }
  
  if (afMode.value === 'inline_f') {
    override.inline_min_f = afInlineMinF.value
  }
  
  if (afMode.value === 'mcode') {
    override.mcode_start = afMStart.value
    override.mcode_end = afMEnd.value
  }
  
  return override
}

async function previewNc() {
  const baseBody = {
    loops: loops.value,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepoverPct.value/100.0,
    stepdown: stepdown.value,
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value/100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.8,
    climb: climb.value,
    feed_xy: feedXY.value,
    safe_z: 5,
    z_rough: -stepdown.value,
    post_id: postId.value,
    // L.3 parameters
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: jerkAware.value,
    machine_feed_xy: feedXY.value,
    machine_rapid: 3000.0,
    machine_accel: machineAccel.value,
    machine_jerk: machineJerk.value,
    corner_tol_mm: cornerTol.value,
    // Adaptive feed override
    adaptive_feed_override: buildAdaptiveOverride()
  }
  const body = patchBodyWithSessionOverride(baseBody)
  
  try {
    const r = await api('/api/cam/pocket/adaptive/gcode', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(body) 
    })
    ncText.value = await r.text()
    ncOpen.value = true
  } catch (err) {
    console.error('Preview failed:', err)
    alert('Failed to preview NC: ' + err)
  }
}

async function exportProgram(){
  const baseBody: any = {
    loops: loops.value,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepoverPct.value/100.0,
    stepdown: stepdown.value,
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value/100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.8,
    climb: climb.value,
    feed_xy: feedXY.value,
    safe_z: 5,
    z_rough: -stepdown.value,
    post_id: postId.value,
    // L.3 parameters
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: jerkAware.value,
    machine_feed_xy: feedXY.value,
    machine_rapid: 3000.0,
    machine_accel: machineAccel.value,
    machine_jerk: machineJerk.value,
    corner_tol_mm: cornerTol.value,
    // Adaptive feed override
    adaptive_feed_override: buildAdaptiveOverride(),
    // Job name for filename
    job_name: jobName.value || undefined
  }
  const body = patchBodyWithSessionOverride(baseBody)
  
  try {
    const r = await api('/api/cam/pocket/adaptive/gcode', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(body) 
    })
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    
    // Use job_name if provided, else fallback to strategy_post pattern
    const stem = (jobName.value && jobName.value.trim()) 
      ? jobName.value.trim().replace(/\s+/g, '_')
      : `pocket_${strategy.value.toLowerCase()}_${postId.value.toLowerCase()}`
    a.download = `${stem}.nc`
    
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (err) {
    console.error('Export failed:', err)
    alert('Failed to export G-code: ' + err)
  }
}

// Load adaptive feed preferences from localStorage
function loadAfPrefs() {
  const saved = localStorage.getItem('toolbox.adaptiveFeed')
  if (saved) {
    try {
      const prefs = JSON.parse(saved)
      afMode.value = prefs.mode || 'inherit'
      afInlineMinF.value = prefs.inline_min_f || 600
      afMStart.value = prefs.mcode_start || 'M52 P'
      afMEnd.value = prefs.mcode_end || 'M52 P100'
    } catch (e) {
      console.warn('Failed to load adaptive feed prefs:', e)
    }
  }
}

// M.1.1 Machine editor and compare functions
function openMachineEditor() {
  machineEditorOpen.value = true
}

async function onMachineSaved(id: string) {
  machineId.value = id
  // Refresh machine list
  try {
    const r = await api('/api/machine/profiles')
    machines.value = await r.json()
  } catch (e) {
    console.error('Failed to refresh machines:', e)
  }
}

function compareMachinesFunc() {
  compareMachinesOpen.value = true
}

// M.2 Optimizer functions
async function runWhatIf() {
  // Ensure we have planned moves
  if (!moves.value?.length) {
    await plan()
  }
  
  if (!moves.value?.length) {
    alert('No moves available. Plan a pocket first.')
    return
  }
  
  if (!machineId.value) {
    alert('Select a machine profile first.')
    return
  }
  
  try {
    const body: Record<string, any> = {
      moves: moves.value,
      machine_profile_id: machineId.value,
      z_total: -stepdown.value,
      stepdown: stepdown.value,
      safe_z: 5,
      bounds: {
        feed: [optFeedLo.value, optFeedHi.value],
        stepover: [optStpLo.value, optStpHi.value],
        rpm: [optRpmLo.value, optRpmHi.value]
      },
      tool: {
        flutes: optFlutes.value,
        chipload_target_mm: optChip.value
      },
      grid: [optGridF.value, optGridS.value]
    }

    // M.3 Add chipload enforcement tolerance if enabled
    if (enforceChip.value) {
      body.tolerance_chip_mm = chipTol.value
    }
    
    const r = await api('/api/cam/opt/what_if', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      const err = await r.text()
      throw new Error(err)
    }
    
    optOut.value = await r.json()
  } catch (e) {
    console.error('What-if optimization failed:', e)
    alert('Optimization failed: ' + e)
  }
}

function applyRecommendation() {
  if (!optOut.value?.opt?.best) {
    return
  }
  
  const b = optOut.value.opt.best
  
  // Apply stepover (best.stepover is 0..1, UI expects %)
  stepoverPct.value = Math.round(b.stepover * 100)
  
  // Apply feed (update the feed_xy ref)
  feedXY.value = Math.round(b.feed_mm_min)
  
  // Note: RPM can be displayed or used in spindle control later
  // For now, just show it in the UI results
  
  alert(`Applied: Feed ${b.feed_mm_min} mm/min, Stepover ${(b.stepover*100).toFixed(1)}%\nRecommended RPM: ${b.rpm}\nRe-plan to see updated toolpath.`)
}

// M.3: Compute energy & heat for current toolpath
async function runEnergy() {
  try {
    // Ensure we have moves
    if (!moves.value?.length) {
      await plan()
    }
    if (!moves.value?.length) {
      alert('No moves available for energy calculation')
      return
    }
    
    const body: any = {
      moves: moves.value,
      material_id: materialId.value,
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      job_name: jobName.value || undefined
    }
    
    const r = await api('/api/cam/metrics/energy', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    energyOut.value = await r.json()
  } catch (e: any) {
    alert('Energy calculation failed: ' + e)
  }
}

// M.3: Export per-segment energy breakdown as CSV
async function exportEnergyCsv() {
  try {
    if (!energyOut.value) {
      alert('Run energy calculation first')
      return
    }
    
    // Ensure we have moves
    if (!moves.value?.length) {
      await plan()
    }
    if (!moves.value?.length) {
      alert('No moves available for CSV export')
      return
    }
    
    const body: any = {
      moves: moves.value,
      material_id: materialId.value,
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      job_name: jobName.value || undefined
    }
    
    const r = await api('/api/cam/metrics/energy_csv', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = '' // Let server Content-Disposition filename win
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e: any) {
    alert('CSV export failed: ' + e)
  }
}

// M.3: Run heat timeseries (power over time)
async function runHeatTS() {
  if (!planOut.value?.moves || !materialId.value || !profileId.value) {
    alert('Run plan first, select material and profile')
    return
  }
  
  try {
    const body = {
      moves: planOut.value.moves,
      machine_profile_id: profileId.value,
      material_id: materialId.value,
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      bins: 120
    }
    
    const r = await api('/api/cam/metrics/heat_timeseries', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    heatTS.value = await r.json()
  } catch (e: any) {
    alert('Heat timeseries failed: ' + e)
  }
}

// M.3: Convert heat timeseries to SVG polyline
function tsPolyline(field: 'p_chip' | 'p_tool' | 'p_work'): string {
  if (!heatTS.value?.[field]) return '0,0'
  
  const data = heatTS.value[field] as number[]
  const tAxis = heatTS.value.t as number[]
  const maxT = Math.max(...tAxis)
  const maxP = Math.max(...data)
  
  if (maxT <= 0 || maxP <= 0) return '0,0'
  
  // Map to 300×120 viewBox
  const pts = data.map((p, i) => {
    const x = (tAxis[i] / maxT) * 300
    const y = 120 - (p / maxP) * 110
    return `${x},${y}`
  })
  
  return pts.join(' ')
}

// M.3: Export bottleneck CSV
async function exportBottleneckCsv() {
  if (!planOut.value?.moves || !profileId.value) {
    alert('Run plan first and select profile')
    return
  }
  
  try {
    const body = {
      moves: planOut.value.moves,
      machine_profile_id: profileId.value,
      job_name: 'pocket'
    }
    
    const r = await api('/api/cam/metrics/bottleneck_csv', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = '' // Let server Content-Disposition filename win
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e: any) {
    alert('Bottleneck CSV export failed: ' + e)
  }
}

// M.3: Export thermal report (Markdown)
async function exportThermalReport() {
  if (!planOut.value?.moves) {
    alert('Run plan first')
    return
  }
  
  try {
    const body = {
      moves: planOut.value.moves,
      machine_profile_id: profileId.value || 'Mach4_Router_4x8',
      material_id: materialId.value || 'maple_hard',
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      bins: 200,
      job_name: 'pocket',
      budgets: {
        chip_j: 500.0,
        tool_j: 150.0,
        work_j: 100.0
      },
      include_csv_links: includeCsvLinks.value
    }
    
    const r = await api('/api/cam/metrics/thermal_report_md', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = '' // Let server Content-Disposition filename win
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e: any) {
    alert('Thermal report export failed: ' + e)
  }
}

// M.4: Export thermal bundle (MD + moves.json ZIP)
async function exportThermalBundle() {
  if (!planOut.value?.moves) {
    alert('Run plan first')
    return
  }
  
  try {
    const body = {
      moves: planOut.value.moves,
      machine_profile_id: profileId.value || 'Mach4_Router_4x8',
      material_id: materialId.value || 'maple_hard',
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      bins: 200,
      job_name: 'pocket',
      budgets: {
        chip_j: 500.0,
        tool_j: 150.0,
        work_j: 100.0
      },
      include_csv_links: includeCsvLinks.value
    }
    
    const r = await api('/api/cam/metrics/thermal_report_bundle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = '' // Let server Content-Disposition filename win
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e: any) {
    alert('Thermal bundle export failed: ' + e)
  }
}

// M.4: Compute live learn session factor from estimated vs actual time
function computeLiveLearnFactor(estimatedSeconds: number, actualSeconds: number): number | null {
  if (!estimatedSeconds || !actualSeconds) return null
  // time ~ 1 / feed ⇒ feed scale ≈ actual / estimated
  // if slower than predicted (actual > est), raw > 1 ⇒ need MORE feed
  const raw = actualSeconds / estimatedSeconds
  const clamped = Math.max(LL_MIN, Math.min(LL_MAX, raw))
  return Number(clamped.toFixed(3))
}

// M.4: Patch request body with session override and learned rules
function patchBodyWithSessionOverride(body: any): any {
  if (liveLearnApplied.value && sessionOverrideFactor.value) {
    body.session_override_factor = sessionOverrideFactor.value
  }
  if (adoptOverrides.value) {
    body.adopt_overrides = true
  }
  return body
}

// M.4: Log current run to database
async function logCurrentRun(actualSeconds?: number) {
  if (!planOut.value?.moves?.length) {
    await plan()
  }
  
  try {
    const segs = planOut.value.moves.map((m: any, i: number) => ({
      idx: i,
      code: m.code,
      x: m.x,
      y: m.y,
      len_mm: m._len_mm || 0,
      limit: m.meta?.limit || null,
      slowdown: m.meta?.slowdown ?? null,
      trochoid: !!m.meta?.trochoid,
      radius_mm: m.meta?.radius_mm ?? null,
      feed_f: m.f ?? null
    }))
    
    const run = {
      job_name: 'pocket',
      machine_id: profileId.value || 'Mach4_Router_4x8',
      material_id: materialId.value || 'maple_hard',
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100,
      stepdown: stepdown.value,
      post_id: null,
      feed_xy: feedXY.value || undefined,
      rpm: undefined,
      est_time_s: planOut.value.stats?.time_s_jerk ?? planOut.value.stats?.time_s_classic ?? null,
      act_time_s: actualSeconds ?? null,
      notes: null
    }
    
    const r = await api('/api/cam/logs/write', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ run, segments: segs })
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const data = await r.json()
    
    // Live learn: compute session factor if actual time provided
    const est = planOut.value.stats?.time_s_jerk ?? planOut.value.stats?.time_s_classic
    if (actualSeconds && est) {
      const f = computeLiveLearnFactor(est, actualSeconds)
      if (f) {
        sessionOverrideFactor.value = f
        liveLearnApplied.value = true
        console.info(`Live learn: session feed scale set to ×${f}`)
      }
    }
    
    alert(`Logged run ${data.run_id} successfully` + (sessionOverrideFactor.value ? `\nLive learn: ×${sessionOverrideFactor.value}` : ''))
  } catch (e: any) {
    alert('Log run failed: ' + e)
  }
}

// M.4: Train feed overrides from logged runs
async function trainOverrides() {
  if (!profileId.value) {
    alert('Select machine profile first')
    return
  }
  
  try {
    const r = await api('/api/cam/learn/train', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ machine_profile: profileId.value, r_min_mm: 5 })
    })
    
    if (!r.ok) {
      throw new Error(await r.text())
    }
    
    const out = await r.json()
    alert(`Learned rules for ${out.machine_profile || out.machine_id}:\n` + JSON.stringify(out.rules, null, 2))
  } catch (e: any) {
    alert('Train overrides failed: ' + e)
  }
}

// M.3: Open compare settings modal (baseline vs recommendation)
async function openCompareSettings() {
  try {
    if (!optOut.value?.opt?.best) {
      alert('Run What-If optimizer first')
      return
    }
    
    // Build baseline request body (current UI settings)
    const baseBody: any = {
      loops: loops.value,
      units: units.value,
      tool_d: toolD.value,
      stepover: stepoverPct.value / 100.0,
      stepdown: stepdown.value,
      corner_radius_min: cornerRadiusMin.value,
      target_stepover: stepoverPct.value / 100.0,
      slowdown_feed_pct: slowdownFeedPct.value,
      margin: margin.value,
      strategy: strategy.value,
      smoothing: 0.8,
      climb: climb.value,
      feed_xy: feedXY.value,
      safe_z: 5,
      z_rough: -stepdown.value,
      post_id: postId.value,
      use_trochoids: useTrochoids.value,
      trochoid_radius: trochoidRadius.value,
      trochoid_pitch: trochoidPitch.value,
      jerk_aware: jerkAware.value,
      machine_feed_xy: feedXY.value,
      machine_rapid: 3000.0,
      machine_accel: machineAccel.value,
      machine_jerk: machineJerk.value,
      corner_tol_mm: cornerTol.value,
      adaptive_feed_override: buildAdaptiveOverride(),
      job_name: jobName.value || undefined
    }
    
    // Build recommendation request body (apply optimizer results)
    const best = optOut.value.opt.best
    const recBody: any = {
      ...baseBody,
      stepover: best.stepover,
      feed_xy: best.feed_mm_min,
      target_stepover: best.stepover
    }
    
    // Fetch baseline NC and plan
    const [baselineNc, baselinePlan] = await Promise.all([
      api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(baseBody)
      }).then(r => r.text()),
      api('/api/cam/pocket/adaptive/plan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(baseBody)
      }).then(r => r.json())
    ])
    
    // Fetch recommendation NC and plan
    const [optNc, optPlan] = await Promise.all([
      api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(recBody)
      }).then(r => r.text()),
      api('/api/cam/pocket/adaptive/plan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(recBody)
      }).then(r => r.json())
    ])
    
    // Populate compare data
    compareData.baselineNc = baselineNc
    compareData.optNc = optNc
    compareData.tb = baselinePlan.stats?.time_s_jerk || baselinePlan.stats?.time_s_classic || 0
    compareData.topt = optPlan.stats?.time_s_jerk || optPlan.stats?.time_s_classic || 0
    
    // Open modal
    compareSettingsOpen.value = true
  } catch (e: any) {
    alert('Compare settings failed: ' + e)
  }
}

// Save adaptive feed preferences to localStorage
function saveAfPrefs() {
  localStorage.setItem('toolbox.adaptiveFeed', JSON.stringify({
    mode: afMode.value,
    inline_min_f: afInlineMinF.value,
    mcode_start: afMStart.value,
    mcode_end: afMEnd.value
  }))
}

// Watch for changes and save
watch([afMode, afInlineMinF, afMStart, afMEnd], saveAfPrefs)

onMounted(async () => {
  loadAfPrefs()
  
  // M.1: Load machine profiles
  try {
    const r = await api('/api/machine/profiles')
    machines.value = await r.json()
  } catch (e) {
    console.error('Failed to load machine profiles:', e)
  }
  
  setTimeout(draw, 100)
})
</script>
