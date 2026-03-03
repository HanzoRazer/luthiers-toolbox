<template>
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="flex flex-wrap gap-4 items-center">
      <!-- Refresh Button -->
      <button
        :disabled="loading"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        @click="$emit('refresh')"
      >
        <span v-if="loading">Loading...</span>
        <span v-else>Refresh</span>
      </button>

      <!-- Limit Selector -->
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-700">Show:</label>
        <select
          :value="limit"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @change="$emit('update:limit', Number(($event.target as HTMLSelectElement).value))"
        >
          <option :value="10">
            10 runs
          </option>
          <option :value="25">
            25 runs
          </option>
          <option :value="50">
            50 runs
          </option>
          <option :value="100">
            100 runs
          </option>
        </select>
      </div>

      <!-- Risk Filter -->
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-700">Risk:</label>
        <select
          :value="riskFilter"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @change="$emit('update:riskFilter', ($event.target as HTMLSelectElement).value)"
        >
          <option value="all">
            All
          </option>
          <option value="green">
            Green
          </option>
          <option value="yellow">
            Yellow
          </option>
          <option value="orange">
            Orange
          </option>
          <option value="red">
            Red
          </option>
          <option value="unknown">
            Unknown
          </option>
        </select>
      </div>

      <!-- Status Filter -->
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-700">Status:</label>
        <select
          :value="statusFilter"
          class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @change="$emit('update:statusFilter', ($event.target as HTMLSelectElement).value)"
        >
          <option value="all">
            All
          </option>
          <option value="pending">
            Pending
          </option>
          <option value="running">
            Running
          </option>
          <option value="completed">
            Completed
          </option>
          <option value="error">
            Error
          </option>
        </select>
      </div>

      <!-- Last Updated -->
      <div
        v-if="lastUpdated"
        class="ml-auto text-sm text-gray-500"
      >
        Updated: {{ lastUpdated }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loading: boolean
  limit: number
  riskFilter: string
  statusFilter: string
  lastUpdated: string | null
}>()

defineEmits<{
  refresh: []
  'update:limit': [value: number]
  'update:riskFilter': [value: string]
  'update:statusFilter': [value: string]
}>()
</script>
