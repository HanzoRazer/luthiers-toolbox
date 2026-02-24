// packages/client/src/sdk/endpoints/businessEstimator.ts
/**
 * Business Engineering Estimator SDK Endpoints
 *
 * Pro feature - parametric cost estimation for instrument builds.
 * All estimation logic runs server-side.
 */

import { apiFetch } from "@/sdk/core/apiFetch";
import type {
  EstimateRequest,
  EstimateResult,
  QuoteRequest,
  QuoteResult,
  ComplexityFactors,
  WBSTemplate,
  LearningCurveProjection,
  LearningCurveParams,
  InstrumentType,
} from "@/types/businessEstimator";

const BASE = "/api/business";

// ============================================================================
// PARAMETRIC ESTIMATION
// ============================================================================

/**
 * Create a parametric cost estimate for an instrument build.
 *
 * Uses engineering estimation techniques:
 * - Work Breakdown Structure (WBS) templates
 * - Complexity factors for design choices
 * - Learning curve adjustments for batch production
 * - Material yield/waste factors
 */
export async function createEstimate(
  request: EstimateRequest
): Promise<EstimateResult> {
  return apiFetch(`${BASE}/estimate/parametric`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Generate a customer-facing quote from an estimate.
 */
export async function generateQuote(
  request: QuoteRequest
): Promise<QuoteResult> {
  return apiFetch(`${BASE}/estimate/quote`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// ============================================================================
// REFERENCE DATA
// ============================================================================

/**
 * Get all complexity factors and their multipliers.
 */
export async function getComplexityFactors(): Promise<ComplexityFactors> {
  return apiFetch(`${BASE}/estimate/factors`, {
    method: "GET",
  });
}

/**
 * Get the Work Breakdown Structure template for an instrument type.
 */
export async function getWBSTemplate(
  instrumentType: InstrumentType
): Promise<WBSTemplate> {
  return apiFetch(`${BASE}/estimate/wbs/${instrumentType}`, {
    method: "GET",
  });
}

/**
 * Preview learning curve effect for batch production.
 */
export async function getLearningCurveProjection(
  params: LearningCurveParams
): Promise<LearningCurveProjection> {
  const searchParams = new URLSearchParams({
    first_unit_hours: params.first_unit_hours.toString(),
    quantity: params.quantity.toString(),
  });
  if (params.learning_rate !== undefined) {
    searchParams.set("learning_rate", params.learning_rate.toString());
  }
  if (params.hourly_rate !== undefined) {
    searchParams.set("hourly_rate", params.hourly_rate.toString());
  }
  return apiFetch(`${BASE}/estimate/learning-curve?${searchParams}`, {
    method: "GET",
  });
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Format currency for display.
 */
export function formatCurrency(value: number, decimals = 0): string {
  return `$${value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
}

/**
 * Format hours for display.
 */
export function formatHours(value: number): string {
  return `${value.toFixed(1)}h`;
}

/**
 * Format percentage for display.
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

/**
 * Format multiplier for display.
 */
export function formatMultiplier(value: number): string {
  return `${value.toFixed(2)}×`;
}

/**
 * Get color for task group (for WBS visualization).
 */
export function getGroupColor(group: string | null): string {
  const colors: Record<string, string> = {
    body: "#4a9eff",
    neck: "#a78bfa",
    finish: "#fb923c",
    binding: "#34d399",
    rosette: "#f472b6",
  };
  return colors[group ?? ""] ?? "#6b7280";
}
