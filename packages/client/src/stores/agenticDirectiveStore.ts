/**
 * Agentic Directive Store — Per-session event collection and M1 directive management.
 *
 * This store:
 * 1. Collects AgentEventV1 events emitted by UI components
 * 2. Periodically runs moment detection + policy decision
 * 3. Exposes the latest directive for the Coach Bubble UI
 * 4. Handles feedback events (helpful/too_much/dismiss)
 *
 * Flag-gated by VITE_AGENTIC_MODE environment variable:
 * - M0: Shadow mode (collect events, compute decisions, but don't render)
 * - M1: Advisory mode (render directives in Coach Bubble)
 * - M2: Actuated mode (issue analyzer commands - not implemented yet)
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";

// --- Types ---

export interface AgentEventSource {
  repo: string;
  component: string;
  version: string;
}

export interface AgentEventV1 {
  event_id: string;
  event_type: string;
  source: AgentEventSource;
  payload: Record<string, unknown>;
  privacy_layer: number;
  occurred_at: string;
  schema_version: string;
  session: { session_id: string };
}

export interface AttentionDirective {
  action: "INSPECT" | "REVIEW" | "COMPARE" | "DECIDE" | "CONFIRM" | "NONE";
  title: string;
  detail: string;
}

export interface PolicyDecision {
  attention_action: string;
  emit_directive: boolean;
  directive: AttentionDirective;
  diagnostic: {
    rule_id: string;
    max_directives?: number;
    would_have_emitted?: AttentionDirective;
    [key: string]: unknown;
  };
}

export interface UWSMSnapshot {
  dimensions: {
    guidance_density: { value: string };
    initiative_tolerance: { value: string };
    cognitive_load_sensitivity: { value: string };
    expertise_proxy: { value: string };
    comparison_preference: { value: string };
    visual_density_tolerance: { value: string };
    exploration_vs_confirmation: { value: string };
  };
}

export type AgenticMode = "M0" | "M1" | "M2";

// --- Constants ---

const DEFAULT_UWSM: UWSMSnapshot = {
  dimensions: {
    guidance_density: { value: "medium" },
    initiative_tolerance: { value: "shared_control" },
    cognitive_load_sensitivity: { value: "medium" },
    expertise_proxy: { value: "intermediate" },
    comparison_preference: { value: "side_by_side" },
    visual_density_tolerance: { value: "moderate" },
    exploration_vs_confirmation: { value: "balanced" },
  },
};

const MOMENT_PRIORITY: Record<string, number> = {
  ERROR: 1,
  OVERLOAD: 2,
  DECISION_REQUIRED: 3,
  FINDING: 4,
  HESITATION: 5,
  FIRST_SIGNAL: 6,
};

// --- Local spine implementation (matches backend) ---

function detectMoments(
  events: AgentEventV1[]
): { moment: string; confidence: number; trigger_events: string[] }[] {
  if (!events.length) return [];

  const evs = [...events].sort((a, b) =>
    a.occurred_at.localeCompare(b.occurred_at)
  );

  const detected: [string, number, string[]][] = [];

  // ERROR
  for (const e of evs) {
    if (e.event_type === "analysis_failed" || e.event_type === "system_error") {
      detected.push(["ERROR", 0.95, [e.event_id]]);
      break;
    }
  }

  // OVERLOAD (explicit too_much)
  if (!detected.some((d) => d[0] === "ERROR")) {
    for (const e of evs) {
      if (e.event_type === "user_feedback") {
        const fb = (e.payload as Record<string, unknown>).feedback;
        if (fb === "too_much") {
          detected.push(["OVERLOAD", 0.9, [e.event_id]]);
          break;
        }
      }
    }
  }

  // OVERLOAD (undo spike)
  if (!detected.some((d) => d[0] === "OVERLOAD")) {
    const undoIds = evs
      .filter(
        (e) =>
          e.event_type === "user_action" &&
          (e.payload as Record<string, unknown>).action === "undo"
      )
      .map((e) => e.event_id);
    if (undoIds.length >= 3) {
      detected.push(["OVERLOAD", 0.75, undoIds.slice(0, 3)]);
    }
  }

  // DECISION_REQUIRED
  if (!detected.some((d) => ["ERROR", "OVERLOAD"].includes(d[0]))) {
    for (const e of evs) {
      if (e.event_type === "decision_required") {
        detected.push(["DECISION_REQUIRED", 0.9, [e.event_id]]);
        break;
      }
    }
  }

  // FINDING (high-confidence artifact)
  if (
    !detected.some((d) =>
      ["ERROR", "OVERLOAD", "DECISION_REQUIRED"].includes(d[0])
    )
  ) {
    for (const e of evs) {
      if (e.event_type === "artifact_created") {
        const p = e.payload as Record<string, unknown>;
        if (
          p.schema === "wolf_candidates_v1" &&
          Number(p.confidence_max ?? 0) >= 0.6
        ) {
          detected.push(["FINDING", 0.7, [e.event_id]]);
          break;
        }
      }
    }
  }

  // HESITATION
  if (
    !detected.some((d) =>
      ["ERROR", "OVERLOAD", "DECISION_REQUIRED", "FINDING"].includes(d[0])
    )
  ) {
    const hasParamChange = evs.some(
      (e) =>
        e.event_type === "user_action" &&
        (e.payload as Record<string, unknown>).action === "parameter_changed"
    );
    if (!hasParamChange) {
      const idleEvent = evs.find((e) => e.event_type === "idle_timeout");
      if (idleEvent) {
        detected.push(["HESITATION", 0.8, [idleEvent.event_id]]);
      }
    }
  }

  // FIRST_SIGNAL
  if (!detected.length) {
    const viewEvent = evs.find(
      (e) =>
        e.event_type === "user_action" &&
        (e.payload as Record<string, unknown>).action === "view_rendered"
    );
    if (viewEvent) {
      detected.push(["FIRST_SIGNAL", 0.75, [viewEvent.event_id]]);
    } else {
      const compEvent = evs.find((e) => e.event_type === "analysis_completed");
      if (compEvent) {
        detected.push(["FIRST_SIGNAL", 0.65, [compEvent.event_id]]);
      }
    }
  }

  if (!detected.length) return [];

  // Priority suppression: keep only highest priority
  detected.sort((a, b) => {
    const pa = MOMENT_PRIORITY[a[0]] ?? 999;
    const pb = MOMENT_PRIORITY[b[0]] ?? 999;
    return pa - pb;
  });

  const best = detected[0];
  return [{ moment: best[0], confidence: best[1], trigger_events: best[2] }];
}

function buildDirective(
  action: string,
  guidance: string,
  softPrompt: boolean
): AttentionDirective {
  const titles: Record<string, string> = {
    INSPECT: "Inspect this",
    REVIEW: "Review this",
    COMPARE: "Compare options",
    DECIDE: "Make a choice",
    CONFIRM: "Confirm",
    NONE: "",
  };

  let detail = "";
  if (action === "INSPECT") {
    detail = "Focus on one signal and make a small change.";
  } else if (action === "REVIEW") {
    detail = "Let's simplify and confirm what changed.";
  } else if (action === "DECIDE") {
    detail = "Choose one option to proceed.";
  }

  if (softPrompt) {
    detail = "Want a suggestion for what to try next?";
  }

  if (guidance === "very_low" || guidance === "low") {
    detail = "";
  }

  return {
    action: action as AttentionDirective["action"],
    title: titles[action] ?? "Next step",
    detail,
  };
}

function decide(
  moment: { moment: string; confidence: number; trigger_events: string[] },
  uwsm: UWSMSnapshot,
  mode: AgenticMode
): PolicyDecision {
  const momentName = moment.moment;

  const guidance = uwsm.dimensions.guidance_density.value;
  const initiative = uwsm.dimensions.initiative_tolerance.value;
  const load = uwsm.dimensions.cognitive_load_sensitivity.value;

  const maxDirectives = load === "high" || load === "very_high" ? 1 : 2;

  const mapping: Record<string, string> = {
    FIRST_SIGNAL: "INSPECT",
    HESITATION: "INSPECT",
    OVERLOAD: "REVIEW",
    DECISION_REQUIRED: "DECIDE",
    FINDING: "REVIEW",
    ERROR: "REVIEW",
  };

  let action = mapping[momentName] ?? "NONE";
  let softPrompt = false;

  // Initiative gate
  if (
    initiative === "user_led" &&
    ["HESITATION", "FINDING", "FIRST_SIGNAL"].includes(momentName)
  ) {
    if (momentName === "HESITATION") {
      softPrompt = true;
    } else {
      action = "NONE";
    }
  }

  const diagnostic: PolicyDecision["diagnostic"] = {
    rule_id: `POLICY_${momentName}_${action}_v1`,
    max_directives: maxDirectives,
  };

  if (mode === "M0") {
    // Shadow mode: don't emit, but track what would have been emitted
    const wouldHave = buildDirective(action, guidance, softPrompt);
    diagnostic.would_have_emitted = wouldHave;
    return {
      attention_action: action,
      emit_directive: false,
      directive: { action: "NONE", title: "", detail: "" },
      diagnostic,
    };
  }

  // M1/M2: emit if action != NONE
  const emitDirective = action !== "NONE";
  const directive = emitDirective
    ? buildDirective(action, guidance, softPrompt)
    : { action: "NONE" as const, title: "", detail: "" };

  return {
    attention_action: action,
    emit_directive: emitDirective,
    directive,
    diagnostic,
  };
}

// --- Debounce utility ---

function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delayMs: number
): T {
  let timeoutId: number | null = null;
  return ((...args: unknown[]) => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }
    timeoutId = window.setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delayMs);
  }) as T;
}

// --- Constants ---

const DECISION_DEBOUNCE_MS = 250; // Prevent flicker
const EVENT_DEDUP_WINDOW_MS = 100; // Prevent rapid-fire same events
const FIRST_SIGNAL_GRACE_MS = 1500; // Grace window for FIRST_SIGNAL priority
const DIRECTIVE_COOLDOWN_MS = 10000; // 10s cooldown between non-critical directives

// Critical moments that bypass cooldown (always show immediately)
const CRITICAL_MOMENTS = new Set(["ERROR", "OVERLOAD", "DECISION_REQUIRED"]);

// --- Directive Key Utils ---

type DetectedMoment = { moment: string; confidence: number; trigger_events: string[] };

/**
 * Build a stable key for a directive based on moment + rule + trigger events.
 * Used for dismiss deduplication.
 */
