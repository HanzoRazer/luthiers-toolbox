"""Patch WoodGradingView.vue for agentic emissions."""
import os

path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "packages",
    "client",
    "src",
    "views",
    "ai",
    "WoodGradingView.vue",
)

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports
old_import = 'import { ref } from "vue"'
new_import = """import { ref, onMounted } from "vue"
import { useAgenticEvents } from '@/composables/useAgenticEvents'

// E-1/E-4: Agentic Spine event emission
const { emitViewRendered, emitAnalysisCompleted, emitAnalysisFailed } = useAgenticEvents()

// E-1/E-4: Emit view_rendered on mount
onMounted(() => {
  emitViewRendered('wood_grading')
})"""

content = content.replace(old_import, new_import, 1)

# Add analysis_completed after successful analysis
old_success = """    analysisResult.value = {
      observations: data.observations,
      grain_spacing_estimate: data.grain_spacing_estimate,
      grain_straightness: data.grain_straightness,
      figure_type: data.figure_type,
      color_uniformity: data.color_uniformity,
      surface_anomalies: data.surface_anomalies || [],
      confidence: data.confidence,
    }
  } catch (err) {"""

new_success = """    analysisResult.value = {
      observations: data.observations,
      grain_spacing_estimate: data.grain_spacing_estimate,
      grain_straightness: data.grain_straightness,
      figure_type: data.figure_type,
      color_uniformity: data.color_uniformity,
      surface_anomalies: data.surface_anomalies || [],
      confidence: data.confidence,
    }

    // E-4: Emit analysis_completed for agentic spine
    emitAnalysisCompleted(['wood_visual_assessment_v1'])
  } catch (err) {"""

content = content.replace(old_success, new_success, 1)

# Add analysis_failed in catch block
old_catch = """  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Analysis failed"
    analysisResult.value = null
  } finally {"""

new_catch = """  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Analysis failed"
    analysisResult.value = null
    // E-4: Emit analysis_failed for agentic spine
    emitAnalysisFailed(err instanceof Error ? err.message : "Analysis failed", 'WOOD_GRADING_ERROR')
  } finally {"""

content = content.replace(old_catch, new_catch, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated WoodGradingView.vue")
