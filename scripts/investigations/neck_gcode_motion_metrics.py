#!/usr/bin/env python3
"""Offline G-code motion metrics for CAM-ORCHESTRATOR-RECOVERY-EVIDENCE-001.

Evidence tooling only. Reads G-code text files named on the command line,
resolves modal state block by block, and emits stable JSON. It never imports
the application, never touches a network or a machine, and writes only to the
path given with ``--out``.

Modal state is the whole point: in the pre-P1 neck program every rapid at
cutting depth inherited its Z from an earlier ``G1`` block and carried no Z
word of its own, so a line-by-line text search finds none of them. This
parser carries motion mode, position, spindle state and tool-length
compensation forward exactly as a controller would read them.

It is NOT a production parser and is not imported by anything in ``app/``.

Usage:
    python scripts/investigations/neck_gcode_motion_metrics.py \
        --plane-z 0.0 --out metrics.json  ARM_NAME=path/to/program.nc  [...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "neck-gcode-motion-metrics/1"

_WORD = re.compile(r"([A-Za-z])\s*([-+]?(?:\d+\.?\d*|\.\d+))")
_OP_HEADER = re.compile(r"\(\s*(OP\d+)\s*:")
_MOTION = {0: "G0", 1: "G1", 2: "G2", 3: "G3"}


class MalformedProgram(ValueError):
    """Raised when a program cannot be analysed honestly."""


@dataclass
class Block:
    line: int
    words: list[tuple[str, float]]
    raw: str
    op: str | None


@dataclass
class State:
    motion: str | None = None
    x: float | None = None
    y: float | None = None
    z: float | None = None
    spindle: str = "off"          # off | cw | ccw
    tool: int | None = None
    tlc_active: bool = False      # G43 in effect
    op: str | None = None


@dataclass
class Metrics:
    total_lines: int = 0
    blocks: int = 0
    g0_moves: int = 0
    g0_below_plane: int = 0
    g0_at_or_below_plane: int = 0
    g0_xy_below_plane: int = 0
    g0_xy_at_or_below_plane: int = 0
    g0_z_only_moves: int = 0
    g0_z_only_heights: dict[str, int] = field(default_factory=dict)
    tool_changes: list[dict] = field(default_factory=list)
    op_transitions: list[dict] = field(default_factory=list)
    g43_count: int = 0
    first_violation_lines: list[int] = field(default_factory=list)


def strip_comments(raw: str, number: int) -> tuple[str, bool]:
    """Remove ``( ... )`` comments by depth; report whether any were nested.

    Nesting is reported, not judged: strict RS274 ends a comment at the first
    ``)``, so how a given controller reads a nested comment is
    controller-specific and outside what this tool can certify.
    """
    out: list[str] = []
    depth = 0
    nested = False
    for ch in raw.split(";", 1)[0]:
        if ch == "(":
            depth += 1
            nested = nested or depth > 1
            continue
        if ch == ")":
            if depth == 0:
                raise MalformedProgram(f"line {number}: ')' with no open comment")
            depth -= 1
            continue
        if depth == 0:
            out.append(ch)
    if depth:
        raise MalformedProgram(f"line {number}: unclosed comment")
    return "".join(out), nested


def tokenize(text: str) -> list[Block]:
    """Strip comments, split words, and refuse anything that is not a word."""
    blocks, _ = _tokenize(text)
    return blocks


def _tokenize(text: str) -> tuple[list[Block], int]:
    if text is None or not text.strip():
        raise MalformedProgram("empty program")
    blocks: list[Block] = []
    nested_lines = 0
    op: str | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        header = _OP_HEADER.search(raw)
        if header:
            op = header.group(1)
        stripped, nested = strip_comments(raw, number)
        nested_lines += nested
        body = stripped.strip()
        if not body or body == "%":
            continue
        words = [(letter.upper(), float(value)) for letter, value in _WORD.findall(body)]
        residue = _WORD.sub("", body).strip()
        if residue or not words:
            raise MalformedProgram(f"line {number}: unparseable text {residue or body!r}")
        blocks.append(Block(number, words, raw.strip(), op))
    if not blocks:
        raise MalformedProgram("program has no executable blocks")
    return blocks, nested_lines


def _height_key(z: float) -> str:
    return f"{z:.3f}"


def analyse(text: str, plane_z: float) -> dict:
    """Resolve modal state and count what the order asks for."""
    blocks, nested_lines = _tokenize(text)
    m = Metrics(total_lines=len(text.splitlines()), blocks=len(blocks))
    s = State()
    pending_tc: dict | None = None

    for b in blocks:
        if b.op != s.op:
            m.op_transitions.append({
                "op": b.op, "line": b.line, "z_before": s.z,
                "spindle_before": s.spindle, "motion_before": s.motion,
            })
            s.op = b.op
        axes: dict[str, float] = {}
        for letter, value in b.words:
            if letter == "N":
                continue  # sequence numbers never change state
            if letter == "G":
                code = round(value, 1)
                if code in _MOTION:
                    s.motion = _MOTION[int(code)]
                elif code == 43:
                    s.tlc_active = True
                    m.g43_count += 1
                    if pending_tc is not None:
                        pending_tc["g43_before_next_motion"] = True
                elif code == 49:
                    s.tlc_active = False
            elif letter == "M":
                code = int(value)
                if code == 3:
                    s.spindle = "cw"
                elif code == 4:
                    s.spindle = "ccw"
                elif code == 5:
                    s.spindle = "off"
                elif code == 6:
                    pending_tc = {
                        "line": b.line, "op": b.op, "tool": s.tool,
                        "z_at_change": s.z, "spindle_at_change": s.spindle,
                        "g43_before_next_motion": False,
                    }
                    m.tool_changes.append(pending_tc)
            elif letter == "T":
                s.tool = int(value)
                if pending_tc is not None and pending_tc["line"] == b.line:
                    pending_tc["tool"] = s.tool
            elif letter in ("X", "Y", "Z"):
                axes[letter] = value

        if not axes:
            continue
        if s.motion is None:
            raise MalformedProgram(f"line {b.line}: axis words before any motion mode")
        for axis, value in axes.items():
            setattr(s, axis.lower(), value)
        if pending_tc is not None:
            pending_tc = None  # first motion after a tool change closes its window
        if s.motion != "G0":
            continue
        m.g0_moves += 1
        xy = "X" in axes or "Y" in axes
        if set(axes) == {"Z"}:
            m.g0_z_only_moves += 1
            key = _height_key(s.z)
            m.g0_z_only_heights[key] = m.g0_z_only_heights.get(key, 0) + 1
        if s.z is None:
            continue
        if s.z < plane_z:
            m.g0_below_plane += 1
            if len(m.first_violation_lines) < 10:
                m.first_violation_lines.append(b.line)
        if s.z <= plane_z:
            m.g0_at_or_below_plane += 1
        if xy and s.z < plane_z:
            m.g0_xy_below_plane += 1
        if xy and s.z <= plane_z:
            m.g0_xy_at_or_below_plane += 1

    unsafe_tc = [
        tc for tc in m.tool_changes
        if tc["z_at_change"] is None or tc["z_at_change"] <= plane_z
    ]
    return {
        "plane_z": plane_z,
        "total_lines": m.total_lines,
        "executable_blocks": m.blocks,
        "nested_comment_lines": nested_lines,
        "g0_moves": m.g0_moves,
        "g0_below_plane": m.g0_below_plane,
        "g0_at_or_below_plane": m.g0_at_or_below_plane,
        "g0_xy_below_plane": m.g0_xy_below_plane,
        "g0_xy_at_or_below_plane": m.g0_xy_at_or_below_plane,
        "g0_z_only_moves": m.g0_z_only_moves,
        "g0_z_only_heights": dict(sorted(m.g0_z_only_heights.items(), key=lambda kv: float(kv[0]))),
        "tool_change_count": len(m.tool_changes),
        "tool_changes_with_spindle_on": sum(1 for tc in m.tool_changes if tc["spindle_at_change"] != "off"),
        "tool_changes_without_known_retract": len(unsafe_tc),
        "tool_changes_without_g43": sum(1 for tc in m.tool_changes if not tc["g43_before_next_motion"]),
        "g43_count": m.g43_count,
        "tool_changes": m.tool_changes,
        "op_transitions": m.op_transitions,
        "first_violation_lines": m.first_violation_lines,
    }


def program_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_arm(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise SystemExit(f"arm must be NAME=PATH, got {spec!r}")
    name, path = spec.split("=", 1)
    if not name or not path:
        raise SystemExit(f"arm must be NAME=PATH, got {spec!r}")
    return name, Path(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plane-z", type=float, required=True,
                    help="workpiece top; a rapid below it moves through stock (no default)")
    ap.add_argument("--out", type=Path, required=True, help="JSON output path")
    ap.add_argument("arms", nargs="+", help="NAME=PATH to a G-code file")
    args = ap.parse_args(argv)

    report = {"schema": SCHEMA, "plane_z": args.plane_z, "arms": {}}
    for spec in args.arms:
        name, path = _parse_arm(spec)
        if name in report["arms"]:
            print(f"duplicate arm name {name!r}", file=sys.stderr)
            return 2
        if not path.is_file():
            print(f"{name}: no such file {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
        try:
            metrics = analyse(text, args.plane_z)
        except MalformedProgram as exc:
            print(f"{name}: refused: {exc}", file=sys.stderr)
            return 3
        metrics["sha256"] = program_sha256(text)
        metrics["source"] = path.name
        report["arms"][name] = metrics

    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
