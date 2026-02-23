/**
 * useRosetteDesignerState - State management for Rosette Designer
 */
import { ref, computed } from "vue";

export interface RosetteSegment {
  id: string;
  type: "strip" | "circle" | "arc";
  points: Array<{ x: number; y: number }>;
  material: string;
  angle?: number;
}

export interface RosetteDimensions {
  soundholeDiameter: number;
  rosetteWidth: number;
  channelDepth: number;
  symmetryCount: number;
}

export interface TemplateStrip {
  material: string;
  width?: number;
  angle?: number;
  shape?: string;
}

export interface RosetteTemplate {
  name: string;
  segments: number;
  strips: TemplateStrip[];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AnyTemplate = any;

export function useRosetteDesignerState() {
  // Design-focused state
  const dimensions = ref<RosetteDimensions>({
    soundholeDiameter: 100,
    rosetteWidth: 20,
    channelDepth: 1.5,
    symmetryCount: 16,
  });

  const showGrid = ref(true);
  const selectedTemplate = ref<string | undefined>(undefined);
  const selectedMaterial = ref("maple");
  const currentStripWidth = ref(1.0);
  const segments = ref<RosetteSegment[]>([]);
  const status = ref("");

  const statusClass = computed(() => {
    if (status.value.startsWith("✅")) return "success";
    if (status.value.startsWith("❌")) return "error";
    return "info";
  });

  function handleSegmentsChanged(newSegments: RosetteSegment[]) {
    segments.value = newSegments;
  }

  function handleTemplateSelected(templateId: string) {
    selectedTemplate.value = templateId;
  }

  function handleMaterialSelected(materialId: string) {
    selectedMaterial.value = materialId;
  }

  /**
   * Apply a template to generate segments
   */
  function applyTemplate(template: AnyTemplate) {
    status.value = `✅ Applied ${template.name} template`;
    dimensions.value.symmetryCount = template.segments;

    // Generate segments from template strips
    const soundholeDiameter = dimensions.value.soundholeDiameter;
    const rosetteWidth = dimensions.value.rosetteWidth;
    const innerRadius = soundholeDiameter / 2;
    const outerRadius = innerRadius + rosetteWidth;

    const generatedSegments: RosetteSegment[] = [];

    template.strips.forEach((strip, idx) => {
      const segmentAngle = (2 * Math.PI) / template.segments;

      for (let i = 0; i < template.segments; i++) {
        const startAngle =
          i * segmentAngle + ((strip.angle || 0) * Math.PI) / 180;
        const endAngle = startAngle + segmentAngle * (strip.width || 1);

        // Create points for this segment (arc approximation)
        const points: Array<{ x: number; y: number }> = [];
        const steps = 8; // Points per arc

        // Outer arc
        for (let s = 0; s <= steps; s++) {
          const angle = startAngle + ((endAngle - startAngle) * s) / steps;
          points.push({
            x: 300 + outerRadius * Math.cos(angle), // 300 = canvas center
            y: 300 + outerRadius * Math.sin(angle),
          });
        }

        // Inner arc (reverse)
        for (let s = steps; s >= 0; s--) {
          const angle = startAngle + ((endAngle - startAngle) * s) / steps;
          points.push({
            x: 300 + innerRadius * Math.cos(angle),
            y: 300 + innerRadius * Math.sin(angle),
          });
        }

        generatedSegments.push({
          id: `seg-${idx}-${i}`,
          type: "strip", // normalized from template shape
          points,
          material: strip.material,
          angle: strip.angle || 0,
        });
      }
    });

    segments.value = generatedSegments;
    handleSegmentsChanged(generatedSegments);
  }

  return {
    dimensions,
    showGrid,
    selectedTemplate,
    selectedMaterial,
    currentStripWidth,
    segments,
    status,
    statusClass,
    handleSegmentsChanged,
    handleTemplateSelected,
    handleMaterialSelected,
    applyTemplate,
  };
}
