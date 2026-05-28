#!/usr/bin/env python3
"""Compare endpoint counts per file between baseline commit and HEAD."""
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
APP = "services/api/app"
DECORATOR = re.compile(r"@router\.(get|post|put|patch|delete)\(")


def count_in_tree(rev: str) -> dict[str, int]:
    """Count @router decorators per file at git rev."""
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", rev, APP],
        cwd=REPO,
        text=True,
    )
    files = [f for f in out.strip().splitlines() if f.endswith(".py")]
    by_file: dict[str, int] = defaultdict(int)

    for rel in files:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"{rev}:{rel}"],
                cwd=REPO,
                stderr=subprocess.DEVNULL,
            )
            content = raw.decode("utf-8", errors="replace")
        except subprocess.CalledProcessError:
            continue
        app_rel = rel.replace("services/api/app/", "").replace("services/api/app\\", "")
        n = len(DECORATOR.findall(content))
        if n:
            by_file[app_rel] = n

    return dict(by_file)


def find_baseline_commit() -> str:
    """Find commit where debt_history last recorded 942 endpoints."""
    import json

    hist = json.loads((REPO / "services/api/metrics/debt_history.json").read_text())
    for entry in reversed(hist):
        if entry.get("endpoints") == 942:
            ts = entry["timestamp"][:10]
            # find closest commit to that date updating debt_history
            log = subprocess.check_output(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%H",
                    f"--before={ts}T23:59:59",
                    "--",
                    "services/api/metrics/debt_history.json",
                ],
                cwd=REPO,
                text=True,
            ).strip()
            if log:
                return log
    return "HEAD~200"


def main():
    baseline_rev = find_baseline_commit()
    old = count_in_tree(baseline_rev)
    new = count_in_tree("HEAD")

    old_total = sum(old.values())
    new_total = sum(new.values())

    print(f"baseline_rev={baseline_rev[:12]}")
    print(f"old_total={old_total} new_total={new_total} delta=+{new_total - old_total}")
    print()

    all_files = set(old) | set(new)
    deltas = []
    for f in all_files:
        d = new.get(f, 0) - old.get(f, 0)
        if d != 0:
            deltas.append((d, new.get(f, 0), old.get(f, 0), f))

    deltas.sort(key=lambda x: -x[0])

    print("--- NEW FILES (did not exist at baseline) ---")
    new_files = [(d, n, o, f) for d, n, o, f in deltas if o == 0 and n > 0]
    print(f"count={len(new_files)} endpoints={sum(x[0] for x in new_files)}")
    for d, n, o, f in new_files[:50]:
        print(f"  +{d:3d} ({n:3d} now)  {f}")
    if len(new_files) > 50:
        print(f"  ... +{len(new_files) - 50} more files")

    print("\n--- GROWTH IN EXISTING FILES ---")
    growth = [(d, n, o, f) for d, n, o, f in deltas if o > 0 and d > 0]
    print(f"files={len(growth)} endpoints=+{sum(x[0] for x in growth)}")
    for d, n, o, f in growth[:30]:
        print(f"  +{d:3d} ({o}->{n})  {f}")

    print("\n--- SHRINK / REMOVED ---")
    shrink = [(d, n, o, f) for d, n, o, f in deltas if d < 0]
    print(f"files={len(shrink)} endpoints={sum(x[0] for x in shrink)}")
    for d, n, o, f in shrink[:20]:
        print(f"  {d:4d} ({o}->{n})  {f}")

    # Category heuristics on NEW files only
    cats = defaultdict(lambda: {"files": 0, "endpoints": 0})
    for d, n, o, f in new_files:
        fl = f.lower()
        if "saw_lab" in fl or "batch_" in fl:
            key = "saw_lab"
        elif "/cam/" in fl or fl.startswith("cam\\") or "cam_" in fl:
            key = "cam_governance_ci"
        elif "art_studio" in fl:
            key = "art_studio"
        elif "rmos" in fl:
            key = "rmos"
        elif "debug" in fl or "probe" in fl or "test" in fl:
            key = "debug_probe"
        elif "compare" in fl:
            key = "compare_lab"
        elif "workflow" in fl:
            key = "workflow"
        else:
            key = "other"
        cats[key]["files"] += 1
        cats[key]["endpoints"] += d

    print("\n--- NEW FILE CATEGORIES ---")
    for k, v in sorted(cats.items(), key=lambda x: -x[1]["endpoints"]):
        print(f"  {k:20s}  {v['endpoints']:4d} endpoints in {v['files']:3d} files")


if __name__ == "__main__":
    main()
