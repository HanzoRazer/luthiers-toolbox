// packages/client/src/stores/artDesignFirstWorkflowStore.ts
/**
 * Art Design-First Workflow Store (Bundle 32.7.0 + 32.7.2 + 32.7.7)
 *
 * Pinia store for managing design-first workflow state.
 * Handles session lifecycle: DRAFT → IN_REVIEW → APPROVED → promotion intent.
 *
 * Bundle 32.7.2: Added localStorage persistence for session ID.
 * Bundle 32.7.7: Added loadSessionById for session picker.
 */

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type {
  DesignFirstSession,
  DesignFirstState,
  PromotionIntent,
} from "@/types/designFirstWorkflow";
import {
  startDesignFirstWorkflow,
  transitionDesignFirstWorkflow,
  getDesignFirstPromotionIntent,
  getDesignFirstWorkflow,
} from "@/sdk/endpoints/artDesignFirstWorkflow";
import { getWorkflowSession } from "@/sdk/endpoints/artDesignFirstWorkflowSessions";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";

// localStorage key for session persistence
const LS_KEY = "artstudio.workflow.sessionId.v1";

export const useArtDesignFirstWorkflowStore = defineStore("artDesignFirstWorkflow", () => {
  // ==========================================================================
  // localStorage Persistence Helpers (Bundle 32.7.2)
  // ==========================================================================

  function _persistSessionId(sid: string): void {
    try {
      localStorage.setItem(LS_KEY, sid);
    } catch {
      // localStorage may be unavailable (e.g., private mode)
    }
  }

  function _clearPersistedSessionId(): void {
    try {
      localStorage.removeItem(LS_KEY);
    } catch {
      // Ignore if localStorage unavailable
    }
  }

  function _getPersistedSessionId(): string | null {
    try {
      return localStorage.getItem(LS_KEY);
    } catch {
      return null;
    }
  }

  // ==========================================================================
  // State
  // ==========================================================================
  const session = ref<DesignFirstSession | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const lastPromotionIntent = ref<PromotionIntent | null>(null);

  // Getters
  const stateName = computed(() => session.value?.state ?? null);
  const canRequestIntent = computed(() => session.value?.state === "approved");
  const hasSession = computed(() => session.value !== null);
  const sessionId = computed(() => session.value?.session_id ?? null);

  // Actions
  async function ensureSessionDesignFirst() {
    const rosette = useRosetteStore();
    const toast = useToastStore();

    if (session.value) return session.value;

    loading.value = true;
    error.value = null;
    try {
      const res = await startDesignFirstWorkflow({
        mode: "design_first",
        design: rosette.currentParams,
        feasibility: rosette.lastFeasibility ?? undefined,
      });
      session.value = res.session;
      // Persist session ID for page reload recovery
      _persistSessionId(res.session.session_id);
      toast.info("Workflow started (Design-First)");
      return session.value;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg;
      toast.error(`Workflow start failed: ${msg}`);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function transition(toState: DesignFirstState, note?: string) {
    if (!session.value) {
      error.value = "No active session";
      return null;
    }

    const rosette = useRosetteStore();
    const toast = useToastStore();

    loading.value = true;
    error.value = null;
    try {
      const res = await transitionDesignFirstWorkflow(session.value.session_id, {
        to_state: toState,
        note,
        design: rosette.currentParams,
        feasibility: rosette.lastFeasibility ?? undefined,
      });
      session.value = res.session;
      toast.success(`Workflow → ${toState}`);
      return session.value;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg;
      toast.error(`Transition failed: ${msg}`);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function requestPromotionIntent(): Promise<PromotionIntent | null> {
    if (!session.value) {
      error.value = "No active session";
      return null;
    }

    const toast = useToastStore();

    loading.value = true;
    error.value = null;
    try {
      const res = await getDesignFirstPromotionIntent(session.value.session_id);
      if (res.ok) {
        lastPromotionIntent.value = res.intent;
        toast.success("Promotion intent prepared (no CAM executed)");
        return res.intent;
      }
      toast.warning(`Blocked: ${res.blocked_reason}`);
      return null;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg;
      toast.error(`Intent request failed: ${msg}`);
      return null;
    } finally {
      loading.value = false;
    }
  }

  function clearSession() {
    session.value = null;
    lastPromotionIntent.value = null;
    error.value = null;
    _clearPersistedSessionId();
  }

  /**
   * Hydrate session from localStorage if available.
   * Call this on component mount to restore session across page reloads.
   */
  async function hydrateFromLocalStorage(): Promise<DesignFirstSession | null> {
    const toast = useToastStore();
    const persistedId = _getPersistedSessionId();

    if (!persistedId) {
      return null;
    }

    // Already have this session loaded
    if (session.value?.session_id === persistedId) {
      return session.value;
    }

    loading.value = true;
    error.value = null;
    try {
      const res = await getDesignFirstWorkflow(persistedId);
      session.value = res.session;
      toast.info("Workflow session restored");
      return session.value;
    } catch (e: unknown) {
      // Session not found on server — clear stale localStorage
      _clearPersistedSessionId();
      const msg = e instanceof Error ? e.message : String(e);
      console.warn("[ArtDesignFirstWorkflow] Failed to hydrate session:", msg);
      return null;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Load a session by ID (Bundle 32.7.7).
   * Used by session picker to jump between sessions.
   */
  async function loadSessionById(sessionId: string): Promise<DesignFirstSession | null> {
    const toast = useToastStore();
    loading.value = true;
    error.value = null;
    try {
      const res = await getWorkflowSession(sessionId);
      session.value = res.session;
      _persistSessionId(res.session.session_id);
      toast.success("Loaded workflow session.");
      return session.value;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg;
      toast.error(`Load failed: ${msg}`);
      return null;
    } finally {
      loading.value = false;
    }
  }

  return {
    // State
    session,
    loading,
    error,
    lastPromotionIntent,
    // Getters
    stateName,
    canRequestIntent,
    hasSession,
    sessionId,
    // Actions
    ensureSessionDesignFirst,
    transition,
    requestPromotionIntent,
    clearSession,
    hydrateFromLocalStorage,
    loadSessionById,
  };
});
