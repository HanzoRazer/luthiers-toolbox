/**
 * SDK Core Module
 *
 * Low-level utilities for API communication.
 */

export { ApiError } from "./errors";
export { setDeprecationHandler, handleDeprecationHeaders, generateRequestId } from "./headers";
export { assertRequestIdHeader, isRequestIdStrict } from "./assertRequestId";
export { apiFetch, get, post, patch, put, del } from "./apiFetch";
export { noteDeprecationFromResponse, resetDeprecationWarning } from "./deprecationBanner";
export type { ApiFetchOptions, PaginatedResponse, Timestamped, IndexedEntity } from "./types";
export type { DeprecationEvent } from "./headers";
export type { RequestIdAssertMode, RequestIdAssertOptions } from "./assertRequestId";
