from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .deprecation_budget import (
    compute_deprecation_budget,
    get_budget_config,
    load_shadow_stats,
)


def _print_result(res, cfg, stats_path: str) -> None:
    payload = {
        "ok": res.ok,
        "enforced": res.enforced,
        "total_hits": res.total_hits,
        "legacy_hits": res.legacy_hits,
        "legacy_rate": res.legacy_rate,
        "reason": res.reason,
        "policy": {
            "enforce_after_utc": cfg.enforce_after_utc.isoformat(),
            "legacy_hits_max": cfg.legacy_hits_max,
            "legacy_rate_max": cfg.legacy_rate_max,
            "min_total_hits": cfg.min_total_hits,
            "stats_path": stats_path,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_check() -> int:
    cfg = get_budget_config()
    stats_path = cfg.stats_path

    p = Path(stats_path)
    if not p.exists():
        print(f"[deprecation_budget] ERROR: stats file not found: {stats_path}", file=sys.stderr)
        print(
            "[deprecation_budget] Hint: set ENDPOINT_STATS_PATH to your shadow stats JSON, "
            "or ensure the shadow aggregator writes it during tests/CI.",
            file=sys.stderr,
        )
        return 1

    try:
        stats = load_shadow_stats(stats_path)
    except Exception as e:
        print(f"[deprecation_budget] ERROR: failed to read stats: {e}", file=sys.stderr)
        return 1

    res = compute_deprecation_budget(stats, cfg)
    _print_result(res, cfg, stats_path)

    if res.ok:
        return 0
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="deprecation_budget")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Check legacy endpoint deprecation budget (fails CI after enforce date).")

    args = parser.parse_args(argv)

    if args.cmd == "check":
        return cmd_check()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
