<script setup lang="ts">
/**
 * CanvasLayer — 2D/3D canvas switching for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles switching between ToolpathCanvas (2D) and ToolpathCanvas3D (3D).
 */

import ToolpathCanvas from '../ToolpathCanvas.vue';
import ToolpathCanvas3D from '../ToolpathCanvas3D.vue';

interface Props {
  viewMode: '2d' | '3d';
  showHeatmap: boolean;
  toolDiameter: number;
  colorByTool: boolean;
  toolFilter: number | null;
  showStock?: boolean;
  showGrid?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showStock: true,
  showGrid: true,
});

const canvas2DRef = defineModel<InstanceType<typeof ToolpathCanvas> | null>('canvas2DRef');
const canvas3DRef = defineModel<InstanceType<typeof ToolpathCanvas3D> | null>('canvas3DRef');
</script>

<template>
  <ToolpathCanvas
    v-if="props.viewMode === '2d'"
    ref="canvas2DRef"
    class="canvas-area"
    :show-heatmap="props.showHeatmap"
    :tool-diameter="props.toolDiameter"
    :color-by-tool="props.colorByTool"
    :tool-filter="props.toolFilter"
  />
  <ToolpathCanvas3D
    v-else
    ref="canvas3DRef"
    class="canvas-area"
    :tool-diameter="props.toolDiameter"
    :show-stock="props.showStock"
    :show-grid="props.showGrid"
    :show-heatmap="props.showHeatmap"
  />
</template>

<style scoped>
.canvas-area {
  flex: 1;
  min-height: 0;
}
</style>
