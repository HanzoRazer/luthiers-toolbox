# Wave 7 Boundary Memo

**Title:** Boundary Between Measurement Viewer (Wave 6A / 6B.1) and Interpretation (Wave 7+)
**Status:** Normative governance document
**Applies to:** `AudioAnalyzerViewer` and all renderers under `packages/client/src/tools/audio_analyzer/`

## Purpose

Wave 6A / 6B.1 establishes the Viewer as a **measurement evidence browser** with **linked navigation**. This memo defines the **boundary** where changes stop being "view + correlate" and become **interpretation**. Interpretation is not forbidden—but it must be explicitly declared as **Wave 7+**, reviewed under different criteria, and ideally isolated behind a mode flag or separate tool surface.

## Definitions

**Measurement display**: Rendering exported artifacts and their fields as-is (charts/tables/media), plus non-analytic UX conveniences (highlighting, cursor sync, navigation).
**Correlation (allowed in 6A/6B.1)**: Showing the *same user-selected coordinate* (e.g., `freqHz`) across multiple charts without creating judgments.
**Interpretation (Wave 7+)**: Any logic that derives meaning, preference, risk, ranking, or recommended action from one or more measurements.

## The Allowed Set (Wave 6A / 6B.1)

The following are explicitly allowed and remain in-scope:

* Rendering exporter-provided fields (e.g., `wsi`, `coh_mean`, `phase_disorder`, `admissible`) as charts/tables.
* A shared cursor (`freqHz`) used for **highlighting and navigation** only.
* Click-to-select setting cursor coordinates (e.g., WSI click sets `freqHz` only; spectrum click sets `{pointId, freqHz}`).
* Shading or markers **only when driven by exporter fields** (e.g., admissible shading from `admissible`).
* "Raw evidence" panels showing payload JSON/CSV rows.
* UI conveniences: filtering file list, download PNG, decimation for performance, tooltips that display exported values.

**Invariant:** Selection state is a user cursor and must not contain derived metrics.

## The Boundary (What Triggers Wave 7+)

Any of the following is **interpretation** and therefore **Wave 7+**:

1. **Derived scoring or ranking**

   * Any `score`, `risk`, `severity`, `priority`, `rank`, "best", "worst".
   * Example: `wolfRisk = f(wsi, coh_mean, peaks, ods)`.

2. **Threshold-based claims not present in the exporter**

   * "Wolf if WSI > 0.4", "bad if coh_mean < 0.8", etc., unless the exporter explicitly provides a classification field and you are only displaying it.

3. **Cross-artifact inference / aggregation**

   * Loading peaks from all points to compute "matches", "counts", "likelihood".
   * Example: "how many points have a peak near this frequency" is already a step toward interpretation unless presented purely as an explicit query result with no implied meaning.

4. **Recommendation or action guidance**

   * Any UI that suggests corrective steps, design changes, or "what to do".

5. **Auto-navigation presented as meaning**

   * Any automatic jump that implies causality (e.g., "jump to the most problematic frequency", "open the worst point").

6. **Language that implies judgment**

   * UI copy such as "problem frequency", "danger zone", "good/bad", "safe/unsafe", "wolf likely".

## Required Process for Wave 7+

If a PR crosses the boundary above, it must:

* Declare **"Wave 7+ (interpretation)"** in the PR title or description.
* Document the interpretation rules, their source, and their testability.
* Prefer isolation behind:

  * a feature flag (e.g., "Analysis Mode"), or
  * a separate route/tool, or
  * a separate schema field exported by tap-tone-pi (best: interpretation computed upstream, then merely displayed here).

## Implementation Guardrails

To make drift hard:

* Keep `EvidenceSelection` (or current selection model) **free of derived fields**.
* Any computed value derived from multiple artifacts must live outside selection state and must be explicitly reviewed as Wave 7+.
* Renderers may display, highlight, and navigate—but must not compute interpretive summaries.

## Review Triggers (Fast Checklist)

A reviewer should treat a change as Wave 7+ if it introduces any of:

* new fields named `score`, `risk`, `rank`, `severity`, `recommendation`
* cross-loading multiple points' peaks for inference
* threshold labels ("wolf if…") or judgmental language
* UI that claims "likely cause", "best", "worst", "problem", "safe"

## Summary

Wave 6A / 6B.1 builds a **linked measurement viewer**. Wave 7+ begins when the system starts telling the user what measurements **mean**. That transition must be deliberate, documented, and reviewed under interpretation governance.
