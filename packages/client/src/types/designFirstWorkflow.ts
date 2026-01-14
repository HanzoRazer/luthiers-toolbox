// packages/client/src/types/designFirstWorkflow.ts
/**
 * Design-First Workflow Types (Bundle 32.7.0)
 *
 * Types for the lightweight workflow binding:
 * Design → Review → Approve → "CAM handoff intent"
 */

import type { RosetteParamSpec } from "@/types/rosette";

export type DesignFirstMode = "design_first";
export type DesignFirstState = "draft" | "in_review" | "approved" | "rejected";

export type DesignFirstEvent = {
  ts: string;
  actor: string;
  action: string;
  from_state: DesignFirstState;
  to_state: DesignFirstState;
  note?: string | null;
};

export type DesignFirstSession = {
  session_id: string;
  mode: DesignFirstMode;
  state: DesignFirstState;
  created_at: string;
  updated_at: string;
  design: RosetteParamSpec;
  feasibility?: Record<string, unknown> | null;
  history: DesignFirstEvent[];
};

export type StartDesignFirstRequest = {
  mode: DesignFirstMode;
  design: RosetteParamSpec;
  feasibility?: Record<string, unknown> | null;
};

export type StartDesignFirstResponse = {
  session: DesignFirstSession;
};

export type GetDesignFirstResponse = {
  session: DesignFirstSession;
};

export type TransitionDesignFirstRequest = {
  to_state: DesignFirstState;
  note?: string | null;
  actor?: string;
  design?: RosetteParamSpec;
  feasibility?: Record<string, unknown> | null;
};

export type TransitionDesignFirstResponse = {
  session: DesignFirstSession;
};

export type PromotionIntent = {
  session_id: string;
  mode: DesignFirstMode;
  approved_at: string;
  design: RosetteParamSpec;
  feasibility?: Record<string, unknown> | null;
  recommended_next_step: string;
};

export type PromotionIntentResponse =
  | { ok: true; intent: PromotionIntent; blocked_reason?: null }
  | { ok: false; intent?: null; blocked_reason: string };
