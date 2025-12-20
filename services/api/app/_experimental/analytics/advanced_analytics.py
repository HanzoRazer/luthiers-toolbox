"""
Advanced Analytics (N9.1) — correlations, anomaly detection, prediction skeleton

Provides small, dependency-free implementations for:
- Pearson correlation between two numeric metrics
- Z-score anomaly detection for job durations / success rates
- Simple heuristic failure risk predictor (placeholder for ML)

This module uses existing RMOS stores via `get_rmos_stores()`.
"""
from typing import Dict, Any, List, Tuple
import math
from collections import defaultdict
import statistics

from ...stores.rmos_stores import get_rmos_stores


class AdvancedAnalytics:
    def __init__(self):
        self.stores = get_rmos_stores()

    def _extract_metric_pairs(self, x_key: str, y_key: str) -> List[Tuple[float, float]]:
        """Extract paired numeric metrics from joblogs and patterns/materials when necessary.

        Supported keys (examples):
        - job.duration_seconds
        - job.success (1 or 0)
        - pattern.complexity_score
        - material.efficiency_score

        We support dotted keys; first token selects source: 'job', 'pattern', 'material'.
        """
        pairs: List[Tuple[float, float]] = []

        joblogs = self.stores.joblogs.get_all()
        patterns = {p["id"]: p for p in self.stores.patterns.get_all()}
        families = {f["id"]: f for f in self.stores.strip_families.get_all()}

        def get_value_from_key(obj: Dict[str, Any], key: str):
            # simple dotted key resolver
            parts = key.split('.')
            v = obj
            for p in parts:
                if not isinstance(v, dict):
                    return None
                v = v.get(p)
                if v is None:
                    return None
            return v

        for job in joblogs:
            # resolve x
            x_val = None
            y_val = None

            if x_key.startswith('job.'):
                x_val = get_value_from_key(job, x_key.split('.', 1)[1])
            elif x_key.startswith('pattern.'):
                pid = job.get('pattern_id')
                if pid and pid in patterns:
                    x_val = get_value_from_key(patterns[pid], x_key.split('.', 1)[1])
            elif x_key.startswith('material.') or x_key.startswith('family.'):
                fid = job.get('strip_family_id')
                if fid and fid in families:
                    x_val = get_value_from_key(families[fid], x_key.split('.', 1)[1])

            if y_key.startswith('job.'):
                y_val = get_value_from_key(job, y_key.split('.', 1)[1])
            elif y_key.startswith('pattern.'):
                pid = job.get('pattern_id')
                if pid and pid in patterns:
                    y_val = get_value_from_key(patterns[pid], y_key.split('.', 1)[1])
            elif y_key.startswith('material.') or y_key.startswith('family.'):
                fid = job.get('strip_family_id')
                if fid and fid in families:
                    y_val = get_value_from_key(families[fid], y_key.split('.', 1)[1])

            # try to coerce to float
            try:
                if x_val is not None:
                    x_val = float(x_val)
                if y_val is not None:
                    y_val = float(y_val)
            except Exception:
                continue

            if x_val is not None and y_val is not None:
                pairs.append((x_val, y_val))

        return pairs

    def pearson_correlation(self, x_key: str, y_key: str) -> Dict[str, Any]:
        """Compute Pearson correlation coefficient between two metrics.

        Returns dict with `r`, `n`, `p_value_estimate` (very rough), and sample stats.
        """
        pairs = self._extract_metric_pairs(x_key, y_key)
        n = len(pairs)
        if n < 2:
            return {"r": 0.0, "n": n, "error": "not enough samples"}

        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mean_x = statistics.mean(xs)
        mean_y = statistics.mean(ys)
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(xs, ys))
        var_x = sum((xi - mean_x) ** 2 for xi in xs)
        var_y = sum((yi - mean_y) ** 2 for yi in ys)

        try:
            r = cov / math.sqrt(var_x * var_y)
        except Exception:
            r = 0.0

        # very rough p-value estimate using t-distribution approximation
        try:
            t_stat = r * math.sqrt((n - 2) / (1 - r * r)) if abs(r) < 1 else float('inf')
            # two-tailed approximate p using survival of t; we won't import scipy — provide NaN placeholder
            p_est = None
        except Exception:
            t_stat = None
            p_est = None

        return {
            "r": r,
            "n": n,
            "mean_x": mean_x,
            "mean_y": mean_y,
            "t_stat": t_stat,
            "p_value_estimate": p_est
        }

    def detect_duration_anomalies(self, z_thresh: float = 3.0) -> Dict[str, Any]:
        """Detect anomalies in job durations using z-score.

        Returns list of jobs flagged as anomalies with dashboard-expected format.
        Dashboard expects: [{job_id, job_type, duration_min, z_score}]
        """
        joblogs = self.stores.joblogs.get_all()
        durations = []
        job_data = []
        for j in joblogs:
            d = j.get('duration_seconds')
            if d is None:
                continue
            try:
                durations.append(float(d))
                job_data.append({
                    'job_id': j.get('id'),
                    'job_type': j.get('job_type', 'Unknown'),
                    'duration_seconds': float(d)
                })
            except Exception:
                continue

        if not durations:
            return {
                "anomalies": [],
                "mean_seconds": 0,
                "stdev_seconds": 0,
                "n": 0
            }

        mean = statistics.mean(durations)
        stdev = statistics.pstdev(durations) if len(durations) > 1 else 0.0
        anomalies = []
        for job in job_data:
            z = (job['duration_seconds'] - mean) / stdev if stdev > 0 else 0.0
            if abs(z) >= z_thresh:
                anomalies.append({
                    "job_id": job['job_id'],
                    "job_type": job['job_type'],
                    "duration_min": job['duration_seconds'] / 60.0,
                    "duration_seconds": job['duration_seconds'],
                    "z_score": z
                })
        
        return {
            "anomalies": anomalies,
            "mean_seconds": mean,
            "stdev_seconds": stdev,
            "n": len(durations)
        }

    def detect_success_rate_anomalies(self, window_days: int = 30, z_thresh: float = 3.0) -> Dict[str, Any]:
        """Detect days with anomalous success rates (daily aggregation).

        Returns days where the daily success_rate z-score exceeds threshold.
        Dashboard expects: [{window_start, window_end, success_rate, z_score}]
        """
        joblogs = self.stores.joblogs.get_all()
        daily = defaultdict(lambda: {"total": 0, "completed": 0})
        for j in joblogs:
            ca = j.get('created_at')
            if not ca:
                continue
            day = ca.split('T')[0]
            daily[day]['total'] += 1
            if j.get('status') == 'completed':
                daily[day]['completed'] += 1

        days = []
        for day, stats in daily.items():
            total = stats['total']
            if total == 0:
                continue
            rate = stats['completed'] / total
            days.append((day, rate))

        if not days:
            return {
                "anomalies": [],
                "mean": 0,
                "stdev": 0,
                "n": 0
            }

        rates = [r for _, r in days]
        mean = statistics.mean(rates)
        stdev = statistics.pstdev(rates) if len(rates) > 1 else 0.0
        anomalies = []
        for day, rate in days:
            z = (rate - mean) / stdev if stdev > 0 else 0.0
            if abs(z) >= z_thresh:
                anomalies.append({
                    "window_start": day,
                    "window_end": day,
                    "success_rate": rate * 100,  # Convert to percentage
                    "z_score": z
                })

        return {
            "anomalies": anomalies,
            "mean": mean * 100,  # Convert to percentage
            "stdev": stdev * 100,  # Convert to percentage
            "n": len(rates)
        }

    def predict_failure_risk(self, job_features: Dict[str, Any]) -> Dict[str, Any]:
        """Simple heuristic predictor for failure risk.

        This is a placeholder and should be replaced by a trained model.
        Dashboard expects: {risk_score: float(0-1), advice: string}
        Input from POST body: {jobType, material, toolDiameter}
        """
        job_type = job_features.get('jobType', '')
        material = job_features.get('material', '')
        tool_d = float(job_features.get('toolDiameter', 6.0))

        # Simple heuristic based on historical data
        joblogs = self.stores.joblogs.get_all()
        
        # Filter similar jobs
        similar = [j for j in joblogs if j.get('job_type') == job_type]
        
        if not similar:
            return {
                "risk_score": 0.33,
                "risk_percent": 33.0,
                "advice": f"No historical data for {job_type}. Medium risk assumed.",
                "explanation": "Insufficient historical data for accurate prediction. Default medium risk assigned."
            }
        
        # Calculate failure rate for similar jobs
        total = len(similar)
        failed = sum(1 for j in similar if j.get('status') in ['failed', 'error'])
        base_risk = failed / total if total > 0 else 0.33
        
        # Adjust for tool diameter (smaller tools = higher risk)
        tool_factor = 1.0
        if tool_d < 3.0:
            tool_factor = 1.3
        elif tool_d < 6.0:
            tool_factor = 1.1
        
        risk = min(1.0, base_risk * tool_factor)
        
        # Generate advice
        if risk < 0.33:
            advice = f"Low risk for {job_type} with {material}. {len(similar)} similar jobs in history."
            explanation = f"Based on {total} similar jobs, {failed} failed. Risk adjusted for tool size."
        elif risk < 0.66:
            advice = f"Medium risk. Consider test run. {failed}/{total} similar jobs failed."
            explanation = f"Failure rate is moderate. Review parameters before production run."
        else:
            advice = f"High risk! {failed}/{total} similar jobs failed. Review parameters carefully."
            explanation = f"High failure rate detected. Consider alternative parameters or smaller test batch."
        
        return {
            "risk_score": risk,
            "risk_percent": risk * 100,  # Test expects this field
            "advice": advice,
            "explanation": explanation
        }


def get_advanced_analytics() -> AdvancedAnalytics:
    return AdvancedAnalytics()
