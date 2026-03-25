"""Code-quality analyzer — file-parallel orchestrator.

Architecture change from original
----------------------------------
Original model:  parallelize across checkers (each checker processes all files)
New model:       parallelize across FILES   (each file gets all checkers applied)

Why this is faster
------------------
- Checkers are typically fast per-file (regex, line scan).
- The file content cache has a 100% hit rate in the new model because each
  file is read once and handed to all checkers in the same worker.
- In the old model, the cache was shared across threads with a race condition
  on cold misses.  The new model eliminates the race entirely: each worker
  owns its file slice and reads content exactly once.

Thread safety
-------------
- No shared mutable state between workers.
- Each worker returns a list of issue dicts; the main thread collects them.
- The file cache is populated in the main thread BEFORE the pool starts,
  so workers only read (never write) the cache.

Enhancements implemented
------------------------
  P0  Thread-safe file cache (double-checked lock → pre-warm strategy)
  P0  None-safe config coercion (checks/exclude_checks never None)
  P0  Fixed git-diff fallback (staged files fallback, explicit error message)
  P1  --severity filter (CLI + programmatic)
  P1  Vue <script setup> aware unused-variable suppression (see vue_checker.py)
  P2  CSSDeadSelectorDetector type guard (see css_checker.py)
  P2  Duplicate detection noise reduction (see duplicate_checker.py)
  P3  Python checker foundation (see python_checks.py)
  P3  Config schema validation (see config.py)
  Arch File-parallel ThreadPoolExecutor (this file)
"""
from __future__ import annotations

import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base import BaseCheck, get_registered_checkers
from .config import load_config, load_baseline, is_suppressed

# Trigger __init_subclass__ registration for all checker modules
from . import checkers as _checkers  # noqa: F401


