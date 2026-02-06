"""Measurement schema validation tests."""

import json
import pathlib

from jsonschema import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_tap_example_validates() -> None:
    tap = json.load(open(ROOT / "examples/measurement/tap_tone.json"))
    schema = json.load(open(ROOT / "schemas/measurement/tap_peaks.schema.json"))
    validate(tap, schema)


def test_moe_example_validates() -> None:
    moe = json.load(open(ROOT / "examples/measurement/bending_test.json"))
    schema = json.load(open(ROOT / "schemas/measurement/moe_result.schema.json"))
    validate(moe, schema)


def test_manifest_example_validates() -> None:
    man = json.load(open(ROOT / "examples/measurement/manifest.json"))
    schema = json.load(open(ROOT / "schemas/measurement/manifest.schema.json"))
    validate(man, schema)
