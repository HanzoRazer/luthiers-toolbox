from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt

from .grid import Grid


def heatmap_scatter(
    grid: Grid,
    values_by_id: Dict[str, float],
    *,
    title: str,
    out_path: Path,
) -> None:
    xs = np.array([p.x for p in grid.points], dtype=np.float32)
    ys = np.array([p.y for p in grid.points], dtype=np.float32)
    vs = np.array([float(values_by_id.get(p.id, 0.0)) for p in grid.points], dtype=np.float32)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.title(title)
    sc = plt.scatter(xs, ys, c=vs)
    plt.xlabel(f"x ({grid.units})")
    plt.ylabel(f"y ({grid.units})")
    plt.gca().set_aspect("equal", adjustable="box")
    plt.colorbar(sc, label="value")
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_curve(
    x: np.ndarray,
    y: np.ndarray,
    *,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.title(title)
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150)
    plt.close()