function makeDirectiveKey(
  moment: DetectedMoment | null,
  decision: PolicyDecision | null
): string | null {
  if (!moment || !decision) return null;
  const m = moment.moment ?? "NONE";
  const rule = decision.diagnostic?.rule_id ?? "NO_RULE";
  // Sort trigger IDs for determinism (order can vary)
  const triggers = [...(moment.trigger_events ?? [])].sort().join(",");
  return `${m}|${rule}|${triggers}`;
}

/**
 * Select moment with FIRST_SIGNAL grace window and one-shot suppression.
 * Ensures FTUE shows "Inspect this" before "Review this".
 *
 * Rules:
 * 1. FIRST_SIGNAL is one-shot: if already shown, never return it again
 * 2. If FINDING is top but we haven't shown FIRST_SIGNAL yet, prefer FIRST_SIGNAL
 * 3. During grace window, suppress non-critical if FIRST_SIGNAL not yet shown
 */
function selectMomentWithGrace(
  moments: DetectedMoment[],
  firstSignalShown: boolean,
  firstViewRenderedAt: number | null
): DetectedMoment | null {
  if (!moments?.length) return null;

  const top = moments[0];

  // One-shot: if FIRST_SIGNAL already shown, never return it again
  if (firstSignalShown && top.moment === "FIRST_SIGNAL") {
    // Skip to next moment if available, otherwise null
    const next = moments.find((m) => m.moment !== "FIRST_SIGNAL");
    return next ?? null;
  }

  // If FINDING is top but we haven't shown FIRST_SIGNAL yet,
  // prefer FIRST_SIGNAL if present in moments list
  if (!firstSignalShown && top.moment === "FINDING") {
    const firstSignal = moments.find((m) => m.moment === "FIRST_SIGNAL");
    if (firstSignal) return firstSignal;

    // Grace window suppression: if FIRST_SIGNAL not present yet,
    // show nothing briefly rather than jumping straight to FINDING
    if (
      firstViewRenderedAt != null &&
      Date.now() - firstViewRenderedAt < FIRST_SIGNAL_GRACE_MS
    ) {
      return null;
    }
  }

  return top;
}

