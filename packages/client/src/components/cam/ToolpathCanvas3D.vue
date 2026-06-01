<script setup lang="ts">
/**
 * ToolpathCanvas3D — P5 Three.js 3D Visualization
 *
 * Real 3D toolpath visualization with depth, showing actual Z movement.
 * Uses Three.js for WebGL rendering with orbit controls.
 *
 * Features:
 * - True 3D toolpath with Z depth
 * - Orbit/zoom/pan camera controls
 * - Tool cylinder visualization
 * - Stock material bounding box
 * - Color-coded move types (rapid/cut/arc)
 * - Depth-based line thickness
 * - Grid reference plane
 */

import { ref, onMounted, onUnmounted, watch, computed } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";
import { EngagementAnalyzer, type EngagementReport } from "@/util/engagementAnalyzer";
import { MEASUREMENT_COLORS, type Measurement, type Point3D } from "@/util/measurementTool";
import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Show stock material bounding box */
  showStock?: boolean;
  /** Show reference grid */
  showGrid?: boolean;
  /** Tool diameter in mm */
  toolDiameter?: number;
  /** Tool length in mm */
  toolLength?: number;
  /** Background color */
  backgroundColor?: string;
  /** P5: Enable heatmap mode */
  showHeatmap?: boolean;
  /** Optional per-tool dimensions keyed by tool number (F-Z3). */
  toolTable?: Record<number, { diameter: number; length?: number }>;
}

const props = withDefaults(defineProps<Props>(), {
  showStock: true,
  showGrid: true,
  toolDiameter: 6,
  toolLength: 50,
  backgroundColor: "#1e1e2e",
  showHeatmap: false,
});

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Refs
// ---------------------------------------------------------------------------

const containerRef = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);

// Three.js objects
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let animationFrameId: number;

// Toolpath objects
let pathGroup: THREE.Group;
let toolMesh: THREE.Mesh;
let _lastProgressIdx = -1;
let _currentToolNumber = -1;
let _currentToolLength = 0;
let stockMesh: THREE.Mesh;
let gridHelper: THREE.GridHelper;
let selectedLine: THREE.Line | null = null;

// P5: Measurement objects
let measurementGroup: THREE.Group;
let pendingMeasureLine: THREE.Line | null = null;
let pendingMeasureStartSphere: THREE.Mesh | null = null;

// P5: Raycasting for segment selection
const raycaster = new THREE.Raycaster();
raycaster.params.Line = { threshold: 3 }; // Click tolerance in world units
const mouse = new THREE.Vector2();

// P5: Engagement analyzer for heatmap
let engagementReport: EngagementReport | null = null;

function updateEngagement(): void {
  if (store.segments.length === 0) {
    engagementReport = null;
    return;
  }
  const analyzer = new EngagementAnalyzer({
    toolDiameter: props.toolDiameter,
  });
  engagementReport = analyzer.analyze(store.segments);
}

// Colors
const COLORS = {
  rapid: 0x999999,
  cut: 0x4a90d9,
  arc: 0x2ecc71,
  tool: 0xe74c3c,
  stock: 0x8b4513,
  grid: 0x444466,
  background: 0x1e1e2e,
  selected: 0xffd700, // Gold for selected segment
};

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

function initThree(): void {
  if (!containerRef.value || !canvasRef.value) return;

  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(props.backgroundColor);

  // Camera
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
  camera.position.set(150, 150, 150);
  camera.lookAt(0, 0, 0);

  // Renderer
  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: true,
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.screenSpacePanning = true;
  controls.minDistance = 10;
  controls.maxDistance = 2000;

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(100, 200, 100);
  scene.add(directionalLight);

  // Single group: one line per segment, built once per toolpath load (F-X1).
  pathGroup = new THREE.Group();
  pathGroup.name = "path";
  scene.add(pathGroup);

  // Tool
  createTool();

  // Grid
  if (props.showGrid) {
    createGrid();
  }

  // P5: Measurement group
  initMeasurementGroup();

  // Start animation loop
  animate();
}

function createTool(): void {
  _currentToolLength = props.toolLength;
  const geometry = new THREE.CylinderGeometry(
    props.toolDiameter / 2,
    props.toolDiameter / 2,
    props.toolLength,
    16
  );
  const material = new THREE.MeshPhongMaterial({
    color: COLORS.tool,
    shininess: 80,
    transparent: true,
    opacity: 0.9,
  });
  toolMesh = new THREE.Mesh(geometry, material);
  toolMesh.name = "tool";
  // Rotate so cylinder points down (Z axis)
  toolMesh.rotation.x = Math.PI / 2;
  scene.add(toolMesh);
}

