#!/usr/bin/env python3
"""Preserve dormant client Axios capabilities without changing production.

Read-only with respect to production source. Copies bytes only when
``--archive-root`` is set and ``--dry-run`` is not. Never deletes a source
file. Reachability facts come from ``client_axios_reachability``. This module
does not parse imports itself.

DORMANT_PRESERVE is provenance, not permission to delete. Axios stays installed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import client_axios_reachability as scan  # noqa: E402

ORDER_ID = "CLIENT-AXIOS-DORMANT-PRESERVATION-024"
SOURCE_COMMIT = "cfaf07751110d99b3539647e877c2ffd80f4f29c"
CLIENT_SRC = "packages/client/src"
PRESERVATION_STATUS = "PRESERVED_COPY_PRODUCTION_RETAINED"
CANONICAL = "DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED"
DORMANT = "DORMANT_PRESERVE"
ENTRIES = ["main.ts", "App.vue", "router/index.ts"]

CHARACTERIZATION_MOCKS = {
    "packages/client/src/components/art/__tests__/RosetteComparePanel.spec.ts",
    "packages/client/src/components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts",
    "packages/client/src/views/art/__tests__/RiskDashboardCrossLab.spec.ts",
    "packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts",
    "packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardRequestOrder.spec.ts",
}

# A route that is absent, or that this order did not re-check, is not
# permission to delete the client that calls it.
def preservation_status_for_route(route_found: bool | None) -> str:
    del route_found
    return PRESERVATION_STATUS


class PreservationError(RuntimeError):
    """The closure is not safe to copy."""


@dataclass(frozen=True)
class ArchivedFile:
    path: str
    role: str
    serves: tuple[str, ...]


@dataclass(frozen=True)
class Exclusion:
    path: str
    reason: str
    kind: str  # caller | dependency


@dataclass(frozen=True)
class Cluster:
    cluster_id: str
    summary: str
    disposition: str
    next_adjudication: str
    files: tuple[ArchivedFile, ...]
    exclusions: tuple[Exclusion, ...]
    forbidden_in_importers: tuple[str, ...]


def _p(rel: str) -> str:
    return f"{CLIENT_SRC}/{rel}"


def _file(rel: str, role: str, *serves: str) -> ArchivedFile:
    return ArchivedFile(_p(rel), role, tuple(_p(item) for item in serves))


N15 = "api/n15.ts"
N16 = "api/n16.ts"
SAW = "api/sawLab.ts"
JOB = "api/job_int.ts"
ADVISORY = "components/ai/aiAdvisoryApi.ts"
SELECTOR = "components/art/ArtPresetSelector.vue"
MANAGER = "views/ArtPresetManager.vue"
JOB_DETAIL = "views/ArtJobDetail.vue"
TIMELINE = "views/ArtJobTimeline.vue"
INSIGHTS = "components/cam/CamJobInsightsSummaryPanel.vue"
INSIGHTS_JOB = "components/cam/CamJobInsightsPanel.vue"
HISTORY_ACTIONS = "components/art/rosette_compare_history/composables/useRosetteCompareActions.ts"
ART_ACTIONS = "views/rosette_compare/composables/useRosetteCompareActions.ts"
ART_HISTORY = "views/rosette_compare/composables/useRosetteCompareHistory.ts"
CANONICAL_API = "components/art/rosette-compare/useRosetteCompareApi.ts"
RISK_BUCKETS = "views/art/risk-dashboard/useRiskBuckets.ts"
RISK_EXPORTS = "views/art/risk-dashboard/useRiskExports.ts"
RISK_DETAILS = "views/art/risk-dashboard/useRiskBucketDetails.ts"


def _clusters() -> tuple[Cluster, ...]:
    cam_serves_n15 = (N15,)
    cam_serves_n16 = (N16,)
    cam_serves_saw = (SAW,)
    cam_serves_job = (JOB,)
    history_cmp = (HISTORY_ACTIONS,)
    history_art = (ART_ACTIONS, ART_HISTORY)
    canonical_serves = (CANONICAL_API,)
    risk_serves = (RISK_BUCKETS, RISK_EXPORTS, RISK_DETAILS)
    return (
        Cluster(
            "cam-utility-clients",
            "Four dormant CAM utility clients. They share a preservation cluster and stay separate endpoint families. Preserving them together is not one deletion.",
            DORMANT,
            "Review n15, n16, sawLab, and job_int separately before any removal. /cam/adaptive2 is not /api/cam/adaptive2. /api/cam/job-int/favorites is not /api/jobint/favorites. sawLab is not the live GET /api/joblog/saw_runs store.",
            (
                _file(N15, "importer", *cam_serves_n15),
                _file("components/toolbox/BackplotGcode.vue", "caller", *cam_serves_n15),
                _file(N16, "importer", *cam_serves_n16),
                _file("components/toolbox/AdaptiveBench.vue", "caller", *cam_serves_n16),
                _file(SAW, "importer", *cam_serves_saw),
                _file("views/saw_lab_dashboard/composables/useSawDashboard.ts", "caller", *cam_serves_saw),
                _file("views/saw_lab_dashboard/TelemetryMetricsPanel.vue", "type-caller", *cam_serves_saw),
                _file("views/saw_lab_dashboard/composables/sawRiskStyles.ts", "type-caller", *cam_serves_saw),
                _file("views/saw_lab_dashboard/composables/useSawDashboardFilters.ts", "type-caller", *cam_serves_saw),
                _file("views/saw_lab_dashboard/composables/useSawDashboardModals.ts", "type-caller", *cam_serves_saw),
                _file("views/saw_lab_dashboard/composables/useSawRiskActions.ts", "type-caller", *cam_serves_saw),
                _file(JOB, "importer", *cam_serves_job),
                _file("components/cam/composables/useJobIntHistoryLoad.ts", "caller", *cam_serves_job),
                _file("components/cam/composables/useJobIntHistoryActions.ts", "caller", *cam_serves_job),
                _file("components/cam/composables/jobIntHistoryTypes.ts", "type-caller", *cam_serves_job),
            ),
            (
                Exclusion(
                    _p("components/toolbox/ArtStudioCAM.vue"),
                    "Unmounted shell that mounts BackplotGcode.vue and AdaptiveBench.vue beside other toolbox tools. Those two callers are archived. The shell is not an Axios importer.",
                    "caller",
                ),
                Exclusion(
                    _p("views/saw_lab_dashboard/composables/index.ts"),
                    "Re-exports the archived saw-dashboard composables and does not import api/sawLab.ts. SawLabDashboard.vue is unmounted and is not an Axios importer.",
                    "caller",
                ),
                Exclusion(
                    _p("views/saw_lab_dashboard/RunDetailModal.vue"),
                    "Imports TelemetryMetricsPanel.vue for display and does not import api/sawLab.ts. The panel's type import is archived with the saw client.",
                    "caller",
                ),
                Exclusion(
                    _p("components/cam/composables/index.ts"),
                    "Re-exports the job-int history composables together with CamPipeline and CamIssues composables the pipeline runner evaluates. It adds no Axios call. Copying the barrel would mix live pipeline exports into this archive. The job-int callers are archived.",
                    "caller",
                ),
                Exclusion(
                    _p("components/cam/composables/useJobIntHistoryClone.ts"),
                    "Imports jobIntHistoryTypes for the clone modal and does not call api/job_int.ts. The Axios callers are useJobIntHistoryLoad.ts and useJobIntHistoryActions.ts.",
                    "caller",
                ),
                Exclusion(
                    _p("components/cam/composables/useJobIntHistoryState.ts"),
                    "Imports jobIntHistoryTypes for history state and does not call api/job_int.ts.",
                    "caller",
                ),
                Exclusion(
                    _p("components/cam/composables/useJobIntHistoryStats.ts"),
                    "Imports jobIntHistoryTypes for history stats and does not call api/job_int.ts.",
                    "caller",
                ),
                Exclusion(
                    _p("sdk/rmos/runs.ts"),
                    "useSawRiskActions imports addOverride from the live RMOS SDK. The SDK is not the saw Axios client. The composable is archived.",
                    "dependency",
                ),
            ),
            (
                "/api/compare/",
                "/api/art/presets",
                "/ai/advisories",
                "/api/cam/adaptive2",
            ),
        ),
        Cluster(
            "ai-advisory",
            "POST /ai/advisories/request, with the Pinia store and the dormant AiAdvisoryPanel. The renderer tree does not call this client.",
            DORMANT,
            "Decide later whether to mount AiAdvisoryPanel. Do not remove the client or the dependency in this preservation order.",
            (
                _file(ADVISORY, "importer", ADVISORY),
                _file("stores/aiAdvisoryStore.ts", "caller", ADVISORY),
                _file("components/ai/AiAdvisoryPanel.vue", "panel", ADVISORY),
            ),
            (),
            ("/api/compare/", "/api/art/"),
        ),
        Cluster(
            "art-presets-jobs",
            "Preset selector, preset CRUD, job detail, and the job timeline. One commercial/art workflow. The timeline's reports_index GET stays here and is not a risk-dashboard /api/compare/risk_* call.",
            DORMANT,
            "Decide later whether to adopt the selector, the manager, job detail, or the timeline. The art component barrel was not archived because it also re-exports live studio components.",
            (
                _file(SELECTOR, "importer", SELECTOR),
                _file(MANAGER, "importer", MANAGER),
                _file(JOB_DETAIL, "importer", JOB_DETAIL),
                _file(TIMELINE, "importer", TIMELINE),
            ),
            (
                Exclusion(
                    _p("components/art/index.ts"),
                    "Only direct caller of ArtPresetSelector.vue, and it also re-exports ArtStudioRosette, ArtStudioInlay, ArtStudioBracing, ConfidenceBadge, and ConfidenceDetails. Those exports are not this workflow. The selector source is archived.",
                    "caller",
                ),
                Exclusion(
                    _p("composables/useConfirm.ts"),
                    "Shared confirm dialog used by live screens. ArtPresetManager.vue is archived. The helper is not an art-preset contract.",
                    "dependency",
                ),
            ),
            ("/api/compare/risk_", "/api/compare/baselines", "/api/compare/history", "/api/compare/diff"),
        ),
        Cluster(
            "cam-insights",
            "GET /api/cam/job_log/insights list client, archived beside the competing per-job api() client. The two URLs are not interchangeable.",
            DORMANT,
            "Keep the list GET and the per-job api() client distinct. Do not delete either because the other exists.",
            (
                _file(INSIGHTS, "importer", INSIGHTS),
                _file(INSIGHTS_JOB, "competing-client", INSIGHTS),
            ),
            (
                Exclusion(
                    _p("services/apiBase.ts"),
                    "Shared api() helper imported by CamJobInsightsPanel.vue. The panel is archived so the per-job URL stays next to the list client. The helper is live infrastructure.",
                    "dependency",
                ),
            ),
            ("/api/cam/job_log/insights/${", "/api/compare/"),
        ),
        Cluster(
            "rosette-history",
            "Two dormant history contracts in one preservation cluster: GET /api/compare/history, and the art-rosette job compare history. Neither is the canonical baseline/diff client.",
            DORMANT,
            "Review /api/compare/history and the art-rosette snapshot history as separate contracts. Do not treat either as useRosetteCompareApi.ts, and do not treat /api/compare/lab as either of them.",
            (
                _file(HISTORY_ACTIONS, "importer", *history_cmp),
                _file("components/art/rosette_compare_history/composables/rosetteCompareTypes.ts", "type", *history_cmp),
                _file("components/art/rosette_compare_history/composables/index.ts", "barrel", *history_cmp),
                _file("components/art/rosette_compare_history/composables/useRosetteCompareState.ts", "caller-support", *history_cmp),
                _file("components/art/rosette_compare_history/composables/useRosetteCompareStats.ts", "caller-support", *history_cmp),
                _file("components/art/rosette_compare_history/composables/useRosetteCompareSparklines.ts", "caller-support", *history_cmp),
                _file("components/art/rosette_compare_history/composables/useRosetteComparePresets.ts", "caller-support", *history_cmp),
                _file("components/art/rosette_compare_history/GlobalSparklines.vue", "view-part", *history_cmp),
                _file("components/art/rosette_compare_history/PresetSparklines.vue", "view-part", *history_cmp),
                _file("components/art/rosette_compare_history/PairStatsBadges.vue", "view-part", *history_cmp),
                _file("components/art/rosette_compare_history/HistoryTable.vue", "view-part", *history_cmp),
                _file("components/art/RosetteCompareHistory.vue", "view", *history_cmp),
                _file(ART_ACTIONS, "importer", *history_art),
                _file(ART_HISTORY, "importer", *history_art),
                _file("views/rosette_compare/composables/rosetteCompareTypes.ts", "type", *history_art),
                _file("views/rosette_compare/composables/index.ts", "barrel", *history_art),
                _file("views/rosette_compare/composables/useRosetteCompareState.ts", "caller-support", *history_art),
                _file("views/rosette_compare/composables/useRosetteComparePaths.ts", "caller-support", *history_art),
                _file("views/rosette_compare/composables/useRosetteCompareHelpers.ts", "caller-support", *history_art),
                _file("views/rosette_compare/CompareDiffSummary.vue", "view-part", *history_art),
                _file("views/rosette_compare/CompareHistorySidebar.vue", "view-part", *history_art),
                _file("views/rosette_compare/compare_history/RiskMetricsBar.vue", "view-part", *history_art),
                _file("views/rosette_compare/compare_history/SnapshotCard.vue", "view-part", *history_art),
                _file("views/ArtStudioRosetteCompare.vue", "view", *history_art),
            ),
            (
                Exclusion(
                    _p("views/ArtStudioUnified.vue"),
                    "Unrouted shell that mounts RosetteCompareHistory.vue and the canonical RosetteComparePanel.vue. Archiving it here would mix /api/compare/history with the baseline/diff contract.",
                    "caller",
                ),
                Exclusion(
                    _p("utils/downloadBlob.ts"),
                    "Shared download helper used by live labs. The compare-history actions composable is archived.",
                    "dependency",
                ),
            ),
            ("/api/compare/baselines", "/api/compare/diff", "/api/compare/lab"),
        ),
        Cluster(
            "rosette-compare-canonical",
            "Canonical baseline and diff client. CANONICAL_BUT_UNROUTED. The panel no longer imports Axios. This is not /api/compare/history and not /api/compare/lab.",
            CANONICAL,
            "Routing this client is a later order. The production composable stays. Do not mark it retired because a copy exists.",
            (
                _file(CANONICAL_API, "importer", *canonical_serves),
                _file("components/art/RosetteComparePanel.vue", "caller", *canonical_serves),
                _file("components/art/rosette-compare/index.ts", "barrel", *canonical_serves),
                _file("components/art/rosette-compare/useRosetteCompareCanvas.ts", "type-caller", *canonical_serves),
            ),
            (
                Exclusion(
                    _p("views/ArtStudioUnified.vue"),
                    "Unrouted shell that mounts the canonical panel and RosetteCompareHistory.vue. Archiving it here would mix baseline/diff with /api/compare/history.",
                    "caller",
                ),
                Exclusion(
                    _p("components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts"),
                    "Characterization spec. It imports Axios only to mock the canonical client. It is not a production capability and is not one of the 17 importers.",
                    "caller",
                ),
                Exclusion(
                    _p("components/art/__tests__/RosetteComparePanel.spec.ts"),
                    "Characterization spec. It mounts RosetteComparePanel.vue and mocks Axios. It is not a production capability and is not one of the 17 importers.",
                    "caller",
                ),
            ),
            ("/api/compare/history", "/api/art/rosette", "/api/compare/lab"),
        ),
        Cluster(
            "risk-dashboard-canonical",
            "February 22 risk-dashboard composables. CANONICAL_BUT_UNROUTED. The three Axios clients stay in production. Bucket and BucketEntry live on the dashboard components this view uses.",
            CANONICAL,
            "Routing the risk dashboard is a later order. Do not mark the three composables retired. /api/compare/lab is not this contract, and neither is the art timeline reports_index GET.",
            (
                _file(RISK_BUCKETS, "importer", *risk_serves),
                _file(RISK_EXPORTS, "importer", *risk_serves),
                _file(RISK_DETAILS, "importer", *risk_serves),
                _file("views/art/risk-dashboard/riskFormatters.ts", "caller-support", *risk_serves),
                _file("views/art/risk-dashboard/useRiskFilters.ts", "caller-support", *risk_serves),
                _file("views/art/risk-dashboard/useRiskNavigation.ts", "caller-support", *risk_serves),
                _file("views/art/risk-dashboard/index.ts", "barrel", *risk_serves),
                _file("views/art/RiskDashboardCrossLab.vue", "view", *risk_serves),
                _file("components/dashboard/index.ts", "type-barrel", *risk_serves),
                _file("components/dashboard/BucketsTable.vue", "type", *risk_serves),
                _file("components/dashboard/BucketDetailsPanel.vue", "type", *risk_serves),
                _file("components/dashboard/FiltersBar.vue", "view-part", *risk_serves),
            ),
            (
                Exclusion(
                    _p("utils/downloadBlob.ts"),
                    "Shared download helper used by live labs. useRiskExports.ts is archived.",
                    "dependency",
                ),
                Exclusion(
                    _p("components/ui/index.ts"),
                    "Shared UI barrel. RiskDashboardCrossLab.vue imports SavedViewsPanel from it. The risk Axios composables and the Bucket types are archived. The UI kit is not the risk contract.",
                    "dependency",
                ),
                Exclusion(
                    _p("views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts"),
                    "Characterization spec. It imports the risk composables and mocks Axios. It is not a production capability and is not one of the 17 importers.",
                    "caller",
                ),
                Exclusion(
                    _p("views/art/risk-dashboard/__tests__/riskDashboardRequestOrder.spec.ts"),
                    "Characterization spec. It imports the risk composables and mocks Axios. It is not a production capability and is not one of the 17 importers.",
                    "caller",
                ),
                Exclusion(
                    _p("views/art/__tests__/RiskDashboardCrossLab.spec.ts"),
                    "Characterization spec. It mounts RiskDashboardCrossLab.vue and mocks Axios. It is not a production capability and is not one of the 17 importers.",
                    "caller",
                ),
            ),
            ("/api/art/presets", "/api/cam/risk/reports_index", "/api/compare/lab", "/api/compare/baselines", "/api/compare/history"),
        ),
    )


def _operations() -> tuple[dict[str, str], ...]:
    def row(
        cluster: str,
        contract: str,
        path: str,
        method: str,
        endpoint: str,
        transport: str,
        archived: str,
        notes: str,
        canonical: str = "",
    ) -> dict[str, str]:
        return {
            "archived": archived,
            "canonical_production_path": canonical,
            "cluster": cluster,
            "contract": contract,
            "deletion_authority": "false",
            "endpoint": endpoint,
            "method": method,
            "notes": notes,
            "production_path": _p(path) if not path.startswith("packages/") else path,
            "transport": transport,
        }

    lab = "composables/useCompareState.ts"
    lab_picker = "components/compare/CompareBaselinePicker.vue"
    adaptive = "components/toolbox/adaptive-bench/useAdaptiveBenchActions.ts"
    favorites = "views/CncProductionView.vue"
    joblog = "stores/useJobLogStore.ts"
    note_keep = "Route presence was not re-litigated. Absence would not authorize deletion."
    rows = [
        row("cam-utility-clients", "gcode-backplot", N15, "POST", "/api/cam/gcode/plot.svg", "axios", "true", note_keep),
        row("cam-utility-clients", "gcode-backplot", N15, "POST", "/api/cam/gcode/estimate", "axios", "true", note_keep),
        row("cam-utility-clients", "gcode-backplot", N15, "POST", "/api/cam/gcode/save_temp", "axios", "true", note_keep),
        row("cam-utility-clients", "adaptive-unprefixed", N16, "POST", "/cam/adaptive2/offset_spiral.svg", "axios", "true", "No /api prefix. Not the adaptive-bench api() client."),
        row("cam-utility-clients", "adaptive-unprefixed", N16, "POST", "/cam/adaptive2/trochoid_corners.svg", "axios", "true", "No /api prefix. Not the adaptive-bench api() client."),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/dashboard/saw/runs", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/dashboard/saw/health", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "POST", "/api/joblog/saw_runs", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/joblog/saw_runs", "axios", "true", "List-with-filters on the Axios client. The live store's bare GET is a different caller."),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/joblog/saw_runs/{id}", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "PUT", "/api/joblog/saw_runs/{id}/status", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "POST", "/api/joblog/saw_runs/{id}/telemetry", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/joblog/saw_runs/{id}/telemetry", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "POST", "/api/learn/ingest", "axios", "true", note_keep),
        row("cam-utility-clients", "saw-lab", SAW, "GET", "/api/learn/health", "axios", "true", note_keep),
        row("cam-utility-clients", "job-int", JOB, "GET", "/api/cam/job-int/log", "axios", "true", note_keep),
        row("cam-utility-clients", "job-int", JOB, "GET", "/api/cam/job-int/log/{runId}", "axios", "true", note_keep),
        row("cam-utility-clients", "job-int", JOB, "POST", "/api/cam/job-int/favorites/{runId}", "axios", "true", "Not /api/jobint/favorites/{runId}."),
        row("ai-advisory", "ai-advisory", ADVISORY, "POST", "/ai/advisories/request", "axios", "true", note_keep),
        row("art-presets-jobs", "art-presets", SELECTOR, "GET", "/api/art/presets", "axios", "true", "Read-only picker. Does not replace preset CRUD."),
        row("art-presets-jobs", "art-presets", MANAGER, "GET", "/api/art/presets", "axios", "true", "CRUD list."),
        row("art-presets-jobs", "art-presets", MANAGER, "POST", "/api/art/presets", "axios", "true", "CRUD create."),
        row("art-presets-jobs", "art-presets", MANAGER, "DELETE", "/api/art/presets/{id}", "axios", "true", "CRUD delete."),
        row("art-presets-jobs", "art-jobs", JOB_DETAIL, "GET", "/api/art/jobs/{jobId}", "axios", "true", note_keep),
        row("art-presets-jobs", "art-jobs", TIMELINE, "GET", "/api/art/jobs", "axios", "true", note_keep),
        row("art-presets-jobs", "art-jobs", TIMELINE, "GET", "/api/cam/risk/reports_index", "axios", "true", "Timeline's second GET. Not the risk-dashboard /api/compare/risk_* family."),
        row("cam-insights", "cam-insights-list", INSIGHTS, "GET", "/api/cam/job_log/insights", "axios", "true", "List. Not the per-job URL."),
        row("cam-insights", "cam-insights-job", INSIGHTS_JOB, "GET", "/api/cam/job_log/insights/{jobId}", "api()", "true", "Competing client. Uses api(), not Axios. Not a substitute for the list."),
        row("rosette-history", "rosette-compare-history", HISTORY_ACTIONS, "GET", "/api/compare/history", "axios", "true", "Distinct from baseline/diff and from /api/compare/lab."),
        row("rosette-history", "art-rosette-history", ART_ACTIONS, "GET", "/api/art/rosette/jobs", "axios", "true", "Art-rosette job compare. Not /api/compare/history."),
        row("rosette-history", "art-rosette-history", ART_ACTIONS, "POST", "/api/art/rosette/compare", "axios", "true", "Art-rosette job compare. Not /api/compare/diff."),
        row("rosette-history", "art-rosette-history", ART_ACTIONS, "POST", "/api/art/rosette/compare/snapshot", "axios", "true", note_keep),
        row("rosette-history", "art-rosette-history", ART_HISTORY, "GET", "/api/art/rosette/compare/snapshots", "axios", "true", note_keep),
        row("rosette-history", "art-rosette-history", ART_HISTORY, "GET", "/api/art/rosette/compare/export_csv", "window.open", "true", "Browser open, not an Axios call. Part of the same history composable."),
        row("rosette-compare-canonical", "rosette-baseline-diff", CANONICAL_API, "GET", "/api/compare/baselines", "axios", "true", "Canonical list.", _p(CANONICAL_API)),
        row("rosette-compare-canonical", "rosette-baseline-diff", CANONICAL_API, "POST", "/api/compare/baselines", "axios", "true", "Canonical save.", _p(CANONICAL_API)),
        row("rosette-compare-canonical", "rosette-baseline-diff", CANONICAL_API, "GET", "/api/compare/baselines/{id}", "axios", "true", "Canonical geometry. Id is encodeURIComponent'd.", _p(CANONICAL_API)),
        row("rosette-compare-canonical", "rosette-baseline-diff", CANONICAL_API, "POST", "/api/compare/diff", "axios", "true", "Canonical diff. Not /api/compare/lab and not /api/compare/history.", _p(CANONICAL_API)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_BUCKETS, "GET", "/api/compare/risk_aggregate", "axios", "true", "Canonical aggregate.", _p(RISK_BUCKETS)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_DETAILS, "GET", "/api/compare/risk_bucket_detail", "axios", "true", "Canonical detail.", _p(RISK_DETAILS)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_EXPORTS, "GET", "/api/compare/risk_bucket_export", "axios", "true", "Blob GET, format=csv.", _p(RISK_EXPORTS)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_EXPORTS, "GET", "/api/compare/risk_bucket_export?format=json", "axios", "true", "Blob GET, format=json. Same path as the CSV export with a different format parameter.", _p(RISK_EXPORTS)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_EXPORTS, "GET", "/api/compare/risk_bucket_report", "axios", "true", "Canonical report.", _p(RISK_EXPORTS)),
        row("risk-dashboard-canonical", "risk-dashboard", RISK_EXPORTS, "GET", "/api/compare/risk_snapshot", "axios", "true", "Canonical snapshot.", _p(RISK_EXPORTS)),
        row("rosette-compare-canonical", "compare-lab", lab, "GET", "/api/compare/lab", "fetch", "false", "Distinct contract owned by useCompareState.ts. Not a Rosette baseline, diff, or history client. Not archived."),
        row("rosette-compare-canonical", "compare-lab", lab_picker, "GET", "/api/compare/lab", "fetch", "false", "Same lab contract, second production owner. Not archived."),
        row("cam-utility-clients", "adaptive-api-prefix", adaptive, "POST", "/api/cam/adaptive2/offset_spiral.svg", "api()", "false", "Competing client. /api prefix. Not a caller of api/n16.ts. Not archived."),
        row("cam-utility-clients", "adaptive-api-prefix", adaptive, "POST", "/api/cam/adaptive2/trochoid_corners.svg", "api()", "false", "Competing client. /api prefix. Not archived."),
        row("cam-utility-clients", "adaptive-api-prefix", adaptive, "POST", "/api/cam/adaptive2/bench", "api()", "false", "Extra bench route on the competing client. api/n16.ts does not call it."),
        row("cam-utility-clients", "jobint-favorites-routed", favorites, "POST", "/api/jobint/favorites/{runId}", "api()", "false", "Routed CNC favorite. Not /api/cam/job-int/favorites. Not archived."),
        row("cam-utility-clients", "saw-joblog-live", joblog, "GET", "/api/joblog/saw_runs", "api()", "false", "Live store covers this GET only. It is not the sawLab Axios client. Not archived."),
    ]
    return tuple(rows)


def clusters() -> tuple[Cluster, ...]:
    found = tuple(sorted(_clusters(), key=lambda item: item.cluster_id))
    ids = [item.cluster_id for item in found]
    if len(ids) != len(set(ids)):
        raise PreservationError("duplicate cluster id")
    return found


def operations() -> tuple[dict[str, str], ...]:
    return _operations()


def copy_bytes(src: Path, dest: Path) -> None:
    """Write dest as the raw bytes of src. Line endings and encoding are kept."""
    data = src.read_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def assert_archive_destination(repo: Path, archive_root: Path) -> None:
    client = (repo / CLIENT_SRC).resolve()
    root = archive_root.resolve()
    if root == client or _inside(root, client):
        raise PreservationError(
            f"archive destination {root} is inside production client source {client}"
        )


def _git_bytes(repo: Path, commit: str, rel: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "cat-file", "blob", f"{commit}:{rel}"],
            cwd=repo,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise PreservationError(f"git cannot read {commit}:{rel}") from exc


def _load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_overlay(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def effective_unresolved(rows: list[dict[str, str]], overlay: dict) -> list[str]:
    retired = {item["path"] for item in overlay["retired_importers"]}
    reclassified = {item["path"] for item in overlay["reclassified_importers"]}
    return sorted(
        row["path"]
        for row in rows
        if row["disposition"] == "UNRESOLVED" and row["path"] not in retired and row["path"] not in reclassified
    )


def production_importers(rows: list[dict[str, str]], overlay: dict, scanned: list[str]) -> list[str]:
    retired = {item["path"] for item in overlay["retired_importers"]}
    extra = set(overlay.get("post_audit_importers") or [])
    expected = sorted(({row["path"] for row in rows} - retired) | extra)
    scanned_full = [f"{CLIENT_SRC}/{rel}" for rel in scanned]
    production = sorted(path for path in scanned_full if path not in CHARACTERIZATION_MOCKS)
    if production != expected:
        raise PreservationError(
            "scanner importers and the inventory overlay disagree: "
            f"only_scanned={sorted(set(production) - set(expected))} "
            f"only_expected={sorted(set(expected) - set(production))}"
        )
    return production


def _src_rel(path: str) -> str:
    prefix = CLIENT_SRC + "/"
    if not path.startswith(prefix):
        raise PreservationError(f"path is outside the client source tree: {path}")
    return path[len(prefix):]


def _caller_index(modules: dict) -> dict[str, list[dict[str, str]]]:
    found: dict[str, dict[str, set[str]]] = {}
    for module in modules.values():
        kinds: dict[str, set[str]] = {}
        for edge in module.imports:
            if not edge.resolved:
                continue
            if edge.type_only:
                kind = "type"
            elif edge.dynamic:
                kind = "dynamic"
            elif edge.side_effect:
                kind = "side-effect"
            else:
                kind = "value"
            kinds.setdefault(edge.resolved, set()).add(kind)
        for _spec, resolved, _mapping, type_only in module.reexports:
            if resolved:
                kinds.setdefault(resolved, set()).add("reexport-type" if type_only else "reexport")
        for resolved, kind_set in kinds.items():
            found.setdefault(resolved, {}).setdefault(module.path, set()).update(kind_set)
    indexed: dict[str, list[dict[str, str]]] = {}
    for resolved, callers in found.items():
        full = f"{CLIENT_SRC}/{resolved}"
        indexed[full] = [
            {"kinds": "+".join(sorted(kinds)), "path": f"{CLIENT_SRC}/{caller}"}
            for caller, kinds in sorted(callers.items())
        ]
    return indexed


def _reachability(src: Path) -> dict[str, dict[str, bool]]:
    modules = scan.load_modules(src)
    binding, _binding_ambiguous = scan._walk(modules, ENTRIES, binding=True)
    evaluated, _evaluated_ambiguous = scan._walk(modules, ENTRIES, binding=False)
    importers = set(scan.axios_importers(src))
    status: dict[str, dict[str, bool]] = {}
    for rel in modules:
        status[f"{CLIENT_SRC}/{rel}"] = {
            "axios_importer": rel in importers,
            "binding_reachable": rel in binding,
            "evaluated_reachable": rel in evaluated,
        }
    return status


def assert_no_ambiguous_paths(paths: list[str]) -> None:
    counts: dict[str, int] = {}
    for path in paths:
        counts[path] = counts.get(path, 0) + 1
    dupes = sorted(path for path, count in counts.items() if count > 1)
    if dupes:
        raise PreservationError("ambiguous paths: " + ", ".join(dupes))


def _validate_closure(repo: Path, selected: tuple[Cluster, ...]) -> None:
    seen: dict[str, str] = {}
    importer_owner: dict[str, str] = {}
    for cluster in selected:
        paths = [item.path for item in cluster.files]
        try:
            assert_no_ambiguous_paths(paths)
        except PreservationError as exc:
            raise PreservationError(f"{cluster.cluster_id}: {exc}") from exc
        for item in cluster.files:
            if item.path in seen:
                raise PreservationError(f"ambiguous path {item.path} in {seen[item.path]} and {cluster.cluster_id}")
            seen[item.path] = cluster.cluster_id
            if not (repo / item.path).is_file():
                raise PreservationError(f"missing path {item.path}")
            if item.role == "importer":
                if item.path in importer_owner:
                    raise PreservationError(f"importer {item.path} is in more than one cluster")
                importer_owner[item.path] = cluster.cluster_id
            text = (repo / item.path).read_text(encoding="utf-8")
            if item.role == "importer":
                for token in cluster.forbidden_in_importers:
                    if token in text:
                        raise PreservationError(
                            f"{cluster.cluster_id} importer {item.path} contains unrelated endpoint token {token}"
                        )
        exclusion_paths = [item.path for item in cluster.exclusions]
        try:
            assert_no_ambiguous_paths(exclusion_paths)
        except PreservationError as exc:
            raise PreservationError(f"{cluster.cluster_id}: {exc}") from exc
        for item in cluster.exclusions:
            if not (repo / item.path).is_file():
                raise PreservationError(f"missing exclusion path {item.path}")
            if not item.reason.strip():
                raise PreservationError(f"exclusion {item.path} has no reason")


def _check_bounds(
    selected: tuple[Cluster, ...],
    callers: dict[str, list[dict[str, str]]],
    modules: dict,
) -> None:
    archived = {item.path: cluster.cluster_id for cluster in selected for item in cluster.files}
    for cluster in selected:
        cluster_paths = {item.path for item in cluster.files}
        excluded_callers = {item.path: item.reason for item in cluster.exclusions if item.kind == "caller"}
        excluded_deps = {item.path: item.reason for item in cluster.exclusions if item.kind == "dependency"}
        external: set[str] = set()
        for path in cluster_paths:
            for caller in callers.get(path, []):
                caller_path = caller["path"]
                if caller_path in cluster_paths:
                    continue
                external.add(caller_path)
                if caller_path in archived and archived[caller_path] != cluster.cluster_id:
                    raise PreservationError(
                        f"{caller_path} calls {path} but is archived in {archived[caller_path]}"
                    )
                if caller_path not in excluded_callers and caller_path not in CHARACTERIZATION_MOCKS:
                    raise PreservationError(
                        f"unbounded caller {caller_path} of {path} in {cluster.cluster_id}"
                    )
        for path, reason in excluded_callers.items():
            if path not in external:
                raise PreservationError(f"stale caller exclusion {path} in {cluster.cluster_id}: {reason}")
        outside_deps: set[str] = set()
        for path in cluster_paths:
            rel = _src_rel(path)
            module = modules[rel]
            deps: set[str] = set()
            for edge in module.imports:
                if edge.resolved:
                    deps.add(f"{CLIENT_SRC}/{edge.resolved}")
            for _spec, resolved, _mapping, _type_only in module.reexports:
                if resolved:
                    deps.add(f"{CLIENT_SRC}/{resolved}")
            for dep in deps:
                if dep not in cluster_paths:
                    outside_deps.add(dep)
                    if dep not in excluded_deps:
                        raise PreservationError(f"unbounded dependency {dep} of {path} in {cluster.cluster_id}")
        for path in excluded_deps:
            if path not in outside_deps:
                raise PreservationError(f"stale dependency exclusion {path} in {cluster.cluster_id}")
def _endpoint_inventory(path: str, serves: tuple[str, ...]) -> list[str]:
    own = [
        f"{item['method']} {item['endpoint']}"
        for item in operations()
        if item["production_path"] == path and item["archived"] == "true"
    ]
    if own:
        return own
    served = set(serves)
    return [
        f"{item['method']} {item['endpoint']}"
        for item in operations()
        if item["production_path"] in served and item["archived"] == "true"
    ]


def build_plan(repo: Path, inventory_path: Path, cluster_id: str | None) -> dict:
    if not inventory_path.is_file():
        raise PreservationError(f"missing inventory {inventory_path}")
    overlay_path = inventory_path.with_name("POST_AUDIT_RETIREMENTS.json")
    if not overlay_path.is_file():
        raise PreservationError(f"missing overlay {overlay_path}")
    rows = _load_inventory(inventory_path)
    if len(rows) != 20:
        raise PreservationError(f"inventory row count is {len(rows)}, expected 20")
    overlay = _load_overlay(overlay_path)
    src = (repo / CLIENT_SRC).resolve()
    scanned = scan.axios_importers(src)
    importers = production_importers(rows, overlay, scanned)
    unresolved = effective_unresolved(rows, overlay)
    if unresolved:
        raise PreservationError("UNRESOLVED rows remain: " + ", ".join(unresolved))
    if len(importers) != 17:
        raise PreservationError(f"importer count is {len(importers)}, expected 17")
    reclassified = {item["path"]: item["disposition"] for item in overlay["reclassified_importers"]}
    for path in importers:
        if path in reclassified and reclassified[path] != CANONICAL:
            raise PreservationError(f"unexpected disposition for {path}")
    if cluster_id and cluster_id not in {item.cluster_id for item in clusters()}:
        raise PreservationError(f"unknown cluster {cluster_id}")
    # Bounds are checked on the full table so a partial copy cannot hide a hole.
    full = clusters()
    _validate_closure(repo, full)
    modules = scan.load_modules(src)
    callers = _caller_index(modules)
    _check_bounds(full, callers, modules)
    reach = _reachability(src)
    owned = {item.path for cluster in full for item in cluster.files if item.role == "importer"}
    if owned != set(importers):
        raise PreservationError(
            "cluster importers do not match the 17 production importers: "
            f"only_clusters={sorted(owned - set(importers))} only_production={sorted(set(importers) - owned)}"
        )
    for path in (
        _p(CANONICAL_API),
        _p(RISK_BUCKETS),
        _p(RISK_EXPORTS),
        _p(RISK_DETAILS),
    ):
        if path not in reclassified:
            raise PreservationError(f"canonical importer missing from overlay: {path}")
    package = json.loads((repo / "packages/client/package.json").read_text(encoding="utf-8"))
    declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    if declared.get("axios") != "^1.21.0":
        raise PreservationError(f"axios declaration is {declared.get('axios')!r}")
    files: list[dict] = []
    for cluster in full:
        for item in cluster.files:
            data = (repo / item.path).read_bytes()
            committed = _git_bytes(repo, SOURCE_COMMIT, item.path)
            if data != committed:
                raise PreservationError(f"working tree differs from {SOURCE_COMMIT} for {item.path}")
            blob = git_blob_sha1(data)
            recorded = subprocess.check_output(
                ["git", "rev-parse", f"{SOURCE_COMMIT}:{item.path}"],
                cwd=repo,
                text=True,
            ).strip()
            if recorded != blob:
                raise PreservationError(f"git blob mismatch for {item.path}")
            git_object = subprocess.check_output(
                ["git", "hash-object", "--", item.path],
                cwd=repo,
                text=True,
            ).strip()
            if git_object != blob:
                raise PreservationError(f"git hash-object mismatch for {item.path}")
            disposition = reclassified.get(item.path, cluster.disposition)
            if item.role != "importer":
                disposition = cluster.disposition
            known = []
            for caller in callers.get(item.path, []):
                caller_path = caller["path"]
                included = "archived" if caller_path in {entry.path for entry in cluster.files} else "excluded"
                reason = ""
                if included == "excluded":
                    reason = next(
                        (
                            exclusion.reason
                            for exclusion in cluster.exclusions
                            if exclusion.path == caller_path
                        ),
                        "characterization spec mocks Axios and is not the preserved production capability",
                    )
                known.append(
                    {
                        "included": included,
                        "kinds": caller["kinds"],
                        "path": caller_path,
                        "reason": reason,
                    }
                )
            files.append(
                {
                    "archive_path": f"source/{item.path}",
                    "capability_cluster": cluster.cluster_id,
                    "disposition": disposition,
                    "endpoint_inventory": _endpoint_inventory(item.path, item.serves),
                    "git_blob": blob,
                    "known_callers": known,
                    "original_path": item.path,
                    "reachability": reach[item.path],
                    "role": item.role,
                    "serves": list(item.serves),
                    "sha256": sha256_bytes(data),
                    "source_commit": SOURCE_COMMIT,
                }
            )
    files.sort(key=lambda item: item["original_path"])
    exclusions = [
        {
            "capability_cluster": cluster.cluster_id,
            "kind": item.kind,
            "path": item.path,
            "reason": item.reason,
        }
        for cluster in full
        for item in sorted(cluster.exclusions, key=lambda exclusion: (exclusion.kind, exclusion.path))
    ]
    return {
        "archive_id": "client-axios-dormant-capabilities",
        "axios_declared": "^1.21.0",
        "axios_removal_authorized": False,
        "clusters": [cluster.cluster_id for cluster in full],
        "dormant_preserve_means_safe_to_delete": False,
        "effective_unresolved": unresolved,
        "exclusions": exclusions,
        "files": files,
        "importer_count": len(importers),
        "importers": importers,
        "inventory_sha256": sha256_bytes(inventory_path.read_bytes()),
        "order_id": ORDER_ID,
        "production_files_retired": False,
        "selected_cluster": cluster_id or "",
        "source_commit": SOURCE_COMMIT,
    }


def render_manifest(plan: dict) -> str:
    body = {key: plan[key] for key in plan if key not in {"importers", "selected_cluster"}}
    return json.dumps(body, indent=2, sort_keys=True) + "\n"


def render_endpoint_matrix() -> str:
    fields = [
        "cluster",
        "contract",
        "production_path",
        "method",
        "endpoint",
        "transport",
        "archived",
        "deletion_authority",
        "canonical_production_path",
        "notes",
    ]
    rows = sorted(
        operations(),
        key=lambda item: (
            item["cluster"],
            item["contract"],
            item["method"],
            item["endpoint"],
            item["production_path"],
            item["transport"],
        ),
    )
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for item in rows:
        writer.writerow(item)
    return buffer.getvalue()


def render_ledger(plan: dict) -> str:
    by_cluster = {cluster.cluster_id: cluster for cluster in clusters()}
    files_by_cluster: dict[str, list[str]] = {}
    serves: dict[str, set[str]] = {}
    for item in plan["files"]:
        files_by_cluster.setdefault(item["capability_cluster"], []).append(item["original_path"])
        for importer in item["serves"]:
            serves.setdefault(importer, set()).add(item["original_path"])
    fields = [
        "path",
        "cluster",
        "disposition",
        "archive_closure",
        "preservation_status",
        "next_adjudication",
    ]
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for path in plan["importers"]:
        cluster_id = next(item["capability_cluster"] for item in plan["files"] if item["original_path"] == path)
        disposition = next(item["disposition"] for item in plan["files"] if item["original_path"] == path)
        closure = sorted(serves[path])
        writer.writerow(
            {
                "archive_closure": ";".join(closure),
                "cluster": cluster_id,
                "disposition": disposition,
                "next_adjudication": by_cluster[cluster_id].next_adjudication,
                "path": path,
                "preservation_status": preservation_status_for_route(None),
            }
        )
    return buffer.getvalue()


def render_capability_index(plan: dict) -> str:
    by_cluster = {cluster.cluster_id: cluster for cluster in clusters()}
    lines = [
        "# Axios dormant capability index",
        "",
        f"Order: {ORDER_ID}.",
        f"Source commit: `{SOURCE_COMMIT}`.",
        f"Production Axios importers: {plan['importer_count']}. Effective UNRESOLVED rows: 0.",
        "Axios remains declared at `^1.21.0`. Removal is not authorized.",
        "DORMANT_PRESERVE does not mean safe to delete. A cluster that has a copy may stay in production.",
        "The four CANONICAL_BUT_UNROUTED importers stay in production. This copy does not retire them.",
        "",
    ]
    grouped: dict[str, list[dict]] = {}
    for item in plan["files"]:
        grouped.setdefault(item["capability_cluster"], []).append(item)
    for cluster_id in plan["clusters"]:
        cluster = by_cluster[cluster_id]
        lines.append(f"## {cluster_id}")
        lines.append("")
        lines.append(cluster.summary)
        lines.append("")
        lines.append(f"Disposition: {cluster.disposition}.")
        lines.append(f"Next adjudication: {cluster.next_adjudication}")
        lines.append("")
        lines.append("Archived files:")
        lines.append("")
        for item in grouped[cluster_id]:
            reach = item["reachability"]
            lines.append(
                f"- `{item['original_path']}` ({item['role']}). "
                f"binding_reachable={str(reach['binding_reachable']).lower()}, "
                f"evaluated_reachable={str(reach['evaluated_reachable']).lower()}."
            )
        lines.append("")
        if cluster.exclusions:
            lines.append("Left in production, with a reason:")
            lines.append("")
            for item in cluster.exclusions:
                lines.append(f"- `{item.path}` ({item.kind}). {item.reason}")
            lines.append("")
    lines.append("## Distinct contracts")
    lines.append("")
    lines.append("`/api/compare/lab` is owned by `packages/client/src/composables/useCompareState.ts` and `packages/client/src/components/compare/CompareBaselinePicker.vue`. It is not the Rosette baseline/diff client and not Rosette history.")
    lines.append("")
    lines.append("`/api/compare/baselines` and `/api/compare/diff` belong to `useRosetteCompareApi.ts`.")
    lines.append("")
    lines.append("`/api/compare/history` belongs to `components/art/rosette_compare_history/composables/useRosetteCompareActions.ts`.")
    lines.append("")
    lines.append("The art-rosette job compare history uses `/api/art/rosette/jobs`, `/api/art/rosette/compare`, `/api/art/rosette/compare/snapshot`, `/api/art/rosette/compare/snapshots`, and `/api/art/rosette/compare/export_csv`.")
    lines.append("")
    return "\n".join(lines)


def _selected_files(plan: dict, cluster_id: str | None) -> list[dict]:
    if not cluster_id:
        return list(plan["files"])
    return [item for item in plan["files"] if item["capability_cluster"] == cluster_id]


def copy_closure(repo: Path, archive_root: Path, files: list[dict]) -> None:
    assert_archive_destination(repo, archive_root)
    for item in files:
        src = repo / item["original_path"]
        dest = archive_root / "source" / item["original_path"]
        if _inside(dest, repo / CLIENT_SRC):
            raise PreservationError(f"refusing to write {dest} inside production client source")
        copy_bytes(src, dest)
        if dest.read_bytes() != src.read_bytes():
            raise PreservationError(f"copy diverged for {item['original_path']}")


def verify_archive(repo: Path, archive_root: Path, plan: dict) -> None:
    manifest_path = archive_root / "MANIFEST.json"
    if not manifest_path.is_file():
        raise PreservationError(f"missing {manifest_path}")
    rendered = render_manifest(plan)
    if manifest_path.read_text(encoding="utf-8") != rendered:
        again = render_manifest(plan)
        if rendered != again:
            raise PreservationError("manifest rendering is not byte-stable")
        raise PreservationError("MANIFEST.json does not match the current plan")
    source_root = archive_root / "source"
    declared = {item["archive_path"]: item for item in plan["files"]}
    on_disk = sorted(
        path.relative_to(archive_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    )
    expected = sorted(item["archive_path"] for item in plan["files"])
    if on_disk != expected:
        missing = sorted(set(expected) - set(on_disk))
        extra = sorted(set(on_disk) - set(expected))
        raise PreservationError(f"archive file set mismatch missing={missing} extra={extra}")
    for rel in on_disk:
        item = declared[rel]
        archived = (archive_root / rel).read_bytes()
        original = (repo / item["original_path"]).read_bytes()
        if archived != original:
            raise PreservationError(f"archived bytes differ from production for {item['original_path']}")
        if sha256_bytes(archived) != item["sha256"]:
            raise PreservationError(f"manifest sha256 mismatch for {item['original_path']}")
        if git_blob_sha1(archived) != item["git_blob"]:
            raise PreservationError(f"manifest git blob mismatch for {item['original_path']}")
        if item["source_commit"] != SOURCE_COMMIT:
            raise PreservationError(f"unexpected source commit on {item['original_path']}")
    client_text = "\n".join(
        path.read_text(encoding="utf-8", errors="surrogateescape")
        for path in (repo / CLIENT_SRC).rglob("*")
        if path.is_file() and path.suffix in {".ts", ".vue", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}
    )
    if "archive/experimental" in client_text:
        raise PreservationError("production client source mentions archive/experimental")


def _print_plan(plan: dict, cluster_id: str | None) -> None:
    files = _selected_files(plan, cluster_id)
    print(f"order={ORDER_ID}")
    print(f"source_commit={SOURCE_COMMIT}")
    print(f"importers={plan['importer_count']}")
    print(f"unresolved={len(plan['effective_unresolved'])}")
    print(f"files={len(files)}")
    for item in files:
        print(f"COPY {item['original_path']} cluster={item['capability_cluster']} role={item['role']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preserve dormant client Axios capabilities.")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--cluster", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()
    inventory = args.inventory if args.inventory.is_absolute() else repo / args.inventory
    cluster_id = args.cluster or None
    try:
        if args.archive_root is not None:
            archive_root = args.archive_root if args.archive_root.is_absolute() else repo / args.archive_root
            assert_archive_destination(repo, archive_root)
        else:
            archive_root = None
        if args.write_manifest and cluster_id:
            raise PreservationError("refusing to write a partial manifest for one cluster")
        if (args.write_manifest or args.verify or (archive_root and not args.dry_run)) and archive_root is None:
            raise PreservationError("refusing to copy or write without --archive-root")
        plan = build_plan(repo, inventory, cluster_id)
        _print_plan(plan, cluster_id)
        if args.dry_run:
            print("dry-run: no files written")
            return 0
        if archive_root is None:
            return 0
        if not args.verify:
            copy_closure(repo, archive_root, _selected_files(plan, cluster_id))
        if args.write_manifest:
            full = build_plan(repo, inventory, None)
            text = render_manifest(full)
            if text != render_manifest(full):
                raise PreservationError("manifest rendering is not byte-stable")
            manifest_path = archive_root / "MANIFEST.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(text, encoding="utf-8", newline="\n")
        if args.verify:
            verify_archive(repo, archive_root, build_plan(repo, inventory, None))
            print("verify: ok")
    except PreservationError as exc:
        print(f"preservation: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
