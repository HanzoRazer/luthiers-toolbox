// SDK Error Types & Normalizer
// H8.2.1: Consistent error handling with request-id correlation

export type StrictRequestIdMode = "off" | "warn" | "error";

export type SdkErrorInfo = {
  kind: "http" | "network" | "parse" | "unknown";
  message: string;              // UI-safe message
  status?: number;
  url?: string;
  method?: string;
  requestId?: string;           // key: surfaced for incident response
  details?: unknown;            // optionally stash raw payload
};

export class SdkHttpError extends Error {
  public readonly info: SdkErrorInfo;

  constructor(info: SdkErrorInfo) {
    super(info.message);
    this.name = "SdkHttpError";
    this.info = info;
  }
}

/**
 * Convert unknown thrown values into a consistent UI-safe error object.
 */
export function normalizeSdkError(err: unknown): SdkErrorInfo {
  if (err instanceof SdkHttpError) return err.info;

  if (err instanceof Error) {
    // Fetch/network errors often come through as TypeError("Failed to fetch")
    const msg = err.message || "Request failed.";
    const kind =
      msg.toLowerCase().includes("fetch") || msg.toLowerCase().includes("network")
        ? "network"
        : "unknown";
    return { kind, message: msg };
  }

  return { kind: "unknown", message: "Unexpected error." };
}
