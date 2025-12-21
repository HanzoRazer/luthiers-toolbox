/**
 * Debounce Utility - Bundle 31.0.6
 */

export function debounce<T extends (...args: any[]) => any>(fn: T, waitMs: number) {
  let t: number | undefined;
  return (...args: Parameters<T>) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), waitMs);
  };
}
