"""Command-line entry points. No HTTP route is registered."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.physical_engineering.build_witness.analyze import analyze_package
from app.physical_engineering.build_witness.package import (
    PackageError,
    create_package,
    ingest_package,
    verify_package,
)
from app.physical_engineering.build_witness.report import render_package
from app.physical_engineering.build_witness.repository import WitnessRepository


def _ledger(args: argparse.Namespace) -> WitnessRepository | None:
    return WitnessRepository(args.registry) if args.registry else None


def create_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a blank build-response witness package")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--instrument-type", required=True)
    parser.add_argument("--registry", type=Path)
    args = parser.parse_args(argv)
    registry = args.registry or args.output.parent / "pem-witness-ledger"
    try:
        witness_id = create_package(args.output, args.instrument_type, WitnessRepository(registry))
    except PackageError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    print(witness_id)
    return 0


def ingest_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory a witness package and publish its manifest")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--replace-manifest", action="store_true")
    parser.add_argument("--registry", type=Path, help="witness ledger (default: pem-witness-ledger beside the package)")
    args = parser.parse_args(argv)
    if not args.write_manifest and not args.replace_manifest:
        print("pass --write-manifest or --replace-manifest", file=sys.stderr)
        return 1
    try:
        payload = ingest_package(args.package, replace=args.replace_manifest, repository=_ledger(args))
    except PackageError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    print(json.dumps({"states": payload["states"], "witness_id": payload["witness_id"]}))
    return 0


def verify_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a witness package")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--registry", type=Path, help="witness ledger (default: pem-witness-ledger beside the package)")
    args = parser.parse_args(argv)
    result = verify_package(args.package, repository=_ledger(args))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"exit={result['exit_code']} witness={result['witness_id']}")
    return int(result["exit_code"])


def analyze_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive descriptive observations from a verified package")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--derive", action="append", default=[])
    parser.add_argument("--compare-reference", action="store_true")
    parser.add_argument("--infer-species", action="store_true")
    args = parser.parse_args(argv)
    try:
        analyze_package(
            args.package,
            compare_reference=args.compare_reference,
            infer_species=args.infer_species,
            derive=args.derive,
        )
    except PackageError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    return 0


def render_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a factual witness report")
    parser.add_argument("--package", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        render_package(args.package)
    except PackageError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    return 0
