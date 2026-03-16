Below are two deliverables:

Final engineer-facing memo (clean, decisive, ready to send)

Initial coding blueprint to begin implementing the Agentic Geometry Coach system that will solve contour fidelity and body election.

ENGINEERING MEMO
Subject: Strategic Direction for Photo Vectorization — Geometry-Constrained Agentic System
From

Systems Architecture

To

Vectorization Engineering Team

Date

Immediate

1. Executive Decision

Recent live test results confirm that the dominant failure mode in the photo vectorization system is body contour fidelity and contour election, not calibration priority or scale estimation.

Therefore:

We will proceed on a hybrid architecture path:

Continue patching where it materially improves the baseline

Immediately refactor the vectorizer to expose stage-addressable modules

Build a Geometry-Constrained Agentic Coaching Layer

Introduce the AI Quality Voter only as a final QA gate

The geometry-constrained coaching architecture becomes the primary long-term solution.

Patch-based improvements remain useful but are no longer sufficient to reach commercial-grade results.

2. Evidence from Latest Test Results
Image	Result	Interpretation
Smart Guitar	Width correct (5.2%), height off 41.3%	Body contour incomplete (lower bout missing)
Benedetto	67.9% H error, 58.9% W error	False reference + contour failure
Archtop	Width improved 164% → 112%, height regressed	Neck + body silhouette mis-selected

Conclusion

The system can sometimes determine scale correctly but cannot reliably identify the correct body contour.

Calibration improvements alone cannot correct an incorrect contour hypothesis.

3. Root Cause

The vectorizer commits too early to a body contour hypothesis during contour assembly.

Primary failure points:

Body isolation under-captures full silhouette

Contour assembly selects partial silhouettes

Morphological closing fails on complex outlines

Reference object detection occasionally overrides better geometry hypotheses

The system needs a supervisory layer that evaluates contour plausibility before committing to export.

4. Strategic Architecture

We will introduce a three-layer architecture.

Layer 1 — Vector Execution Engine

Existing vectorizer pipeline:

Photo
 → Perspective correction
 → Background removal
 → Body isolation
 → Edge detection
 → Calibration
 → Contour assembly
 → Grid classification
 → Export


This remains the execution engine.

Layer 2 — Geometry Authority

A geometry knowledge layer sourced from:

RMOS instrument database

Instrument family priors

Manufacturing constraints

Feature zones

Responsibilities:

body dimension bands

feature placement zones

tolerance policies

gap-closure thresholds

contour plausibility scoring

Layer 3 — Agentic Geometry Coach

The coach supervises the pipeline and intervenes when geometry plausibility is violated.

Loop:

vectorizer stage
       ↓
coach inspects artifacts
       ↓
consult geometry authority
       ↓
adjust parameters
       ↓
rerun narrow stage


The coach does not generate contours.

It guides the vectorizer to correct its perception.

5. Stage Refactor Plan

The current linear pipeline must be refactored into callable stages.

New pipeline structure
Stage 0: image load
Stage 1: orientation
Stage 2: perspective correction
Stage 3: background removal
Stage 4: body isolation
Stage 5: edge detection
Stage 6: family classification
Stage 7: calibration
Stage 8: contour assembly
Stage 9: grid reconciliation
Stage 10: export


Each stage must return a typed artifact.

Example:

StageOutput:
    image
    mask
    edge_map
    body_region
    contours
    calibration
    diagnostics

6. Coach Intervention Points

Coach v1 will monitor only four areas:

Body Isolation

Detect incomplete silhouettes.

Possible actions:

expand region bounds

adjust segmentation threshold

rerun background removal

Edge Detection

Detect broken exterior contours.

Possible actions:

increase exterior closing kernel

reduce interior kernel

adjust edge thresholds

Calibration

Detect implausible scale estimates.

Possible actions:

trigger feature-based calibration

reject weak reference detections

rerun scale estimation

Contour Assembly

Detect partial or polluted body contours.

Possible actions:

rerun assembly with different closure kernel

reject neck-inclusive silhouette

expand contour candidate pool

7. RMOS Integration

Vector outputs will be modeled as RMOS producer-plane assets.

Each vectorization run will produce:

