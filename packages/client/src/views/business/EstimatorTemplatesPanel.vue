<script setup lang="ts">
/**
 * EstimatorTemplatesPanel - Quick-start instrument templates
 *
 * Features:
 * - Pre-configured templates for common builds
 * - One-click load to form
 * - Complexity hints and typical costs
 */
import { computed } from "vue";
import type {
  EstimateRequest,
  InstrumentType,
  BuilderExperience,
  BodyComplexity,
  BindingComplexity,
  NeckComplexity,
  FretboardInlay,
  FinishType,
  RosetteComplexity,
} from "@/types/businessEstimator";

const emit = defineEmits<{
  loadTemplate: [request: EstimateRequest];
}>();

// ============================================================================
// TYPES
// ============================================================================

interface Template {
  id: string;
  name: string;
  description: string;
  category: "acoustic" | "electric" | "bass" | "other";
  complexity: "beginner" | "intermediate" | "advanced";
  typicalHours: string;
  typicalCost: string;
  request: EstimateRequest;
}

// ============================================================================
// TEMPLATES
// ============================================================================

const templates: Template[] = [
  // Acoustic
  {
    id: "dreadnought_basic",
    name: "Dreadnought Basic",
    description: "Entry-level dreadnought with oil finish",
    category: "acoustic",
    complexity: "beginner",
    typicalHours: "80-100",
    typicalCost: "$800-1200",
    request: {
      instrument_type: "acoustic_dreadnought" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "none" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "oil" as FinishType,
      rosette_complexity: "simple_rings" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 45,
      include_materials: true,
    },
  },
  {
    id: "dreadnought_pro",
    name: "Dreadnought Pro",
    description: "Full-featured with binding and nitro finish",
    category: "acoustic",
    complexity: "advanced",
    typicalHours: "140-180",
    typicalCost: "$2500-4000",
    request: {
      instrument_type: "acoustic_dreadnought" as InstrumentType,
      builder_experience: "experienced" as BuilderExperience,
      body_complexity: ["cutaway_venetian", "arm_bevel"] as BodyComplexity[],
      binding_body_complexity: "multiple" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "blocks" as FretboardInlay,
      finish_type: "nitro_burst" as FinishType,
      rosette_complexity: "mosaic" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 65,
      include_materials: true,
    },
  },
  {
    id: "om_standard",
    name: "OM Standard",
    description: "Orchestra model with French polish",
    category: "acoustic",
    complexity: "intermediate",
    typicalHours: "100-130",
    typicalCost: "$1500-2200",
    request: {
      instrument_type: "acoustic_om" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "single" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "shellac_french_polish" as FinishType,
      rosette_complexity: "simple_rings" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 50,
      include_materials: true,
    },
  },
  {
    id: "parlor_vintage",
    name: "Parlor Vintage",
    description: "Small body with vintage appointments",
    category: "acoustic",
    complexity: "intermediate",
    typicalHours: "90-120",
    typicalCost: "$1200-1800",
    request: {
      instrument_type: "acoustic_parlor" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "herringbone" as BindingComplexity,
      neck_complexity: "volute" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "nitro_vintage" as FinishType,
      rosette_complexity: "mosaic" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 50,
      include_materials: true,
    },
  },
  {
    id: "classical_student",
    name: "Classical Student",
    description: "Simple classical for learning",
    category: "acoustic",
    complexity: "beginner",
    typicalHours: "70-90",
    typicalCost: "$600-900",
    request: {
      instrument_type: "classical" as InstrumentType,
      builder_experience: "beginner" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "none" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "none" as FretboardInlay,
      finish_type: "shellac_wipe" as FinishType,
      rosette_complexity: "simple_rings" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 40,
      include_materials: true,
    },
  },

  // Electric
  {
    id: "solidbody_basic",
    name: "Solid Body Basic",
    description: "Simple solid body with poly finish",
    category: "electric",
    complexity: "beginner",
    typicalHours: "50-70",
    typicalCost: "$500-800",
    request: {
      instrument_type: "electric_solid" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "none" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "poly_solid" as FinishType,
      rosette_complexity: "none" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 45,
      include_materials: true,
    },
  },
  {
    id: "solidbody_pro",
    name: "Solid Body Pro",
    description: "Carved top with nitro burst",
    category: "electric",
    complexity: "advanced",
    typicalHours: "90-120",
    typicalCost: "$1800-2800",
    request: {
      instrument_type: "electric_solid" as InstrumentType,
      builder_experience: "experienced" as BuilderExperience,
      body_complexity: ["carved_top", "arm_bevel", "tummy_cut"] as BodyComplexity[],
      binding_body_complexity: "single" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "trapezoids" as FretboardInlay,
      finish_type: "nitro_burst" as FinishType,
      rosette_complexity: "none" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 60,
      include_materials: true,
    },
  },
  {
    id: "semi_hollow",
    name: "Semi-Hollow",
    description: "Chambered body with binding",
    category: "electric",
    complexity: "advanced",
    typicalHours: "100-140",
    typicalCost: "$2000-3200",
    request: {
      instrument_type: "electric_semi_hollow" as InstrumentType,
      builder_experience: "experienced" as BuilderExperience,
      body_complexity: ["cutaway_florentine"] as BodyComplexity[],
      binding_body_complexity: "multiple" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "blocks" as FretboardInlay,
      finish_type: "nitro_burst" as FinishType,
      rosette_complexity: "none" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 60,
      include_materials: true,
    },
  },

  // Bass
  {
    id: "bass_4_basic",
    name: "4-String Bass Basic",
    description: "Standard 4-string with simple finish",
    category: "bass",
    complexity: "beginner",
    typicalHours: "60-80",
    typicalCost: "$600-950",
    request: {
      instrument_type: "bass_4" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "none" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "oil" as FinishType,
      rosette_complexity: "none" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 45,
      include_materials: true,
    },
  },
  {
    id: "bass_5_pro",
    name: "5-String Bass Pro",
    description: "Extended range with multi-scale neck",
    category: "bass",
    complexity: "advanced",
    typicalHours: "100-140",
    typicalCost: "$2200-3500",
    request: {
      instrument_type: "bass_5" as InstrumentType,
      builder_experience: "experienced" as BuilderExperience,
      body_complexity: ["arm_bevel", "tummy_cut"] as BodyComplexity[],
      binding_body_complexity: "none" as BindingComplexity,
      neck_complexity: "multi_scale" as NeckComplexity,
      fretboard_inlay: "blocks" as FretboardInlay,
      finish_type: "oil" as FinishType,
      rosette_complexity: "none" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 60,
      include_materials: true,
    },
  },

  // Other
  {
    id: "ukulele_concert",
    name: "Concert Ukulele",
    description: "Concert size with simple appointments",
    category: "other",
    complexity: "beginner",
    typicalHours: "30-45",
    typicalCost: "$300-500",
    request: {
      instrument_type: "ukulele" as InstrumentType,
      builder_experience: "intermediate" as BuilderExperience,
      body_complexity: ["standard"] as BodyComplexity[],
      binding_body_complexity: "single" as BindingComplexity,
      neck_complexity: "standard" as NeckComplexity,
      fretboard_inlay: "dots" as FretboardInlay,
      finish_type: "shellac_wipe" as FinishType,
      rosette_complexity: "simple_rings" as RosetteComplexity,
      batch_size: 1,
      hourly_rate: 40,
      include_materials: true,
    },
  },
];