// --- Store ---

export const useAgenticDirectiveStore = defineStore(
  "agenticDirective",
  () => {
    // State
    const sessionId = ref<string>(`session_${Date.now().toString(36)}`);
    const events = ref<AgentEventV1[]>([]);
    const uwsm = ref<UWSMSnapshot>({ ...DEFAULT_UWSM });
    const latestDecision = ref<PolicyDecision | null>(null);
    const dismissed = ref<boolean>(false);

    // Event deduplication tracking
    const lastEventByType = ref<Map<string, number>>(new Map());

    // Directive dedupe tracking (Option B)
    const lastDirectiveKey = ref<string | null>(null);
    const dismissedKeys = ref<Set<string>>(new Set());
    const firstSignalShown = ref<boolean>(false);
    const firstViewRenderedAt = ref<number | null>(null);
    const latestMoment = ref<DetectedMoment | null>(null);
    const lastDirectiveShownAt = ref<number | null>(null);

    // Mode from environment
    const mode = computed<AgenticMode>(() => {
      const envMode = import.meta.env.VITE_AGENTIC_MODE as string | undefined;
      if (envMode === "M1") return "M1";
      if (envMode === "M2") return "M2";
      return "M0"; // Default to shadow
    });

    // Computed
    const isEnabled = computed(() => mode.value !== "M0");
    const currentDirective = computed(() => {
      if (!isEnabled.value || dismissed.value) return null;
      if (!latestDecision.value?.emit_directive) return null;
      return latestDecision.value.directive;
    });

    // Actions

    /**
     * Check if an event of this type was emitted recently (deduplication).
     */
    function isDuplicateEvent(eventType: string): boolean {
      const now = Date.now();
      const lastTime = lastEventByType.value.get(eventType);
      if (lastTime && now - lastTime < EVENT_DEDUP_WINDOW_MS) {
        return true;
      }
      lastEventByType.value.set(eventType, now);
      return false;
    }

    function emitEvent(
      eventType: string,
      payload: Record<string, unknown>,
      component = "ui"
    ) {
      // Deduplication: skip if same event type within window
      // Exception: user_feedback and user_action always go through
      if (
        !["user_feedback", "user_action"].includes(eventType) &&
        isDuplicateEvent(eventType)
      ) {
        return null;
      }

      const event: AgentEventV1 = {
        event_id: `evt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
        event_type: eventType,
        source: {
          repo: "luthiers-toolbox",
          component,
          version: "1.0.0",
        },
        payload,
        privacy_layer: 2,
        occurred_at: new Date().toISOString(),
        schema_version: "1.0.0",
        session: { session_id: sessionId.value },
      };

      events.value.push(event);

      // Track first view_rendered for FIRST_SIGNAL grace window
      if (
        eventType === "user_action" &&
        payload?.action === "view_rendered" &&
        firstViewRenderedAt.value === null
      ) {
        firstViewRenderedAt.value = Date.now();
      }

      // Re-run decision pipeline (debounced)
      debouncedUpdateDecision();

      return event;
    }

    function updateDecisionImmediate() {
      const moments = detectMoments(events.value);

      // IMPORTANT: choose moment with FIRST_SIGNAL grace logic
      const chosen = selectMomentWithGrace(
        moments,
        firstSignalShown.value,
        firstViewRenderedAt.value
      );

      if (!chosen) {
        latestMoment.value = null;
        latestDecision.value = null;
        return;
      }

      latestMoment.value = chosen;

      const decision = decide(chosen, uwsm.value, mode.value);
      latestDecision.value = decision;

      // Shadow mode never shows UI directives
      if (mode.value === "M0") return;

      // If decision doesn't emit, nothing to track
      if (!decision.emit_directive) return;

      const key = makeDirectiveKey(chosen, decision);

      // 1) If key already dismissed, suppress showing it (but keep decision for diagnostics)
      if (key && dismissedKeys.value.has(key)) {
        latestDecision.value = { ...decision, emit_directive: false };
        return;
      }

      // 2) If same directiveKey as last time, do NOT reset dismissed=false
      //    (prevents flicker/resurrection on reprocessing full event list)
      if (key && key === lastDirectiveKey.value) {
        return;
      }

      // 3) Cooldown: suppress non-critical moments if within cooldown period
      //    (prevents nagging — feels human)
      const isCritical = CRITICAL_MOMENTS.has(chosen.moment);
      if (!isCritical && lastDirectiveShownAt.value != null) {
        const elapsed = Date.now() - lastDirectiveShownAt.value;
        if (elapsed < DIRECTIVE_COOLDOWN_MS) {
          // Suppress but keep decision for diagnostics
          latestDecision.value = { ...decision, emit_directive: false };
          return;
        }
      }

      // 4) New directiveKey: accept it, show bubble, and clear dismissed for this new key only
      lastDirectiveKey.value = key ?? null;
      lastDirectiveShownAt.value = Date.now();
      dismissed.value = false;

      // FIRST_SIGNAL bookkeeping
      if (chosen.moment === "FIRST_SIGNAL") {
        firstSignalShown.value = true;
      }
    }

    // Debounced version to prevent UI flicker
    const debouncedUpdateDecision = debounce(
      updateDecisionImmediate,
      DECISION_DEBOUNCE_MS
    );

    // Alias for external callers who want immediate update
    function updateDecision() {
      updateDecisionImmediate();
    }

    function submitFeedback(feedback: "helpful" | "too_much") {
      const directive = latestDecision.value?.directive;
      const ruleId = latestDecision.value?.diagnostic?.rule_id ?? "unknown";

      // Add current directive key to dismissed set (prevents resurrection)
      const key = makeDirectiveKey(latestMoment.value, latestDecision.value);
      if (key) {
        dismissedKeys.value.add(key);
      }

      emitEvent("user_feedback", {
        feedback,
        directive_action: directive?.action ?? "NONE",
        rule_id: ruleId,
      });

      // If too_much, nudge UWSM cognitive_load_sensitivity
      if (feedback === "too_much") {
        const current = uwsm.value.dimensions.cognitive_load_sensitivity.value;
        if (current === "low") {
          uwsm.value.dimensions.cognitive_load_sensitivity.value = "medium";
        } else if (current === "medium") {
          uwsm.value.dimensions.cognitive_load_sensitivity.value = "high";
        } else if (current === "high") {
          uwsm.value.dimensions.cognitive_load_sensitivity.value = "very_high";
        }
      }

      // Dismiss current directive
      dismissed.value = true;
    }

    function dismissDirective() {
      const directive = latestDecision.value?.directive;
      const ruleId = latestDecision.value?.diagnostic?.rule_id ?? "unknown";

      // Add current directive key to dismissed set (prevents resurrection)
      const key = makeDirectiveKey(latestMoment.value, latestDecision.value);
      if (key) {
        dismissedKeys.value.add(key);
      }

      emitEvent("user_action", {
        action: "dismiss_directive",
        directive_action: directive?.action ?? "NONE",
        rule_id: ruleId,
      });

      dismissed.value = true;
    }

    function clearSession() {
      events.value = [];
      latestDecision.value = null;
      latestMoment.value = null;
      dismissed.value = false;
      sessionId.value = `session_${Date.now().toString(36)}`;
      uwsm.value = { ...DEFAULT_UWSM };

      // Reset directive tracking
      lastDirectiveKey.value = null;
      dismissedKeys.value.clear();
      firstSignalShown.value = false;
      firstViewRenderedAt.value = null;
      lastDirectiveShownAt.value = null;
      lastEventByType.value.clear();
    }

    // Export events as JSONL (for debugging/recording)
    function exportEventsJsonl(): string {
      return events.value.map((e) => JSON.stringify(e)).join("\n");
    }

    return {
      // State
      sessionId,
      events,
      uwsm,
      latestDecision,
      dismissed,
      mode,

      // Computed
      isEnabled,
      currentDirective,

      // Actions
      emitEvent,
      updateDecision,
      submitFeedback,
      dismissDirective,
      clearSession,
      exportEventsJsonl,
    };
  }
);