function createGrid(): void {
  gridHelper = new THREE.GridHelper(200, 20, COLORS.grid, COLORS.grid);
  gridHelper.rotation.x = Math.PI / 2; // Rotate to XY plane
  gridHelper.position.z = 0;
  scene.add(gridHelper);
}

function createStock(): void {
  if (stockMesh) {
    scene.remove(stockMesh);
    stockMesh.geometry.dispose();
    (stockMesh.material as THREE.Material).dispose();
  }

  if (!props.showStock || !store.bounds) return;

  const bounds = store.bounds;
  const width = bounds.x_max - bounds.x_min;
  const height = bounds.y_max - bounds.y_min;
  const depth = Math.abs(bounds.z_min) + 5; // Stock thickness

  const geometry = new THREE.BoxGeometry(width, height, depth);
  const material = new THREE.MeshPhongMaterial({
    color: COLORS.stock,
    transparent: true,
    opacity: 0.2,
    side: THREE.DoubleSide,
  });

  stockMesh = new THREE.Mesh(geometry, material);
  stockMesh.name = "stock";
  stockMesh.position.set(
    (bounds.x_min + bounds.x_max) / 2,
    (bounds.y_min + bounds.y_max) / 2,
    -depth / 2
  );
  scene.add(stockMesh);
}

// ---------------------------------------------------------------------------
// Toolpath Rendering
// ---------------------------------------------------------------------------

function buildAllLines(): void {
  clearGroup(pathGroup);
  _lastProgressIdx = -1;

  if (store.segments.length === 0) return;

  // P5: Update engagement data for heatmap
  if (props.showHeatmap && !engagementReport) {
    updateEngagement();
  }

  // Build one line per segment ONCE (baseline = faded/upcoming). Playback then
  // only flips opacity on segments that cross the progress boundary, instead of
  // tearing down and rebuilding the whole scene every tick. (F-X1)
  for (let i = 0; i < store.segments.length; i++) {
    const line = createSegmentLine(store.segments[i], i);
    if (line) pathGroup.add(line);
  }

  updateSelectedSegment();
  maybeRebuildTool();
  updateToolPosition();
  createStock();
  fitCameraToScene(); // fit on every load, not only at index 0 (F-Z4)

  applyProgress(store.currentSegmentIndex);
}

/** O(Δ) progress update: only re-opacity the segments that crossed the boundary. */
function applyProgress(idx: number): void {
  const children = pathGroup.children;
  if (children.length === 0) return;
  const clamped = Math.max(-1, Math.min(idx, children.length - 1));

  if (clamped > _lastProgressIdx) {
    for (let i = _lastProgressIdx + 1; i <= clamped; i++) {
      setLineCompleted(children[i] as THREE.Line, true);
    }
  } else if (clamped < _lastProgressIdx) {
    for (let i = clamped + 1; i <= _lastProgressIdx; i++) {
      setLineCompleted(children[i] as THREE.Line, false);
    }
  }
  _lastProgressIdx = clamped;
}

function setLineCompleted(line: THREE.Line | undefined, completed: boolean): void {
  if (!line) return;
  const mat = line.material as THREE.Material & { opacity: number };
  const ud = line.userData as { completedOpacity?: number };
  mat.opacity = completed ? ud.completedOpacity ?? 0.9 : 0.15;
}

