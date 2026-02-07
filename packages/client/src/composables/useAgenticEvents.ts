/**
 * Agentic Event Emission Composable
 *
 * Provides a simple API for Vue components to emit AgentEventV1 events
 * that feed into the M1 directive pipeline.
 *
 * Usage:
 *   const { emitViewRendered, emitAnalysisCompleted, emitUserAction } = useAgenticEvents();
 *
 *   // When a view renders
 *   emitViewRendered('spectrum', 'main');
 *
 *   // When analysis completes
 *   emitAnalysisCompleted(['wolf_candidates_v1']);
 *
 *   // Custom user action
 *   emitUserAction('parameter_changed', { param: 'frequency', value: 440 });
 */

import { useAgenticDirectiveStore } from "@/stores/agenticDirectiveStore";

export function useAgenticEvents() {
  const store = useAgenticDirectiveStore();

  /**
   * Emit when a view/panel renders and becomes visible to the user.
   * Triggers FIRST_SIGNAL moment detection.
   */
  function emitViewRendered(panelId: string, traceId?: string) {
    return store.emitEvent("user_action", {
      action: "view_rendered",
      panel_id: panelId,
      trace_id: traceId,
    });
  }

  /**
   * Emit when an analysis completes successfully.
   * Triggers FIRST_SIGNAL moment detection.
   */
  function emitAnalysisCompleted(artifactsCreated: string[]) {
    return store.emitEvent(
      "analysis_completed",
      { artifacts_created: artifactsCreated },
      "analyzer"
    );
  }

  /**
   * Emit when an analysis fails.
   * Triggers ERROR moment detection.
   */
  function emitAnalysisFailed(error: string, code?: string) {
    return store.emitEvent(
      "analysis_failed",
      { error, code },
      "analyzer"
    );
  }

  /**
   * Emit when an artifact is created with confidence.
   * Triggers FINDING moment detection if confidence_max >= 0.6.
   */
  function emitArtifactCreated(
    schema: string,
    confidenceMax: number,
    metadata?: Record<string, unknown>
  ) {
    return store.emitEvent(
      "artifact_created",
      {
        schema,
        artifact_type: schema,
        confidence_max: confidenceMax,
        ...metadata,
      },
      "analyzer"
    );
  }

  /**
   * Emit a generic user action.
   */
  function emitUserAction(action: string, payload?: Record<string, unknown>) {
    return store.emitEvent("user_action", { action, ...payload });
  }

  /**
   * Emit when user hovers over an element (for HESITATION detection).
   */
  function emitHover(elementId: string) {
    return store.emitEvent("user_action", {
      action: "hover",
      element_id: elementId,
    });
  }

  /**
   * Emit when user undoes an action (for OVERLOAD detection).
   */
  function emitUndo(context?: string) {
    return store.emitEvent("user_action", {
      action: "undo",
      context,
    });
  }

  /**
   * Emit when user changes a parameter (suppresses HESITATION).
   */
  function emitParameterChanged(param: string, value: unknown) {
    return store.emitEvent("user_action", {
      action: "parameter_changed",
      param,
      value,
    });
  }

  /**
   * Emit idle timeout event (for HESITATION detection).
   * Typically called by an idle timer component.
   */
  function emitIdleTimeout(idleSeconds: number) {
    return store.emitEvent("idle_timeout", { idle_seconds: idleSeconds });
  }

  /**
   * Emit when a decision is required from the user.
   * Triggers DECISION_REQUIRED moment.
   */
  function emitDecisionRequired(
    decisionType: string,
    options: string[]
  ) {
    return store.emitEvent("decision_required", {
      decision_type: decisionType,
      options,
    });
  }

  /**
   * Emit tool rendered event.
   */
  function emitToolRendered(toolId: string) {
    return store.emitEvent("tool_rendered", { tool_id: toolId });
  }

  /**
   * Emit tool closed event.
   */
  function emitToolClosed(toolId: string) {
    return store.emitEvent("tool_closed", { tool_id: toolId });
  }

  return {
    // Core emitters
    emitViewRendered,
    emitAnalysisCompleted,
    emitAnalysisFailed,
    emitArtifactCreated,
    emitUserAction,

    // Specialized emitters
    emitHover,
    emitUndo,
    emitParameterChanged,
    emitIdleTimeout,
    emitDecisionRequired,
    emitToolRendered,
    emitToolClosed,

    // Direct access to store (for advanced usage)
    store,
  };
}
