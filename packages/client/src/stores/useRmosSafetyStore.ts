/**
 * RMOS N10.2: Safety store for apprenticeship mode.
 * 
 * Pinia store managing safety mode state, action evaluation, and override tokens.
 */

import { defineStore } from "pinia";
import type {
  SafetyModeState,
  SafetyMode,
  SafetyActionContext,
  EvaluateActionResponse,
  OverrideToken,
} from "@/models/rmos_safety";

export const useRmosSafetyStore = defineStore("rmosSafety", {
  state: () => ({
    modeState: null as SafetyModeState | null,
    loadingMode: false,
    errorMode: null as string | null,

    lastDecision: null as EvaluateActionResponse | null,
    evaluating: false,
    evalError: null as string | null,
  }),

  getters: {
    /**
     * Get current safety mode, defaulting to unrestricted if not loaded.
     */
    currentMode(state): SafetyMode {
      return state.modeState?.mode ?? "unrestricted";
    },

    /**
     * Check if currently in apprentice mode.
     */
    isApprenticeMode(state): boolean {
      return state.modeState?.mode === "apprentice";
    },

    /**
     * Check if currently in mentor review mode.
     */
    isMentorReviewMode(state): boolean {
      return state.modeState?.mode === "mentor_review";
    },

    /**
     * Check if currently in unrestricted mode.
     */
    isUnrestrictedMode(state): boolean {
      return state.modeState?.mode === "unrestricted";
    },
  },

  actions: {
    /**
     * Fetch current safety mode from API.
     */
    async fetchMode() {
      this.loadingMode = true;
      this.errorMode = null;
      try {
        const res = await fetch("/api/rmos/safety/mode");
        if (!res.ok) throw new Error(`Failed to fetch safety mode: ${res.status}`);
        this.modeState = (await res.json()) as SafetyModeState;
      } catch (e: any) {
        this.errorMode = String(e.message || e);
      } finally {
        this.loadingMode = false;
      }
    },

    /**
     * Set safety mode (requires mentor/admin privileges).
     * 
     * @param mode - Target safety mode
     * @param setBy - Optional identifier of who set the mode
     */
    async setMode(mode: SafetyMode, setBy?: string) {
      this.loadingMode = true;
      this.errorMode = null;
      try {
        const res = await fetch("/api/rmos/safety/mode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode, set_by: setBy ?? null }),
        });
        if (!res.ok) throw new Error(`Failed to set safety mode: ${res.status}`);
        this.modeState = (await res.json()) as SafetyModeState;
      } catch (e: any) {
        this.errorMode = String(e.message || e);
      } finally {
        this.loadingMode = false;
      }
    },

    /**
     * Evaluate whether an action is allowed, requires override, or is denied.
     * 
     * @param ctx - Action context with risk factors
     * @param overrideToken - Optional override token to consume
     * @returns EvaluateActionResponse with decision
     * @throws Error if evaluation fails or override is invalid
     */
    async evaluateAction(ctx: SafetyActionContext, overrideToken?: string): Promise<EvaluateActionResponse> {
      this.evaluating = true;
      this.evalError = null;
      this.lastDecision = null;
      try {
        const res = await fetch("/api/rmos/safety/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...ctx, override_token: overrideToken ?? null }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => null);
          const msg = err?.detail || `Safety evaluation failed: ${res.status}`;
          throw new Error(msg);
        }
        const data = (await res.json()) as EvaluateActionResponse;
        this.lastDecision = data;
        return data;
      } catch (e: any) {
        this.evalError = String(e.message || e);
        throw e;
      } finally {
        this.evaluating = false;
      }
    },

    /**
     * Create a new override token via API.
     * 
     * @param action - Action name the token authorizes
     * @param createdBy - Optional identifier of who created the token
     * @param ttlMinutes - Token expiration time in minutes (default 15)
     * @returns OverrideToken with unique token string
     * @throws Error if creation fails
     */
    async createOverride(action: string, createdBy?: string, ttlMinutes = 15): Promise<OverrideToken> {
      const res = await fetch("/api/rmos/safety/create-override", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, created_by: createdBy ?? null, ttl_minutes: ttlMinutes }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const msg = err?.detail || `Failed to create override: ${res.status}`;
        throw new Error(msg);
      }
      return (await res.json()) as OverrideToken;
    },

    /**
     * Clear last decision and errors.
     */
    clearDecision() {
      this.lastDecision = null;
      this.evalError = null;
    },

    /**
     * Guarded action helper - wraps evaluation + prompt flow for DRY UI integration.
     * 
     * Evaluates action safety, prompts for override if needed, and executes action if allowed.
     * 
     * @param ctx - Action context with risk factors
     * @param doAction - Async function to execute if safety allows
     * @returns true if action executed, false if blocked/cancelled
     * 
     * Example:
     *   await safety.guardedAction(
     *     { action: "promote_preset", lane: "safe", fragility_score: 0.8 },
     *     async () => {
     *       await fetch("/api/rmos/presets/123/promote", { ... })
     *     }
     *   )
     */
    async guardedAction(
      ctx: SafetyActionContext,
      doAction: () => Promise<void>
    ): Promise<boolean> {
      // 1. Initial evaluation
      const res = await this.evaluateAction(ctx).catch(() => null);
      if (!res) return false;

      const decision = res.decision;

      // 2. Handle deny
      if (decision.decision === "deny") {
        alert(`Action denied: ${decision.reason}`);
        return false;
      }

      // 3. Handle override requirement
      if (decision.decision === "require_override") {
        const token = window.prompt(
          `Safety override required.\n\nReason: ${decision.reason}\n\n` +
            `Ask mentor for a one-time override token and paste it here:`
        );
        if (!token) return false;

        // Retry with override
        const res2 = await this
          .evaluateAction(ctx, token)
          .catch((e) => {
            alert(`Override failed: ${String(e)}`);
            return null;
          });
        if (!res2) return false;

        if (res2.decision.decision !== "allow") {
          alert(`Still blocked: ${res2.decision.reason}`);
          return false;
        }
      }

      // 4. Safe to perform the action
      await doAction();
      return true;
    },

    /**
     * Clear all safety state (for logout/reset).
     */
    reset() {
      this.modeState = null;
      this.loadingMode = false;
      this.errorMode = null;
      this.lastDecision = null;
      this.evaluating = false;
      this.evalError = null;
    },
  },
});
