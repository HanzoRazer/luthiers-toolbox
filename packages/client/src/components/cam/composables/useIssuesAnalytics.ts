/**
 * useIssuesAnalytics - Risk scoring, time estimates, and export for CAM issues
 */
import { computed, type Ref } from "vue";
import type { SimIssue } from "@/types/cam";
import { type SeverityOption } from "./useSeverityFilter";

export function useIssuesAnalytics(issues: Ref<SimIssue[]>) {
  /**
   * Severity metrics: counts of each severity in the full issues list.
   */
  const severityCounts = computed<Record<SeverityOption, number>>(() => {
    const counts: Record<SeverityOption, number> = {
      info: 0,
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    };
    for (const iss of issues.value) {
      const sev = (iss.severity || "medium") as SeverityOption;
      if (sev in counts) {
        counts[sev] += 1;
      }
    }
    return counts;
  });

  /**
   * Risk score: weighted severity sum
   */
  const riskScore = computed(() => {
    const c = severityCounts.value;
    return (
      c.critical * 5 +
      c.high * 3 +
      c.medium * 2 +
      c.low * 1 +
      c.info * 0.5
    );
  });

  /**
   * Total extra time from all issues
   */
  const totalExtraTimeSec = computed<number>(() => {
    let total = 0;
    for (const iss of issues.value as (SimIssue & { extra_time_s?: number })[]) {
      const extra = typeof iss.extra_time_s === "number" ? iss.extra_time_s : 0;
      total += extra;
    }
    return total;
  });

  function formatDuration(sec: number): string {
    if (!sec || sec <= 0) return "0 s";
    const whole = Math.round(sec);
    const minutes = Math.floor(whole / 60);
    const seconds = whole % 60;
    if (minutes === 0) return `${seconds} s`;
    return `${minutes} min ${seconds} s`;
  }

  /**
   * Export data as JSON
   */
  const analyticsJson = computed(() => {
    return JSON.stringify(
      {
        total_issues: issues.value.length,
        severity_counts: severityCounts.value,
        risk_score: riskScore.value,
        total_extra_time_s: totalExtraTimeSec.value,
        total_extra_time_human: formatDuration(totalExtraTimeSec.value),
      },
      null,
      2
    );
  });

  /**
   * Export data as CSV
   */
  const analyticsCsv = computed(() => {
    const header = [
      "index",
      "type",
      "severity",
      "x",
      "y",
      "z",
      "extra_time_s",
      "note",
    ];
    const rows: string[] = [];
    rows.push(header.join(","));

    (issues.value as (SimIssue & { extra_time_s?: number })[]).forEach(
      (iss, idx) => {
        const extra =
          typeof iss.extra_time_s === "number" ? iss.extra_time_s : "";
        const row = [
          idx.toString(),
          (iss.type || "").replace(/,/g, " "),
          (iss.severity || "").toString(),
          iss.x.toFixed(4),
          iss.y.toFixed(4),
          iss.z != null ? iss.z.toFixed(4) : "",
          extra.toString(),
          (iss.note || "").replace(/[\r\n,]/g, " "),
        ];
        rows.push(row.join(","));
      }
    );

    return rows.join("\n");
  });

  function downloadBlob(content: string, mime: string, filename: string) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function downloadJson() {
    if (!issues.value.length) return;
    downloadBlob(analyticsJson.value, "application/json", "cam_issues_analytics.json");
  }

  function downloadCsv() {
    if (!issues.value.length) return;
    downloadBlob(analyticsCsv.value, "text/csv", "cam_issues_analytics.csv");
  }

  return {
    severityCounts,
    riskScore,
    totalExtraTimeSec,
    formatDuration,
    analyticsJson,
    analyticsCsv,
    downloadJson,
    downloadCsv,
  };
}
