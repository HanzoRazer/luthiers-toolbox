/**
 * Art Placement SDK - Stub module
 *
 * TODO: Implement when API endpoint is available
 */

export interface PlacementPreviewRequest {
  params?: Record<string, unknown>;
  ornament?: Record<string, unknown>;
  host?: Record<string, unknown>;
  placement?: Record<string, unknown>;
}

export interface PlacementPreviewResponse {
  svg: string;
}

/**
 * Preview placement as SVG
 *
 * @param _req - Placement preview request (unused, stub)
 * @returns Promise resolving to empty SVG placeholder
 */
export async function previewPlacementSvg(
  _req: PlacementPreviewRequest
): Promise<PlacementPreviewResponse> {
  console.warn("previewPlacementSvg: API endpoint not implemented");
  return { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>' };
}
