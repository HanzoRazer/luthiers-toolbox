// captureElementScreenshot.ts
// B22.12: Screenshot capture helper (stub)
//
// Current implementation: Serializes SVG element to data:image/svg+xml URL
// Future: Can be replaced with html2canvas or dom-to-image for PNG capture

/**
 * Capture an element containing SVG as an SVG data URL.
 *
 * This is a lightweight approach that preserves vector quality.
 * For bitmap (PNG) capture, replace this with html2canvas or dom-to-image.
 *
 * @param rootEl - Root element to search for SVG
 * @returns SVG data URL or undefined if no SVG found
 */
export async function captureElementAsSvgDataUrl(
  rootEl: HTMLElement | null
): Promise<string | undefined> {
  if (!rootEl) return undefined;

  const svgEl = rootEl.querySelector("svg");
  if (!svgEl) return undefined;

  try {
    // Clone to avoid modifying original
    const clonedSvg = svgEl.cloneNode(true) as SVGElement;

    // Ensure viewBox is set for proper scaling
    if (!clonedSvg.hasAttribute("viewBox")) {
      const bbox = svgEl.getBBox();
      clonedSvg.setAttribute(
        "viewBox",
        `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`
      );
    }

    // Add xmlns if missing (required for standalone SVG)
    if (!clonedSvg.hasAttribute("xmlns")) {
      clonedSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    }

    // Serialize to string
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clonedSvg);

    // Encode to base64 data URL
    const encoded = window.btoa(unescape(encodeURIComponent(svgString)));
    return `data:image/svg+xml;base64,${encoded}`;
  } catch (error) {
    console.error("Failed to capture SVG screenshot:", error);
    return undefined;
  }
}

/**
 * Capture an element as a PNG data URL using html2canvas.
 *
 * NOTE: Requires html2canvas library to be installed:
 * npm install html2canvas
 *
 * @param rootEl - Element to capture
 * @returns PNG data URL or undefined on error
 */
export async function captureElementAsPngDataUrl(
  rootEl: HTMLElement | null
): Promise<string | undefined> {
  if (!rootEl) return undefined;

  try {
    // Dynamic import to avoid bundling if not used
    const html2canvas = (await import("html2canvas")).default;

    const canvas = await html2canvas(rootEl, {
      backgroundColor: "#ffffff",
      scale: 2, // Higher quality
      logging: false,
    });

    return canvas.toDataURL("image/png");
  } catch (error) {
    console.warn(
      "html2canvas not available or capture failed. Install with: npm install html2canvas",
      error
    );
    return undefined;
  }
}

/**
 * Capture element screenshot with automatic fallback.
 *
 * Tries PNG capture first (if html2canvas available), falls back to SVG.
 *
 * @param rootEl - Element to capture
 * @param preferredFormat - 'png' or 'svg' (default: 'svg')
 * @returns Data URL or undefined
 */
export async function captureElementScreenshot(
  rootEl: HTMLElement | null,
  preferredFormat: "png" | "svg" = "svg"
): Promise<string | undefined> {
  if (preferredFormat === "png") {
    const png = await captureElementAsPngDataUrl(rootEl);
    if (png) return png;
    // Fallback to SVG if PNG fails
    return captureElementAsSvgDataUrl(rootEl);
  }

  return captureElementAsSvgDataUrl(rootEl);
}
