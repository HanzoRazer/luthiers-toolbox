# services/api/app/governance/metrics_registry.py
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, Mapping, Tuple


def _norm_labels(labels: Mapping[str, str] | None) -> Tuple[Tuple[str, str], ...]:
    if not labels:
        return tuple()
    # stable ordering for deterministic keys & output
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


@dataclass
class Counter:
    name: str
    help: str
    # key: normalized labels tuple -> value
    values: Dict[Tuple[Tuple[str, str], ...], int] = field(default_factory=dict)

    def inc(self, labels: Mapping[str, str] | None = None, amount: int = 1) -> None:
        key = _norm_labels(labels)
        self.values[key] = int(self.values.get(key, 0)) + int(amount)

    def render(self) -> str:
        lines = []
        lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} counter")
        for lbls, val in sorted(self.values.items(), key=lambda x: x[0]):
            if not lbls:
                lines.append(f"{self.name} {val}")
            else:
                inner = ",".join([f'{k}="{v}"' for k, v in lbls])
                lines.append(f"{self.name}{{{inner}}} {val}")
        return "\n".join(lines)


class MetricsRegistry:
    """
    Tiny prometheus-style in-process registry.
    - Counters only (good enough for H7.2.2.1)
    - Thread-safe
    - Text exposition compatible with /metrics scrape
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, Counter] = {}

    def counter(self, name: str, help: str) -> Counter:
        with self._lock:
            c = self._counters.get(name)
            if c is None:
                c = Counter(name=name, help=help)
                self._counters[name] = c
            return c

    def inc(self, name: str, help: str, labels: Mapping[str, str] | None = None, amount: int = 1) -> None:
        self.counter(name, help).inc(labels=labels, amount=amount)

    def render_prometheus(self) -> str:
        with self._lock:
            counters = list(self._counters.values())
        # render outside lock
        chunks = [c.render() for c in counters if c.values]
        return "\n\n".join(chunks) + ("\n" if chunks else "")


# Global singleton (intentionally small + stable surface)
metrics = MetricsRegistry()
