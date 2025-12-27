"""
H7.2.2: Prometheus-style metrics for RMOS CAM endpoints.

Provides:
- Counter: increment-only metric
- HistogramMs: latency histogram in milliseconds
- Request-ID sampling for structured logs
"""
from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


_LOCK = threading.Lock()


@dataclass(frozen=True)
class MetricKey:
    name: str
    labels: Tuple[Tuple[str, str], ...]


def _norm_labels(labels: Optional[Dict[str, str]]) -> Tuple[Tuple[str, str], ...]:
    if not labels:
        return tuple()
    # stable ordering
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


class Counter:
    """
    Minimal in-process counter (Prometheus-style).
    """

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help = help_text
        self._values: Dict[MetricKey, float] = {}

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        key = MetricKey(self.name, _norm_labels(labels))
        with _LOCK:
            self._values[key] = self._values.get(key, 0.0) + float(amount)

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} counter"]
        with _LOCK:
            items = list(self._values.items())
        for key, val in items:
            if key.labels:
                lbl = ",".join([f'{k}="{v}"' for k, v in key.labels])
                lines.append(f"{self.name}{{{lbl}}} {val}")
            else:
                lines.append(f"{self.name} {val}")
        return "\n".join(lines) + "\n"


class HistogramMs:
    """
    Tiny histogram in milliseconds.
    Buckets are fixed to keep this simple and stable.
    """

    DEFAULT_BUCKETS_MS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)

    def __init__(self, name: str, help_text: str, buckets_ms: Tuple[int, ...] = DEFAULT_BUCKETS_MS):
        self.name = name
        self.help = help_text
        self.buckets_ms = buckets_ms
        self._bucket_counts: Dict[MetricKey, Dict[int, float]] = {}
        self._sum: Dict[MetricKey, float] = {}
        self._count: Dict[MetricKey, float] = {}

    def observe(self, ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        ms = float(ms)
        key = MetricKey(self.name, _norm_labels(labels))
        with _LOCK:
            if key not in self._bucket_counts:
                self._bucket_counts[key] = {b: 0.0 for b in self.buckets_ms}
                self._sum[key] = 0.0
                self._count[key] = 0.0

            for b in self.buckets_ms:
                if ms <= b:
                    self._bucket_counts[key][b] += 1.0
            self._sum[key] += ms
            self._count[key] += 1.0

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} histogram"]
        with _LOCK:
            keys = list(self._bucket_counts.keys())
            bucket_counts = {k: dict(self._bucket_counts[k]) for k in keys}
            sums = dict(self._sum)
            counts = dict(self._count)

        for key in keys:
            base_labels = dict(key.labels)
            cumulative = 0.0
            for b in self.buckets_ms:
                cumulative += bucket_counts[key].get(b, 0.0)
                lbl = dict(base_labels)
                lbl["le"] = str(b)
                lines.append(f'{self.name}_bucket{{{_render_labels(lbl)}}} {cumulative}')
            # +Inf bucket
            lbl = dict(base_labels)
            lbl["le"] = "+Inf"
            lines.append(f'{self.name}_bucket{{{_render_labels(lbl)}}} {counts.get(key, 0.0)}')
            lines.append(f'{self.name}_sum{{{_render_labels(base_labels)}}} {sums.get(key, 0.0)}')
            lines.append(f'{self.name}_count{{{_render_labels(base_labels)}}} {counts.get(key, 0.0)}')
        return "\n".join(lines) + "\n"


def _render_labels(labels: Dict[str, str]) -> str:
    return ",".join([f'{k}="{v}"' for k, v in sorted(labels.items())])


def should_sample_request_id() -> bool:
    """
    Probabilistic sampling for request-id logs (default 1%).
    """
    raw = os.getenv("RMOS_METRICS_REQUEST_ID_SAMPLE_RATE", "0.01").strip()
    try:
        rate = float(raw)
    except Exception:
        rate = 0.01
    if rate <= 0:
        return False
    if rate >= 1:
        return True
    return random.random() < rate


def now_ms() -> float:
    return time.monotonic() * 1000.0


# ---------------------------------------------------------------------
# H7.2.2: roughing_gcode_intent metrics
# ---------------------------------------------------------------------

cam_roughing_intent_requests_total = Counter(
    "cam_roughing_intent_requests_total",
    "Total requests to /cam/roughing_gcode_intent",
)

cam_roughing_intent_issues_total = Counter(
    "cam_roughing_intent_issues_total",
    "Total /cam/roughing_gcode_intent requests that produced >=1 normalization issue",
)

cam_roughing_intent_strict_rejects_total = Counter(
    "cam_roughing_intent_strict_rejects_total",
    "Total /cam/roughing_gcode_intent requests rejected in strict mode due to normalization issues",
)

cam_roughing_intent_latency_ms = HistogramMs(
    "cam_roughing_intent_latency_ms",
    "Latency (ms) for /cam/roughing_gcode_intent",
)


def render_prometheus() -> str:
    """
    Render all registered metrics in Prometheus exposition format.
    """
    parts = [
        cam_roughing_intent_requests_total.render(),
        cam_roughing_intent_issues_total.render(),
        cam_roughing_intent_strict_rejects_total.render(),
        cam_roughing_intent_latency_ms.render(),
    ]
    return "".join(parts)
