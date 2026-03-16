<script setup lang="ts">
/**
 * OverlaysLayer — Consolidated overlay components for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Contains: LoadingOverlay, MemoryWarning, ValidationOverlay, EmptyState
 */

import { LoadingOverlay, ValidationOverlay, EmptyState } from './index';
import MemoryWarning from '../MemoryWarning.vue';
import type { MemoryInfo } from '@/stores/useToolpathPlayerStore';
import type { ValidationIssue } from '@/util/gcodeValidator';

interface ParseProgress {
  stage: 'uploading' | 'simulating' | 'idle' | 'complete';
  percent: number;
}

interface Props {
  loading: boolean;
  parseProgress: ParseProgress;
  showMemBanner: boolean;
  memoryInfo: MemoryInfo;
  hasErrors: boolean;
  validationErrors: ValidationIssue[];
  segmentCount: number;
  error: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  dismissMemory: [];
  optimizeMemory: [];
  loadAnyway: [];
}>();
</script>

<template>
  <!-- Loading overlay with progress -->
  <LoadingOverlay
    v-if="props.loading"
    :progress="props.parseProgress"
  />

  <!-- Memory warning banner -->
  <MemoryWarning
    v-if="props.showMemBanner"
    :memory-info="props.memoryInfo"
    @close="emit('dismissMemory')"
    @optimize="emit('optimizeMemory')"
  />

  <!-- Validation error overlay -->
  <ValidationOverlay
    v-if="props.hasErrors && !props.loading && props.segmentCount === 0"
    :errors="props.validationErrors"
    @load-anyway="emit('loadAnyway')"
  />

  <!-- Error / Empty state -->
  <EmptyState
    v-if="!props.loading && !props.hasErrors && props.segmentCount === 0"
    :error="props.error"
  />
</template>
