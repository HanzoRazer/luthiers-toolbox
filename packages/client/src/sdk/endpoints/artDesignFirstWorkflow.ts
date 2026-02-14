// packages/client/src/sdk/endpoints/artDesignFirstWorkflow.ts
/**
 * Art Studio Design-First Workflow SDK Endpoints (Bundle 32.7.0)
 *
 * Typed SDK helpers for the design-first workflow API.
 */

import { apiFetch } from "@/sdk/core/apiFetch";
import type {
  GetDesignFirstResponse,
  PromotionIntentResponse,
  StartDesignFirstRequest,
  StartDesignFirstResponse,
  TransitionDesignFirstRequest,
  TransitionDesignFirstResponse,
} from "@/types/designFirstWorkflow";

const BASE = "/api/art/design-first-workflow";

/**
 * Start a new design-first workflow session.
 */
export async function startDesignFirstWorkflow(
  req: StartDesignFirstRequest
): Promise<StartDesignFirstResponse> {
  return apiFetch(`${BASE}/sessions/start`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Get an existing workflow session.
 */
export async function getDesignFirstWorkflow(
  sessionId: string
): Promise<GetDesignFirstResponse> {
  return apiFetch(`${BASE}/sessions/${sessionId}`, {
    method: "GET",
  });
}

/**
 * Transition a workflow session to a new state.
 */
export async function transitionDesignFirstWorkflow(
  sessionId: string,
  req: TransitionDesignFirstRequest
): Promise<TransitionDesignFirstResponse> {
  return apiFetch(`${BASE}/sessions/${sessionId}/transition`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/**
 * Get a CAM handoff promotion intent (does NOT execute CAM).
 */
export async function getDesignFirstPromotionIntent(
  sessionId: string
): Promise<PromotionIntentResponse> {
  return apiFetch(`${BASE}/sessions/${sessionId}/promotion_intent`, {
    method: "POST",
  });
}