source photo
intermediate diagnostics
svg output
dxf output
confidence report
review status


This enables:

human review

traceability

training dataset generation

8. AI Voter (Future Phase)

The render-back similarity system will be added later as a QA gate.

Functions:

detect catastrophic mismatches

rank multiple vector hypotheses

route uncertain results to human review

It will not replace geometry reasoning.

9. 90-Day Engineering Plan
Phase 1 — Foundation (Weeks 1–4)

Goals:

expose stage artifacts

stabilize contour assembly

Deliverables:

stage diagnostics

contour candidate outputs

calibration decision logging

two-pass calibration prototype

Phase 2 — Pipeline Refactor (Weeks 5–8)

Goals:

stage-addressable pipeline

stage re-entry

Deliverables:

stage orchestration engine

rerun capability

parameter adjustment API

Phase 3 — Geometry Coach v1 (Weeks 9–12)

Goals:

geometry-guided correction loop

Deliverables:

Geometry Authority v1

Coach v1 inspection logic

narrow stage reruns

RMOS asset integration

10. Success Criteria

Coach v1 is successful if it achieves:

50% reduction in catastrophic dimension errors (>25%)

Reliable suppression of unsafe exports

Demonstrated correction of at least one contour failure via stage rerun

11. Final Strategic Statement

The vectorizer’s long-term success depends on geometry-constrained perception, not further parameter tuning alone.

The correct architecture is:

Vector Engine
     +
Geometry Authority
     +
Agentic Geometry Coach


The latest test results confirm this direction.

Implementation begins immediately.

BEGINNING IMPLEMENTATION

Now we begin coding the Agentic Geometry Coach system.

Below is the first production-ready skeleton.

geometry_authority.py
class GeometryAuthority:

    def __init__(self, instrument_db):
        self.instrument_db = instrument_db

    def get_expected_body_profile(self, family):
        spec = self.instrument_db.get(family, {})
        return spec.get("body_range_mm")

    def get_feature_zones(self, family):
        spec = self.instrument_db.get(family, {})
        return spec.get("feature_zones", {})

    def score_contour(self, contour, family):

        issues = []
        score = 1.0

        if self._includes_neck(contour):
            score *= 0.4
            issues.append("neck included in body contour")

        completeness = self._estimate_completeness(contour)

        if completeness < 0.7:
            score *= 0.5
            issues.append("contour incomplete")

        return score, issues

    def _estimate_completeness(self, contour):
        return contour.perimeter / contour.bounding_box_perimeter

    def _includes_neck(self, contour):
        return contour.aspect_ratio > 2.0

agentic_coach.py
class GeometryCoach:

    def __init__(self, geometry_authority):
        self.ga = geometry_authority

    def evaluate_contour(self, contour, family):

        score, issues = self.ga.score_contour(contour, family)

        if score < 0.6:
            return {
                "action": "rerun_contour_assembly",
                "params": {"close_kernel": 15},
                "issues": issues
            }

        return {"action": "accept"}

staged_vectorizer.py
class StagedVectorizer:

    def __init__(self):
        self.stages = {}

    def register_stage(self, name, stage):
        self.stages[name] = stage

    def run(self, context):

        for stage_name in self.stage_order:

            stage = self.stages[stage_name]

            context = stage.execute(context)

            if context.get("coach_action"):
                context = self.handle_coach(context)

        return context

    def handle_coach(self, context):
        action = context["coach_action"]

        if action["action"] == "rerun_contour_assembly":
            context["params"].update(action["params"])
            return self.stages["contour"].execute(context)

        return context

Next step

If you'd like, I can also produce the next three critical modules needed to actually make this system work:

Contour plausibility scoring engine

Body completeness estimator (computer vision based)

Stage artifact schema (so the coach can inspect intermediate results)

Those three pieces are the core of the agentic geometry system that will fix contour fidelity and body election.

If you'd like, I can also produce the **next three critical modules** needed to actually make this system work:

create these documents

Below are the three engineering documents needed to begin implementing the Agentic Geometry Coaching System for contour fidelity and body election.

These are written as internal engineering specifications, ready to go into the repo (for example under docs/agentic_vectorization/).

