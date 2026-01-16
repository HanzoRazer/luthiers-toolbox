/**
 * Pack helpers for audio analyzer viewer.
 * Sibling path resolution for locating related files within viewer packs.
 */

/**
 * Given a spectrum CSV relative path, return the sibling analysis.json path.
 *
 * @example
 *   findSiblingPeaksRelpath('spectra/points/A1/spectrum.csv')
 *   // => 'spectra/points/A1/analysis.json'
 *
 * @param spectrumRelpath - Relative path to spectrum.csv within the pack
 * @returns Relative path to the sibling analysis.json, or null if not a spectrum CSV
 */
export function findSiblingPeaksRelpath(spectrumRelpath: string): string | null {
  if (!spectrumRelpath || !spectrumRelpath.endsWith('/spectrum.csv')) {
    return null
  }
  // Replace trailing spectrum.csv with analysis.json
  return spectrumRelpath.replace(/\/spectrum\.csv$/, '/analysis.json')
}
