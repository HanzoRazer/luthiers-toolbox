#!/usr/bin/env python3
"""Generate a deflection batch template."""

import csv
import sys

TEMPLATE = [
    {
        "method": "3point",
        "span_mm": 400,
        "width_mm": 20,
        "thickness_mm": 3.0,
        "force_N": 5.0,
        "deflection_mm": 0.62,
        "density_g_cm3": 0.41,
        "inner_span_mm": "",
    }
]


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "data/deflection_runs.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TEMPLATE[0].keys())
        w.writeheader()
        w.writerows(TEMPLATE)
    print(f"Wrote template: {out}")


if __name__ == "__main__":
    main()