class CodeQualityAnalyzer:
    """Central orchestrator — discovers files, runs checkers, collects issues.

    Parallelism model
    -----------------
    Files are partitioned into ``workers`` chunks.  Each worker thread
    processes its chunk sequentially (all checkers × all files in chunk).
    This gives:
      • Zero cache contention  — content is pre-warmed, workers only read.
      • Better CPU utilisation — no idle threads waiting for a slow checker.
      • Simpler error isolation — one file crash doesn't kill other checkers.
    """

    def __init__(
        self,
        project_path: str | Path,
        *,
        config_overrides: Optional[Dict[str, Any]] = None,
        baseline_path: Optional[Path] = None,
        changed_only: bool = False,
        fix: bool = False,
        workers: int = 0,         # 0 = read from config
        severity_filter: Optional[List[str]] = None,
        verbose: bool = False,
        summary_only: bool = False,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.config = load_config(self.project_path, config_overrides or {})
        self.baseline_issues = load_baseline(baseline_path) if baseline_path else []
        self.changed_only = changed_only
        self.fix = fix
        self.verbose = verbose
        self.summary_only = summary_only

        # Severity filter — CLI wins, then config, then "everything"
        cfg_filter: List[str] = self.config.get("severity_filter") or []
        self.severity_filter: Set[str] = set(
            severity_filter if severity_filter is not None else cfg_filter
        )

        # Workers: CLI > config > CPU count
        if workers > 0:
            self.workers = workers
        else:
            cfg_workers = self.config.get("workers") or 0
            self.workers = max(1, int(cfg_workers) if cfg_workers else 4)

        # Results
        self.issues: List[Dict[str, Any]] = []

        # File content cache — pre-warmed in main thread; workers read-only
        self._file_cache: Dict[Path, str] = {}
        self._cache_lock = threading.Lock()   # guards cold-miss population

    # ── File caching ──────────────────────────────────────────────────────

    def get_file_content(self, file_path: Path) -> str:
        """Return full file content.  Thread-safe double-checked locking."""
        fp = file_path.resolve()
        # Fast path — already cached (read-only, no lock needed)
        cached = self._file_cache.get(fp)
        if cached is not None:
            return cached
        # Slow path — populate under lock
        with self._cache_lock:
            if fp not in self._file_cache:   # second check inside lock
                try:
                    self._file_cache[fp] = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    self._file_cache[fp] = ""
        return self._file_cache[fp]

    def _prewarm_cache(self, files: List[Path]) -> None:
        """Read all files in the main thread before handing work to the pool.

        Workers only ever READ from the cache, eliminating all write races.
        """
        for fp in files:
            self.get_file_content(fp)

    def get_file_lines(self, file_path: Path) -> List[str]:
        return self.get_file_content(file_path).splitlines(keepends=True)

    # ── Issue filtering ───────────────────────────────────────────────────

    def _filter_issue(self, issue: Dict[str, Any]) -> bool:
        """Return True if issue should be kept (not filtered, not suppressed)."""
        # Severity filter
        if self.severity_filter and issue.get("severity") not in self.severity_filter:
            return False
        # Baseline suppression
        if self.baseline_issues and is_suppressed(issue, self.baseline_issues):
            return False
        return True

    # ── File discovery ────────────────────────────────────────────────────

    def _get_files(self) -> List[Path]:
        """Gather files respecting config patterns & exclusions.

        Uses os.walk with early directory pruning instead of glob so that
        excluded dirs (node_modules, .git, …) are never even traversed.
        """
        import os

        exclude_dirs: Set[str] = set(self.config.get("exclude_dirs") or [])
        file_patterns: List[str] = self.config.get("file_patterns") or ["**/*"]

        # Collect allowed extensions from patterns like **/*.vue → .vue
        import fnmatch
        allowed_exts: Optional[Set[str]] = None
        if all(p.startswith("**/*.") for p in file_patterns):
            allowed_exts = {
                "." + p.split("*.")[-1] for p in file_patterns
            }

        results: List[Path] = []
        seen: Set[Path] = set()

        for root, dirs, files in os.walk(self.project_path):
            root_path = Path(root)
            # Prune excluded dirs in-place (prevents descent)
            dirs[:] = [
                d for d in dirs
                if d not in exclude_dirs and not d.startswith(".")
            ]

            for fname in files:
                fp = root_path / fname
                if allowed_exts and fp.suffix.lower() not in allowed_exts:
                    continue
                resolved = fp.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    results.append(fp)

        return results

    def _get_changed_files(self) -> List[Path]:
        """Return only files changed or staged according to git."""
        commands = [
            ["git", "diff", "--name-only", "HEAD"],       # unstaged vs HEAD
            ["git", "diff", "--name-only", "--cached"],   # staged
            ["git", "diff", "--name-only"],               # unstaged (no HEAD yet)
        ]

        names: Set[str] = set()
        ran_any = False

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_path,
                )
            except FileNotFoundError:
                if self.verbose:
                    print(
                        "[git] git not found — falling back to all files",
                        file=sys.stderr,
                    )
                return self._get_files()

            if result.returncode == 0:
                ran_any = True
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line:
                        names.add(line)

        if not ran_any:
            if self.verbose:
                print(
                    "[git] Not a git repository or no commits — "
                    "falling back to all files",
                    file=sys.stderr,
                )
            return self._get_files()

        if not names:
            if self.verbose:
                print("[git] No changed files detected.", file=sys.stderr)
            return []

        all_files = self._get_files()
        return [
            f for f in all_files
            if str(f.relative_to(self.project_path)) in names
        ]

    # ── Checker management ────────────────────────────────────────────────

    def _active_checkers(self) -> List[BaseCheck]:
        """Instantiate checkers allowed by config.  None-safe."""
        allowed: List[str] = self.config.get("checks") or []
        excluded: List[str] = self.config.get("exclude_checks") or []

        instances: List[BaseCheck] = []
        for cls in get_registered_checkers():
            if allowed and cls.name not in allowed:
                continue
            if cls.name in excluded:
                continue
            instances.append(cls(self))
        return instances

    # ── Worker function ───────────────────────────────────────────────────

    @staticmethod
    def _process_file_chunk(
        files: List[Path],
        checkers: List[BaseCheck],
        file_cache: Dict[Path, str],
    ) -> List[Dict[str, Any]]:
        """Process a slice of files through all checkers.

        Runs in a worker thread.  Reads file content from the pre-warmed
        cache (read-only — no races).  Returns raw issues for the caller
        to filter.
        """
        chunk_issues: List[Dict[str, Any]] = []

        for fp in files:
            content = file_cache.get(fp.resolve(), "")

            for checker in checkers:
                if not checker.accepts(fp):
                    continue
                try:
                    file_issues = checker.check_file(fp, content)
                    if file_issues:
                        chunk_issues.extend(file_issues)
                except Exception as exc:
                    chunk_issues.append({
                        "check": checker.name,
                        "file": str(fp),
                        "line": 0,
                        "message": f"Checker crashed: {exc}",
                        "severity": "critical",
                        "suggestion": "Report this as a bug in the checker.",
                    })

        return chunk_issues

    # ── Main entry ────────────────────────────────────────────────────────

    def analyze(self) -> List[Dict[str, Any]]:
        """Run all active checkers and return filtered, sorted issues."""
        files = self._get_changed_files() if self.changed_only else self._get_files()

        if not files:
            if self.verbose:
                print("No files to analyze.", file=sys.stderr)
            return []

        if self.verbose:
            print(f"Analyzing {len(files)} file(s)…", file=sys.stderr)

        checkers = self._active_checkers()
        if not checkers:
            if self.verbose:
                print("No checkers active.", file=sys.stderr)
            return []

        if self.verbose:
            print(f"Running {len(checkers)} checker(s) across {self.workers} worker(s)…",
                  file=sys.stderr)

        # Pre-warm cache in main thread — workers will only READ
        self._prewarm_cache(files)

        raw_issues: List[Dict[str, Any]] = []

        if self.workers > 1 and len(files) > 1:
            # Partition files into chunks — one chunk per worker
            chunks = _partition(files, self.workers)
            cache_snapshot = dict(self._file_cache)  # immutable view for workers

            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                futures = [
                    pool.submit(self._process_file_chunk, chunk, checkers, cache_snapshot)
                    for chunk in chunks
                    if chunk  # skip empty chunks when files < workers
                ]
                for future in as_completed(futures):
                    exc = future.exception()
                    if exc:
                        print(f"[worker] chunk failed: {exc}", file=sys.stderr)
                    else:
                        raw_issues.extend(future.result())
        else:
            # Single-threaded fallback
            raw_issues = self._process_file_chunk(
                files, checkers, self._file_cache
            )

        # Filter (severity + baseline suppression)
        self.issues = [i for i in raw_issues if self._filter_issue(i)]

        # Auto-fix pass (runs in main thread — safe to write files)
        if self.fix:
            self._apply_fixes(checkers)

        # Sort by file then line
        self.issues.sort(key=lambda i: (i["file"], i["line"]))
        return self.issues

    # ── Auto-fix ──────────────────────────────────────────────────────────

    def _apply_fixes(self, checkers: List[BaseCheck]) -> None:
        """Apply auto-fixes for fixable issues (main thread only)."""
        fixable_map = {c.name: c for c in checkers if c.fixable}
        applied = 0

        for issue in list(self.issues):   # iterate a copy — we may prune
            checker = fixable_map.get(issue["check"])
            if not checker:
                continue
            fp = Path(issue["file"])
            new_content = checker.fix(fp, issue)
            if new_content is not None:
                try:
                    fp.write_text(new_content, encoding="utf-8")
                    applied += 1
                    # Invalidate cache entry so subsequent reads are fresh
                    self._file_cache.pop(fp.resolve(), None)
                except OSError as exc:
                    print(f"[fix] Could not write {fp}: {exc}", file=sys.stderr)

        if self.verbose and applied:
            print(f"Applied {applied} auto-fix(es).", file=sys.stderr)

    # ── Reporting helpers ─────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        """Return aggregated counts by severity and file directory."""
        from collections import defaultdict
        counts: Dict[str, int] = defaultdict(int)
        by_dir: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for issue in self.issues:
            sev = issue.get("severity", "unknown")
            counts[sev] += 1
            directory = str(Path(issue["file"]).parent)
            by_dir[directory][sev] += 1

        return {
            "total": len(self.issues),
            "by_severity": dict(counts),
            "by_directory": {k: dict(v) for k, v in by_dir.items()},
        }


# ── Utilities ─────────────────────────────────────────────────────────────────

def _partition(items: List[Any], n: int) -> List[List[Any]]:
    """Split ``items`` into up to ``n`` roughly equal chunks."""
    if not items:
        return []
    size = max(1, (len(items) + n - 1) // n)
    return [items[i: i + size] for i in range(0, len(items), size)]
