// packages/client/src/stores/artDesignFirstWorkflowStore.ts
/**
 * Art Design-First Workflow Store (Bundle 32.7.0)
 *
 * Pinia store for managing design-first workflow state.
 * Handles session lifecycle: DRAFT → IN_REVIEW → APPROVED → promotion intent.
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
} from "@/sdk/endpoints/artDesignFirstWorkflow";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";

export const useArtDesignFirstWorkflowStore = defineStore("artDesignFirstWorkflow", () => {
  // State
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
  };
});
