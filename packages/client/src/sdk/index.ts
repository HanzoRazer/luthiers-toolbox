/**
 * Luthier's Toolbox Frontend SDK
 *
 * Canonical, type-safe API client for frontend applications.
 *
 * Usage:
 *   import { rmos, art, ApiError, setDeprecationHandler } from "@/sdk";
 *
 *   // Configure deprecation warnings (optional, recommended for dev)
 *   setDeprecationHandler((e) => {
 *     console.warn(`[DEPRECATION] ${e.method} ${e.url}`, e);
 *   });
 *
 *   // Use domain clients
 *   const runs = await rmos.runs.listRuns({ limit: 50 });
 *   const session = await rmos.workflow.getSession(sessionId);
 *   const snapshots = await art.snapshots.listSnapshots();
 */

// Domain clients
export * as rmos from "./rmos";
export * as art from "./art";

// Core utilities
export { ApiError } from "./core/errors";
export { setDeprecationHandler, generateRequestId } from "./core/headers";
export { assertRequestIdHeader, isRequestIdStrict } from "./core/assertRequestId";
export { apiFetch, get, post, patch, put, del } from "./core/apiFetch";

// Core types
export type { ApiFetchOptions, PaginatedResponse, Timestamped, IndexedEntity } from "./core/types";
export type { DeprecationEvent } from "./core/headers";
export type { RequestIdAssertMode, RequestIdAssertOptions } from "./core/assertRequestId";