// One line per segment, baseline opacity = upcoming/faded. Segment index is
// stored in userData for raycasting; the "completed" opacity is stashed there
// so applyProgress() can flip it cheaply.
function createSegmentLine(segment: MoveSegment, segmentIndex: number): THREE.Line | null {
  const points = [
    new THREE.Vector3(segment.from_pos[0], segment.from_pos[1], segment.from_pos[2]),
    new THREE.Vector3(segment.to_pos[0], segment.to_pos[1], segment.to_pos[2]),
  ];
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const isRapid = segment.type === "rapid";
  const completedOpacity = isRapid ? 0.5 : 0.9;

  // P5: Heatmap mode — color by engagement
  if (props.showHeatmap && engagementReport) {
    const engData = engagementReport.segments[segmentIndex];
    const heatColor = engData
      ? EngagementAnalyzer.getColorInterpolatedHex(engData.engagement)
      : 0x333333;
    const material = new THREE.LineBasicMaterial({
      color: heatColor,
      transparent: true,
      opacity: 0.15,
      linewidth: 1,
    });
    const line = new THREE.Line(geometry, material);
    line.userData.segmentIndex = segmentIndex;
    line.userData.completedOpacity = isRapid ? 0.3 : 0.9;
    return line;
  }

  // Normal mode: color by move type
  let color: number;
  if (isRapid) color = COLORS.rapid;
  else if (segment.type.includes("arc")) color = COLORS.arc;
  else color = COLORS.cut;

  // Depth-based intensity (deeper = brighter)
  const zNorm = store.bounds
    ? (segment.to_pos[2] - store.bounds.z_min) / (store.bounds.z_max - store.bounds.z_min + 0.01)
    : 0.5;
  const intensity = 0.5 + (1 - zNorm) * 0.5;

  if (isRapid) {
    const dashedMaterial = new THREE.LineDashedMaterial({
      color,
      dashSize: 2,
      gapSize: 1,
      transparent: true,
      opacity: 0.15,
    });
    const line = new THREE.Line(geometry, dashedMaterial);
    line.computeLineDistances();
    line.userData.segmentIndex = segmentIndex;
    line.userData.completedOpacity = completedOpacity;
    return line;
  }

  const material = new THREE.LineBasicMaterial({
    color: new THREE.Color(color).multiplyScalar(intensity),
    transparent: true,
    opacity: 0.15,
    linewidth: 1, // Note: linewidth > 1 only works on some platforms
  });
  const line = new THREE.Line(geometry, material);
  line.userData.segmentIndex = segmentIndex;
  line.userData.completedOpacity = completedOpacity;
  return line;
}

/** Resize the cutter cylinder when the active tool changes (F-Z3). */
function maybeRebuildTool(): void {
  const toolNum = store.currentSegment?.tool_number ?? 1;
  if (toolNum === _currentToolNumber) return;
  _currentToolNumber = toolNum;

  const dims = props.toolTable?.[toolNum];
  if (!dims) return; // no tool table → keep the default cylinder

  if (toolMesh) {
    scene.remove(toolMesh);
    toolMesh.geometry.dispose();
    (toolMesh.material as THREE.Material).dispose();
  }
  _currentToolLength = dims.length ?? props.toolLength;
  const geometry = new THREE.CylinderGeometry(
    dims.diameter / 2,
    dims.diameter / 2,
    _currentToolLength,
    16,
  );
  const material = new THREE.MeshPhongMaterial({
    color: COLORS.tool,
    shininess: 80,
    transparent: true,
    opacity: 0.9,
  });
  toolMesh = new THREE.Mesh(geometry, material);
  toolMesh.name = "tool";
  toolMesh.rotation.x = Math.PI / 2;
  scene.add(toolMesh);
}

function updateToolPosition(): void {
  if (!toolMesh) return;

  const pos = store.toolPosition;
  toolMesh.position.set(pos[0], pos[1], pos[2] + _currentToolLength / 2);
}

// ---------------------------------------------------------------------------
// P5: Selection Handling
// ---------------------------------------------------------------------------

function updateSelectedSegment(): void {
  // Remove old selected line
  if (selectedLine) {
    scene.remove(selectedLine);
    selectedLine.geometry.dispose();
    (selectedLine.material as THREE.Material).dispose();
    selectedLine = null;
  }

  const idx = store.selectedSegmentIndex;
  if (idx === null || idx < 0 || idx >= store.segments.length) return;

  const segment = store.segments[idx];
  const points = [
    new THREE.Vector3(segment.from_pos[0], segment.from_pos[1], segment.from_pos[2]),
    new THREE.Vector3(segment.to_pos[0], segment.to_pos[1], segment.to_pos[2]),
  ];

  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({
    color: COLORS.selected,
    linewidth: 3,
    transparent: false,
  });

  selectedLine = new THREE.Line(geometry, material);
  selectedLine.name = "selectedSegment";
  selectedLine.renderOrder = 999; // Render on top
  scene.add(selectedLine);
}

