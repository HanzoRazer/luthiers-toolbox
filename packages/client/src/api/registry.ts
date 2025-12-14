// packages/client/src/api/registry.ts
/**
 * Data Registry API Client
 *
 * Provides typed functions for accessing edition-based data:
 * - System tier (all editions): scales, woods, formulas
 * - Edition tier (Pro/Enterprise): empirical limits, machines, tools
 *
 * @module api/registry
 */

// ============================================================================
// Types
// ============================================================================

export type Edition =
  | "express"
  | "pro"
  | "enterprise"
  | "parametric"
  | "neck_designer"
  | "headstock_designer"
  | "bridge_designer"
  | "fingerboard_designer"
  | "cnc_blueprints";

export interface RegistryInfo {
  edition: Edition;
  version: string;
  tiers: string[];
  system_datasets: string[];
  edition_datasets: string[];
}

export interface ScaleLength {
  id: string;
  name: string;
  length_mm: number;
  length_inches: number;
  description?: string;
}

export interface ScaleLengthResponse {
  scales: Record<string, ScaleLength>;
  count: number;
}

export interface WoodSpecies {
  id: string;
  name: string;
  density_kg_m3: number;
  janka_hardness: number;
  workability: "easy" | "moderate" | "difficult";
  common_uses: string[];
}

export interface WoodSpeciesResponse {
  species: Record<string, WoodSpecies>;
  count: number;
}

export interface FeedClamp {
  roughing_max: number;
  finishing_max: number;
  plunge_max: number;
}

export interface SpeedClamp {
  min_rpm: number;
  max_rpm: number;
  optimal_sfm: number;
}

export interface EmpiricalLimit {
  wood_id: string;
  feed_clamp: FeedClamp;
  speed_clamp: SpeedClamp;
  doc_limits: {
    max_depth_mm: number;
    recommended_mm: number;
  };
  warnings: {
    burn_risk: boolean;
    tearout_risk: boolean;
    dust_hazard: boolean;
  };
}

export interface EmpiricalLimitsResponse {
  limits: Record<string, EmpiricalLimit>;
  count: number;
  edition_required: string;
}

export interface FretFormula {
  id: string;
  name: string;
  constant: number;
  description?: string;
}

export interface FretFormulasResponse {
  formulas: Record<string, FretFormula>;
  count: number;
  edition: Edition;
}

export interface RegistryHealth {
  status: "healthy" | "degraded" | "unhealthy";
  checks: {
    system_tier?: { status: string; scales_loaded?: number; error?: string };
    edition_tier?: { status: string; limits_loaded?: number; error?: string };
  };
}

export interface EntitlementError {
  error: "edition_required" | "pro_required" | "enterprise_required";
  feature?: string;
  current_edition: Edition;
  required_edition: Edition;
  message: string;
  upgrade_url: string;
}

// ============================================================================
// API Configuration
// ============================================================================

const BASE_URL = "/api/registry";

/**
 * Get current edition from localStorage or default
 */
export function getCurrentEdition(): Edition {
  const stored = localStorage.getItem("ltb_edition");
  if (stored && isValidEdition(stored)) {
    return stored as Edition;
  }
  return "pro"; // Default for development
}

/**
 * Set current edition in localStorage
 */
export function setCurrentEdition(edition: Edition): void {
  localStorage.setItem("ltb_edition", edition);
}

function isValidEdition(value: string): value is Edition {
  return [
    "express",
    "pro",
    "enterprise",
    "parametric",
    "neck_designer",
    "headstock_designer",
    "bridge_designer",
    "fingerboard_designer",
    "cnc_blueprints",
  ].includes(value);
}

/**
 * Build headers with edition context
 */
function buildHeaders(edition?: Edition): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  // Add edition header for testing/override
  const ed = edition ?? getCurrentEdition();
  headers["X-Edition"] = ed;
  return headers;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get registry metadata and available datasets
 */
export async function getRegistryInfo(
  edition?: Edition
): Promise<RegistryInfo> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/info?edition=${ed}`, {
    headers: buildHeaders(ed),
  });
  if (!response.ok) {
    throw new Error(`Failed to get registry info: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get standard scale length specifications (System tier - all editions)
 */
export async function getScaleLengths(
  edition?: Edition
): Promise<ScaleLengthResponse> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/scale_lengths?edition=${ed}`, {
    headers: buildHeaders(ed),
  });
  if (!response.ok) {
    throw new Error(`Failed to get scale lengths: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get wood species reference data (System tier - all editions)
 */
export async function getWoodSpecies(
  edition?: Edition
): Promise<WoodSpeciesResponse> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/wood_species?edition=${ed}`, {
    headers: buildHeaders(ed),
  });
  if (!response.ok) {
    throw new Error(`Failed to get wood species: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get empirical feed/speed limits (Edition tier - Pro/Enterprise only)
 *
 * @throws {EntitlementError} if current edition is Express
 */
export async function getEmpiricalLimits(
  edition?: Edition
): Promise<EmpiricalLimitsResponse> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/empirical_limits`, {
    headers: buildHeaders(ed),
  });

  if (response.status === 403) {
    const error: EntitlementError = await response.json();
    throw error;
  }

  if (!response.ok) {
    throw new Error(`Failed to get empirical limits: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get empirical limits for a specific wood species (Edition tier - Pro/Enterprise only)
 *
 * @throws {EntitlementError} if current edition is Express
 */
export async function getEmpiricalLimitByWood(
  woodId: string,
  edition?: Edition
): Promise<{ wood_id: string; limits: EmpiricalLimit; edition: Edition }> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/empirical_limits/${woodId}`, {
    headers: buildHeaders(ed),
  });

  if (response.status === 403) {
    const error: EntitlementError = await response.json();
    throw error;
  }

  if (response.status === 404) {
    throw new Error(`Wood species '${woodId}' not found`);
  }

  if (!response.ok) {
    throw new Error(`Failed to get empirical limit: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get fret calculation formulas (System tier - all editions)
 */
export async function getFretFormulas(
  edition?: Edition
): Promise<FretFormulasResponse> {
  const ed = edition ?? getCurrentEdition();
  const response = await fetch(`${BASE_URL}/fret_formulas?edition=${ed}`, {
    headers: buildHeaders(ed),
  });
  if (!response.ok) {
    throw new Error(`Failed to get fret formulas: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Check registry health status
 */
export async function getRegistryHealth(): Promise<RegistryHealth> {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Failed to get registry health: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if an error is an EntitlementError
 */
export function isEntitlementError(error: unknown): error is EntitlementError {
  return (
    typeof error === "object" &&
    error !== null &&
    "error" in error &&
    "required_edition" in error
  );
}

/**
 * Get upgrade prompt message for entitlement errors
 */
export function getUpgradePrompt(error: EntitlementError): string {
  return `${
    error.message
  }\n\nUpgrade to ${error.required_edition.toUpperCase()} at: ${
    error.upgrade_url
  }`;
}