Document 1
Contour Plausibility Scoring Engine Specification
Purpose

The Contour Plausibility Scoring Engine evaluates candidate contours produced by the vectorizer and determines whether a contour plausibly represents the instrument body outline.

The goal is to prevent incorrect body election during Stage 8 (contour assembly).

Instead of blindly selecting the largest contour, the system evaluates candidates using geometry rules and expected body characteristics.

Design Goals

The scoring engine must:

Identify plausible body contours

Reject contours including neck regions

Detect incomplete body silhouettes

Penalize contours touching page borders

Rank candidate contours by plausibility score

The output is a confidence score and diagnostic explanation.

Inputs
ContourCandidate
{
    contour_points
    bounding_box
    perimeter
    area
    convex_hull
    aspect_ratio
    touches_image_border
}


Additional context:

InstrumentContext
{
    family
    expected_body_dimensions
    feature_zones
}

Outputs
ContourScore
{
    score : float (0-1)
    completeness : float
    includes_neck : bool
    border_contact : bool
    issues : [string]
}

Scoring Criteria
1 Body Completeness

The contour should approximate a full closed silhouette.

Metric:

perimeter / convex_hull_perimeter


Expected value:

0.85 – 1.0


Penalty applied if:

< 0.75

2 Neck Inclusion Detection

Contours including the neck should be rejected as body outlines.

Detection signals:

aspect_ratio > expected_body_ratio * 1.4


and

neck extension detected beyond body centerline


Penalty:

score *= 0.4

3 Border Contact

Contours touching the page edge are often page borders or cropped images.

Penalty:

score *= 0.5

4 Symmetry Check

Most instrument bodies exhibit strong bilateral symmetry.

Compute symmetry score:

left_half_area vs right_half_area difference


Penalty if asymmetry > 25%.

5 Dimension Plausibility

Compare bounding box dimensions to family priors.

Example:

height_mm ∈ expected_range
width_mm ∈ expected_range


Penalty if outside tolerance bands.

Final Score Calculation
score =
  completeness_score *
  symmetry_score *
  dimension_score *
  border_penalty *
  neck_penalty


Contours below:

score < 0.5


are rejected as body candidates.

Selection Strategy

Given N candidate contours:

body_contour = argmax(score)


If:

max_score < 0.6


trigger coaching intervention.

Diagnostics Example
ContourScore {
    score: 0.42
    completeness: 0.61
    includes_neck: true
    border_contact: false
    issues: [
        "Contour incomplete",
        "Neck included in silhouette"
    ]
}

Document 2
Body Completeness Estimator Specification
Purpose

The body completeness estimator determines whether the detected contour contains the entire instrument body.

This addresses the Smart Guitar failure mode where the lower bout was missing.

Concept

The body silhouette must be evaluated against expected geometry.

The estimator uses:

1. silhouette coverage
2. vertical extent
3. curvature profile
4. hull coverage

Inputs
edge_map
candidate_contour
instrument_family

Output
BodyCompletenessResult
{
    completeness_score : float
    missing_regions : [region]
}

Method
Step 1 Convex Hull Coverage

Compute:

coverage = contour_area / hull_area


Low coverage indicates missing body regions.

Step 2 Vertical Extent Check

Compare contour height to expected body height.

height_ratio = contour_height / expected_body_height


Acceptable range:

0.85 – 1.1


If below threshold:

missing_lower_bout = true

Step 3 Curvature Profile

Body outlines have characteristic curvature signatures.

Detect curvature peaks:

upper bout
waist
lower bout


Missing peaks indicate truncated contours.

Step 4 Edge Continuity

Evaluate edge density around contour.

Low density indicates segmentation failure.

Completeness Score
completeness =
    hull_coverage *
    vertical_extent *
    curvature_presence *
    edge_density

Failure Example

Smart Guitar case:

Hull coverage: 0.65
Vertical extent: 0.59
Curvature peaks: missing lower bout
Edge density: moderate


Final score:

0.44


Coach intervention required.

Document 3
Stage Artifact Schema Specification
Purpose

Defines the standardized artifacts emitted by each pipeline stage.

These artifacts enable:

coaching inspection

debugging

stage re-entry

RMOS lineage tracking