// ============================================================================
// COMPUTED
// ============================================================================

const categories = computed(() => {
  const order = ["acoustic", "electric", "bass", "other"];
  const labels: Record<string, string> = {
    acoustic: "Acoustic Guitars",
    electric: "Electric Guitars",
    bass: "Bass Guitars",
    other: "Other Instruments",
  };

  return order.map((cat) => ({
    id: cat,
    label: labels[cat],
    templates: templates.filter((t) => t.category === cat),
  }));
});

// ============================================================================
// ACTIONS
// ============================================================================

function loadTemplate(template: Template): void {
  emit("loadTemplate", { ...template.request });
}

function getComplexityColor(complexity: string): string {
  const colors: Record<string, string> = {
    beginner: "#60e0a0",
    intermediate: "#f0c060",
    advanced: "#f06060",
  };
  return colors[complexity] || "#8090b0";
}
</script>

<template>
  <div class="templates-panel">
    <header class="panel-header">
      <h3>Quick Start Templates</h3>
    </header>

    <p class="instructions">
      Select a template to pre-fill the form with typical values.
    </p>

    <div class="categories">
      <div
        v-for="category in categories"
        :key="category.id"
        class="category-section"
      >
        <h4 class="category-title">{{ category.label }}</h4>

        <div class="template-grid">
          <div
            v-for="template in category.templates"
            :key="template.id"
            class="template-card"
            @click="loadTemplate(template)"
          >
            <div class="template-header">
              <div class="template-name">{{ template.name }}</div>
              <div
                class="complexity-badge"
                :style="{ color: getComplexityColor(template.complexity) }"
              >
                {{ template.complexity }}
              </div>
            </div>
            <div class="template-description">{{ template.description }}</div>
            <div class="template-stats">
              <span class="stat">
                <span class="stat-icon">⏱</span>
                {{ template.typicalHours }}h
              </span>
              <span class="stat">
                <span class="stat-icon">$</span>
                {{ template.typicalCost }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.templates-panel {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.panel-header {
  margin-bottom: 8px;
}

.panel-header h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0;
}

.instructions {
  font-size: 11px;
  color: #506090;
  margin: 0 0 16px;
}

/* Categories */
.categories {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-section {
  /* spacing handled by gap */
}

.category-title {
  font-size: 9px;
  letter-spacing: 1px;
  color: #6080b0;
  text-transform: uppercase;
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #1e2438;
}

/* Template Grid */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.template-card {
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.template-card:hover {
  border-color: #4080f0;
  transform: translateY(-1px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.template-name {
  font-size: 12px;
  font-weight: 600;
  color: #c0c8e0;
}

.complexity-badge {
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.template-description {
  font-size: 10px;
  color: #506090;
  margin-bottom: 10px;
  line-height: 1.4;
}

.template-stats {
  display: flex;
  gap: 12px;
}

.stat {
  font-size: 10px;
  color: #8090b0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 9px;
  color: #506090;
}
</style>