function onCanvasClick(event: MouseEvent): void {
  if (!containerRef.value || !canvasRef.value) return;

  const rect = canvasRef.value.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);

  // Raycast against the single path group (one line per segment).
  const intersects = raycaster.intersectObjects(pathGroup.children, false);

  // P5: Handle measure mode
  if (store.measureMode) {
    let measurePoint: Point3D;

    if (intersects.length > 0) {
      // Snap to intersection point
      const point = intersects[0].point;
      measurePoint = { x: point.x, y: point.y, z: point.z };
    } else {
      // Try to find a point on the XY plane (Z=0)
      const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
      const intersectPoint = new THREE.Vector3();
      raycaster.ray.intersectPlane(plane, intersectPoint);
      if (intersectPoint) {
        measurePoint = { x: intersectPoint.x, y: intersectPoint.y, z: 0 };
      } else {
        return;
      }
    }

    store.addMeasurePoint(measurePoint);
    buildMeasurements();
    return;
  }

  if (intersects.length > 0) {
    const hit = intersects[0].object;
    const segmentIndex = hit.userData.segmentIndex;
    if (typeof segmentIndex === "number") {
      store.selectSegment(segmentIndex);
    }
  } else {
    store.selectSegment(null);
  }
}

function clearGroup(group: THREE.Group): void {
  while (group.children.length > 0) {
    const child = group.children[0];
    if (child instanceof THREE.Line) {
      child.geometry.dispose();
      (child.material as THREE.Material).dispose();
    }
    if (child instanceof THREE.Mesh) {
      child.geometry.dispose();
      (child.material as THREE.Material).dispose();
    }
    group.remove(child);
  }
}

// ---------------------------------------------------------------------------
// P5: Measurement Rendering
// ---------------------------------------------------------------------------

function initMeasurementGroup(): void {
  measurementGroup = new THREE.Group();
  measurementGroup.name = "measurements";
  scene.add(measurementGroup);
}

function createMeasurementSphere(point: Point3D, color: number): THREE.Mesh {
  const geometry = new THREE.SphereGeometry(2, 16, 16);
  const material = new THREE.MeshBasicMaterial({ color });
  const sphere = new THREE.Mesh(geometry, material);
  sphere.position.set(point.x, point.y, point.z);
  return sphere;
}

function createMeasurementLine(start: Point3D, end: Point3D, color: number): THREE.Line {
  const points = [
    new THREE.Vector3(start.x, start.y, start.z),
    new THREE.Vector3(end.x, end.y, end.z),
  ];
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineDashedMaterial({
    color,
    dashSize: 3,
    gapSize: 2,
    linewidth: 2,
  });
  const line = new THREE.Line(geometry, material);
  line.computeLineDistances();
  return line;
}

function buildMeasurements(): void {
  clearGroup(measurementGroup);

  // Draw completed measurements
  for (const m of store.measurements) {
    // Start sphere
    const startSphere = createMeasurementSphere(m.start, MEASUREMENT_COLORS.pointHex);
    measurementGroup.add(startSphere);

    // End sphere
    const endSphere = createMeasurementSphere(m.end, MEASUREMENT_COLORS.pointHex);
    measurementGroup.add(endSphere);

    // Line
    const line = createMeasurementLine(m.start, m.end, MEASUREMENT_COLORS.lineHex);
    measurementGroup.add(line);

    // Label sprite (text in 3D)
    const label = createMeasurementLabel(m);
    measurementGroup.add(label);
  }

  // Draw pending measurement
  updatePendingMeasurement();
}

function createMeasurementLabel(m: Measurement): THREE.Sprite {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  canvas.width = 128;
  canvas.height = 32;

  // Draw background
  ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw text
  const label = store.measureTool.formatDistance(m.distance);
  ctx.font = "bold 14px Arial";
  ctx.fillStyle = "#ffffff";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, canvas.width / 2, canvas.height / 2);

  // Create sprite
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture });
  const sprite = new THREE.Sprite(material);

  // Position at midpoint
  sprite.position.set(
    (m.start.x + m.end.x) / 2,
    (m.start.y + m.end.y) / 2,
    (m.start.z + m.end.z) / 2 + 5
  );
  sprite.scale.set(20, 5, 1);

  return sprite;
}