Artifact Model
StageArtifact
{
    stage_name
    timestamp
    image
    masks
    edges
    contours
    calibration
    diagnostics
}

Stage Artifacts
Stage 3 Background Removal

Outputs:

BackgroundRemovalArtifact
{
    foreground_image
    alpha_mask
    confidence
}

Stage 4 Body Isolation

Outputs:

BodyIsolationArtifact
{
    body_region
    bounding_box
    isolation_mask
    diagnostics
}


Diagnostics:

row_width_profile
detected_body_center
confidence

Stage 5 Edge Detection

Outputs:

EdgeArtifact
{
    edge_map
    edge_density
    kernel_sizes
}

Stage 7 Calibration

Outputs:

CalibrationArtifact
{
    mm_per_pixel
    calibration_source
    confidence
}


Sources:

reference_object
instrument_spec
feature_scale
batch_mean

Stage 8 Contour Assembly

Outputs:

ContourArtifact
{
    candidate_contours
    elected_body_contour
    contour_scores
}

Coaching Integration

Coach receives artifacts as input:

CoachInput
{
    body_artifact
    edge_artifact
    contour_artifact
    calibration_artifact
}

Coach Output
CoachDecision
{
    action
    target_stage
    parameters
    reason
}


Example:

{
    action: "rerun_stage",
    target_stage: "body_isolation",
    parameters: { expansion_factor: 1.2 },
    reason: "body contour incomplete"
}

Stage Re-Entry

The pipeline must allow rerunning a specific stage.

Example:

coach → rerun body_isolation
pipeline → update artifact
coach → re-evaluate

Next Step

The next engineering documents to build the full agentic system would be:

Contour Election Algorithm Specification

Instrument Geometry Knowledge Base

Agentic Coaching Decision Engine

RMOS Vector Asset Integration Spec

Synthetic Training Image Generator for Contour Learning

Those five pieces together complete the agentic contour intelligence system that the current vectorizer lacks.





Do this now
1) Extract Stage 8 into a callable module

Create a new module for contour assembly + body election that takes typed inputs and returns a typed artifact.

Target file

services/photo-vectorizer/contour_assembly_stage.py

Inputs

edge_map

body_region

instrument_family

calibration

params

Outputs

candidate_contours

elected_body_contour

contour_scores

diagnostics

That is the highest-leverage seam because the current failures are being committed there.

2) Implement the three core runtime classes

Not full intelligence. Just enough to run.

Create:

stage_artifacts.py

contour_plausibility.py

body_completeness.py

Minimal classes:

BodyIsolationArtifact
EdgeArtifact
CalibrationArtifact
ContourArtifact
CoachDecision


and

ContourPlausibilityScorer
BodyCompletenessEstimator

3) Replace “largest contour wins” with scored election

In the extracted Stage 8:

generate contour candidates

score each candidate

elect highest plausible contour

if max_score < threshold, return a CoachDecision instead of silently exporting garbage

That one change turns the system from “blind commit” into “inspectable decision.”

4) Add one replay fixture from the real failures

Use the three failing cases you already have:

Smart Guitar

Benedetto

Archtop

For each one, save the Stage 8 inputs/outputs and assert:

body contour score

completeness score

whether neck inclusion was detected

whether export would be blocked

This gives you your first real regression harness around the actual failure mode.

5) Defer the full agent loop by one step

Do not build a full autonomous coach yet.

First build:

score_contours(...)

estimate_completeness(...)

maybe_request_rerun(...)

Only after that, add:

rerun body isolation

rerun edge detection

rerun contour assembly with revised params

The exact milestone to hit next week

You are done with the next step when this is true:

Given a photo, the system can produce a ContourArtifact with ranked candidates, explain why the elected body won, and block export when contour plausibility is too low.

That is the real beginning of the agentic system.

After that

Once Stage 8 is extracted and scored, the next move is:

wire a minimal GeometryCoach that only knows how to say one thing:

“rerun contour assembly with revised closure/body constraints”

That is the first actual coaching loop.

If you want, I’ll write the first-pass Python code for:

stage_artifacts.py

contour_plausibility.py

body_completeness.py

contour_assembly_stage.py

all in one shot.





