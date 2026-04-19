#!/usr/bin/env python3
"""
Frontend Mode Benchmark Runner
==============================

Benchmarks blueprint vectorizer: refined vs layered_dual_pass.

Usage:
    python scripts/run_frontend_mode_benchmark.py
    python scripts/run_frontend_mode_benchmark.py --api-base http://localhost:8000

Author: Production Shop
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_API_BASE = "http://localhost:8000"
DEFAULT_MANIFEST = "benchmark_manifest.json"
DEFAULT_OUTPUT_DIR = "benchmark_results"

BENCHMARK_CONFIGS = [
    {"id": "refined", "name": "Production (refined)", "mode": "refined", "export_preset": "geometry_only", "track": "primary"},
    {"id": "layered_geometry_only", "name": "Candidate (layered+geo)", "mode": "layered_dual_pass", "export_preset": "geometry_only", "track": "primary"},
    {"id": "layered_reference_full", "name": "Candidate (layered+ref)", "mode": "layered_dual_pass", "export_preset": "reference_full", "track": "secondary"},
]

@dataclass
class BenchmarkResult:
    file_name: str
    config_id: str
    config_name: str
    track: str
    success: bool
    ok: bool = False
    error: str = ""
    entity_count: int = 0
    selection_score: float = 0.0
    processing_ms: float = 0.0
    execution_path: Dict[str, Any] = field(default_factory=dict)
    width_mm: float = 0.0
    height_mm: float = 0.0
    has_dxf: bool = False

@dataclass
class BenchmarkComparison:
    file_name: str
    baseline_id: str
    candidate_id: str
    entity_delta: int = 0
    entity_delta_pct: float = 0.0
    score_delta: float = 0.0
    verdict: str = ""
    reasons: List[str] = field(default_factory=list)

def run_vectorize_async(api_base, file_path, mode, export_preset, timeout=300):
    url = f"{api_base}/api/blueprint/vectorize/async"
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        data = {"mode": mode, "export_preset": export_preset, "debug": "true", "target_height_mm": "500"}
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        job_id = response.json().get("job_id")
    
    status_url = f"{api_base}/api/blueprint/vectorize/status/{job_id}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        status = requests.get(status_url, timeout=10).json()
        if status.get("status") == "complete":
            return status.get("result", {})
        if status.get("status") == "failed":
            raise RuntimeError(status.get("error", "Failed"))
    raise TimeoutError("Timeout")

def run_benchmark(api_base, file_path, config):
    result = BenchmarkResult(file_name=file_path.name, config_id=config["id"], config_name=config["name"], track=config["track"], success=False)
    try:
        resp = run_vectorize_async(api_base, file_path, config["mode"], config["export_preset"])
        result.success = True
        result.ok = resp.get("ok", False)
        result.entity_count = resp.get("artifacts", {}).get("dxf", {}).get("entity_count", 0)
        result.selection_score = resp.get("selection", {}).get("selection_score", 0.0)
        result.processing_ms = resp.get("metrics", {}).get("processing_ms", 0.0)
        result.execution_path = resp.get("debug", {}).get("execution_path", {})
        result.has_dxf = resp.get("artifacts", {}).get("dxf", {}).get("present", False)
    except Exception as e:
        result.error = str(e)
    return result

def compare(baseline, candidate):
    c = BenchmarkComparison(file_name=baseline.file_name, baseline_id=baseline.config_id, candidate_id=candidate.config_id)
    if baseline.entity_count > 0:
        c.entity_delta = candidate.entity_count - baseline.entity_count
        c.entity_delta_pct = (c.entity_delta / baseline.entity_count) * 100
    c.score_delta = candidate.selection_score - baseline.selection_score
    
    if not candidate.success:
        c.verdict = "CANDIDATE_FAILED"
    elif not baseline.success:
        c.verdict = "BASELINE_FAILED"
    elif c.score_delta > 0.05 or (abs(c.score_delta) <= 0.05 and c.entity_delta_pct > 10):
        c.verdict = "CANDIDATE_BETTER"
    elif abs(c.score_delta) <= 0.05 and abs(c.entity_delta_pct) <= 10:
        c.verdict = "EQUIVALENT"
    else:
        c.verdict = "BASELINE_BETTER"
    return c

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-only", action="store_true")
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found")
        sys.exit(1)
    
    manifest = json.loads(manifest_path.read_text())
    base_path = manifest_path.parent
    configs = [c for c in BENCHMARK_CONFIGS if not args.primary_only or c["track"] == "primary"]
    
    print(f"API: {args.api_base}")
    print(f"Configs: {[c['id'] for c in configs]}")
    
    results = []
    for f in manifest.get("files", []):
        fp = base_path / f["path"]
        if not fp.exists():
            print(f"SKIP: {fp}")
            continue
        print(f"\nProcessing: {f['name']}")
        for cfg in configs:
            print(f"  {cfg['id']}...", end=" ", flush=True)
            r = run_benchmark(args.api_base, fp, cfg)
            results.append(r)
            print(f"entities={r.entity_count}" if r.success else f"FAILED")
    
    comparisons = []
    for fn in set(r.file_name for r in results):
        b = next((r for r in results if r.file_name == fn and r.config_id == "refined"), None)
        c = next((r for r in results if r.file_name == fn and r.config_id == "layered_geometry_only"), None)
        if b and c:
            comparisons.append(compare(b, c))
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    report = {"generated": datetime.now().isoformat(), "results": [asdict(r) for r in results], "comparisons": [asdict(c) for c in comparisons]}
    (out_dir / f"benchmark_{ts}.json").write_text(json.dumps(report, indent=2, default=str))
    
    # Summary
    print("\n" + "="*50 + "\nSUMMARY\n" + "="*50)
    for c in comparisons:
        print(f"  {c.file_name}: {c.verdict} (score {c.score_delta:+.2f}, entities {c.entity_delta_pct:+.0f}%)")

    wins = sum(1 for c in comparisons if c.verdict == "CANDIDATE_BETTER")
    losses = sum(1 for c in comparisons if c.verdict == "BASELINE_BETTER")
    print(f"\nCandidate wins: {wins}, Baseline wins: {losses}")
    print("RECOMMENDATION:", "Promote layered_dual_pass" if wins > losses else "Keep refined")

if __name__ == "__main__":
    main()