function updatePendingMeasurement(): void {
  // Clear pending objects
  if (pendingMeasureLine) {
    scene.remove(pendingMeasureLine);
    pendingMeasureLine.geometry.dispose();
    (pendingMeasureLine.material as THREE.Material).dispose();
    pendingMeasureLine = null;
  }
  if (pendingMeasureStartSphere) {
    scene.remove(pendingMeasureStartSphere);
    pendingMeasureStartSphere.geometry.dispose();
    (pendingMeasureStartSphere.material as THREE.Material).dispose();
    pendingMeasureStartSphere = null;
  }

  const pendingStart = store.pendingMeasureStart;
  if (!pendingStart) return;

  // Draw pending start sphere
  pendingMeasureStartSphere = createMeasurementSphere(pendingStart, MEASUREMENT_COLORS.pendingHex);
  scene.add(pendingMeasureStartSphere);
}

// ---------------------------------------------------------------------------
// Camera
// ---------------------------------------------------------------------------

function fitCameraToScene(): void {
  if (!store.bounds) return;

  const bounds = store.bounds;
  const centerX = (bounds.x_min + bounds.x_max) / 2;
  const centerY = (bounds.y_min + bounds.y_max) / 2;
  const centerZ = (bounds.z_min + bounds.z_max) / 2;

  const sizeX = bounds.x_max - bounds.x_min;
  const sizeY = bounds.y_max - bounds.y_min;
  const sizeZ = bounds.z_max - bounds.z_min;
  const maxSize = Math.max(sizeX, sizeY, sizeZ);

  // Position camera
  const distance = maxSize * 2;
  camera.position.set(
    centerX + distance * 0.7,
    centerY + distance * 0.7,
    centerZ + distance * 0.7
  );
  camera.lookAt(centerX, centerY, centerZ);

  // Update controls target
  controls.target.set(centerX, centerY, centerZ);
  controls.update();

  // Update grid position
  if (gridHelper) {
    gridHelper.position.set(centerX, centerY, 0);
    const gridSize = Math.ceil(maxSize / 10) * 10 + 40;
    scene.remove(gridHelper);
    gridHelper = new THREE.GridHelper(gridSize, gridSize / 10, COLORS.grid, COLORS.grid);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.set(centerX, centerY, 0);
    scene.add(gridHelper);
  }
}

// ---------------------------------------------------------------------------
// Animation Loop
// ---------------------------------------------------------------------------

function animate(): void {
  animationFrameId = requestAnimationFrame(animate);

  controls.update();
  renderer.render(scene, camera);
}

// ---------------------------------------------------------------------------
// Resize Handling
// ---------------------------------------------------------------------------

function handleResize(): void {
  if (!containerRef.value) return;

  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

// ---------------------------------------------------------------------------
// View Controls (exposed for parent)
// ---------------------------------------------------------------------------

function resetView(): void {
  fitCameraToScene();
}

function setViewTop(): void {
  if (!store.bounds) return;
  const bounds = store.bounds;
  const centerX = (bounds.x_min + bounds.x_max) / 2;
  const centerY = (bounds.y_min + bounds.y_max) / 2;
  const maxSize = Math.max(bounds.x_max - bounds.x_min, bounds.y_max - bounds.y_min);

  camera.position.set(centerX, centerY, maxSize * 1.5);
  camera.lookAt(centerX, centerY, 0);
  controls.target.set(centerX, centerY, 0);
  controls.update();
}

function setViewFront(): void {
  if (!store.bounds) return;
  const bounds = store.bounds;
  const centerX = (bounds.x_min + bounds.x_max) / 2;
  const centerZ = (bounds.z_min + bounds.z_max) / 2;
  const maxSize = Math.max(bounds.x_max - bounds.x_min, Math.abs(bounds.z_min));

  camera.position.set(centerX, -maxSize * 1.5, centerZ);
  camera.lookAt(centerX, 0, centerZ);
  controls.target.set(centerX, 0, centerZ);
  controls.update();
}

function setViewSide(): void {
  if (!store.bounds) return;
  const bounds = store.bounds;
  const centerY = (bounds.y_min + bounds.y_max) / 2;
  const centerZ = (bounds.z_min + bounds.z_max) / 2;
  const maxSize = Math.max(bounds.y_max - bounds.y_min, Math.abs(bounds.z_min));

  camera.position.set(-maxSize * 1.5, centerY, centerZ);
  camera.lookAt(0, centerY, centerZ);
  controls.target.set(0, centerY, centerZ);
  controls.update();
}

// Expose methods for parent component
defineExpose({
  resetView,
  setViewTop,
  setViewFront,
  setViewSide,
});

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  initThree();
  window.addEventListener("resize", handleResize);

  // Build initial toolpath if segments exist
  if (store.segments.length > 0) {
    buildAllLines();
  }
});

onUnmounted(() => {
  cancelAnimationFrame(animationFrameId);
  window.removeEventListener("resize", handleResize);

  // Cleanup Three.js
  if (renderer) {
    renderer.dispose();
  }
  if (controls) {
    controls.dispose();
  }
  clearGroup(pathGroup);
});

// Watch playback position — O(Δ) progress update, NOT a scene rebuild (F-X1)
watch(
  () => store.currentSegmentIndex,
  (idx) => {
    applyProgress(idx);
  }
);

// Watch for a new toolpath loaded — rebuild the line set once
watch(
  () => store.segments.length,
  () => {
    buildAllLines();
  }
);

// Watch tool changes — resize the cutter if a tool table is provided (F-Z3)
watch(
  () => store.currentSegment?.tool_number,
  () => {
    maybeRebuildTool();
    updateToolPosition();
  }
);

// Watch tool position for smooth updates during playback
watch(
  () => store.toolPosition,
  () => {
    updateToolPosition();
  },
  { deep: true }
);

// P5: Watch for selection changes
watch(
  () => store.selectedSegmentIndex,
  () => {
    updateSelectedSegment();
  }
);

// P5: Watch for heatmap toggle
watch(
  () => props.showHeatmap,
  (show) => {
    if (show) {
      updateEngagement();
    }
    buildAllLines();
  }
);

// P5: Watch for measurement changes
watch(
  () => [store.measurements, store.pendingMeasureStart],
  () => {
    buildMeasurements();
  },
  { deep: true }
);
</script>

<template>
  <div
    ref="containerRef"
    class="toolpath-canvas-3d"
  >
    <canvas
      ref="canvasRef"
      @click="onCanvasClick"
    />

    <!-- View controls overlay -->
    <div class="view-controls">
      <button
        title="Reset View"
        @click="resetView"
      >
        ⟲
      </button>
      <button
        title="Top View"
        @click="setViewTop"
      >
        ⬆
      </button>
      <button
        title="Front View"
        @click="setViewFront"
      >
        ◯
      </button>
      <button
        title="Side View"
        @click="setViewSide"
      >
        ◐
      </button>
    </div>

    <!-- Legend (normal mode) -->
    <div
      v-if="!showHeatmap"
      class="legend"
    >
      <span class="legend-item rapid">
        <span class="swatch" />
        Rapid
      </span>
      <span class="legend-item cut">
        <span class="swatch" />
        Cut
      </span>
      <span class="legend-item arc">
        <span class="swatch" />
        Arc
      </span>
    </div>

    <!-- P5: Heatmap legend -->
    <div
      v-if="showHeatmap"
      class="heatmap-legend"
    >
      <span class="legend-title">Engagement</span>
      <div class="gradient-bar" />
      <div class="gradient-labels">
        <span>Low</span>
        <span>High</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolpath-canvas-3d {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  overflow: hidden;
}

.toolpath-canvas-3d canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.view-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.view-controls button {
  width: 28px;
  height: 28px;
  background: rgba(30, 30, 46, 0.8);
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ccc;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.view-controls button:hover {
  background: #33334a;
  color: #fff;
}

.legend {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 12px;
  padding: 6px 10px;
  background: rgba(30, 30, 46, 0.8);
  border-radius: 4px;
  font-size: 11px;
  color: #aaa;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-item .swatch {
  width: 12px;
  height: 3px;
  border-radius: 1px;
}

.legend-item.rapid .swatch {
  background: #999999;
  border-style: dashed;
}

.legend-item.cut .swatch {
  background: #4a90d9;
}

.legend-item.arc .swatch {
  background: #2ecc71;
}

/* P5: Heatmap legend */
.heatmap-legend {
  position: absolute;
  bottom: 10px;
  left: 10px;
  padding: 8px 12px;
  background: rgba(30, 30, 46, 0.9);
  border-radius: 4px;
  font-size: 11px;
  color: #aaa;
}

.legend-title {
  display: block;
  margin-bottom: 6px;
  color: #888;
  font-weight: 600;
}

.gradient-bar {
  width: 100px;
  height: 10px;
  border-radius: 2px;
  background: linear-gradient(
    to right,
    #333333 0%,
    #1a4a9e 20%,
    #2ecc71 40%,
    #f1c40f 60%,
    #e67e22 80%,
    #e74c3c 100%
  );
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 9px;
  color: #666;
}
</style>
