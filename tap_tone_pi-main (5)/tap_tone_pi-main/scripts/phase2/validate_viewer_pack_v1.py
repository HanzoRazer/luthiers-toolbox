#!/usr/bin/env python3
"""
validate_viewer_pack_v1.py

Validate a viewer_pack_v1 bundle (directory or zip).

Checks:
  - manifest schema_version/schema_id constants
  - additionalProperties:false expectations (no unexpected keys)
  - file presence for all manifest files
  - sha256 + byte size per file
  - bundle_sha256 computed from manifest JSON bytes *before* adding bundle_sha256
  - relpath safety (no absolute paths, no .. traversal)

Exit codes:
  0 = OK
  2 = validation failed
  3 = runtime error (IO / parse)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# --------------------------
# Strict "additionalProperties:false" expectations
# --------------------------

ALLOWED_MANIFEST_KEYS = {
    "schema_version",
    "schema_id",
    "created_at_utc",
    "source_capdir",
    "detected_phase",
    "measurement_only",
    "interpretation",
    "points",
    "contents",
    "files",
    "bundle_sha256",
}

ALLOWED_CONTENTS_KEYS = {
    "audio",
    "spectra",
    "coherence",
    "ods",
    "wolf",
    "plots",
    "provenance",
}

ALLOWED_FILE_ENTRY_KEYS = {
    "relpath",
    "sha256",
    "bytes",
    "mime",
    "kind",
}


# --------------------------
# Helpers
# --------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_fileobj(fobj: io.BufferedReader) -> Tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = fobj.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        total += len(chunk)
    return h.hexdigest(), total


def die(msg: str, *, code: int = 2) -> int:
    print(f"[viewer-pack-validate] FAIL: {msg}", file=sys.stderr)
    return code


def warn(msg: str) -> None:
    print(f"[viewer-pack-validate] WARN: {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"[viewer-pack-validate] OK: {msg}", file=sys.stdout)


def assert_no_extra_keys(obj: Dict[str, Any], allowed: set, where: str) -> Optional[str]:
    extra = sorted(set(obj.keys()) - allowed)
    if extra:
        return f"{where} has unexpected keys: {extra}"
    return None


def assert_required_keys(obj: Dict[str, Any], required: Iterable[str], where: str) -> Optional[str]:
    missing = [k for k in required if k not in obj]
    if missing:
        return f"{where} missing required keys: {missing}"
    return None


def validate_relpath(relpath: str) -> Optional[str]:
    # Must be posix-like relative path without traversal
    if relpath.startswith("/") or relpath.startswith("\\"):
        return f"relpath must be relative, got absolute: {relpath}"
    # Prevent Windows drive paths
    if len(relpath) >= 2 and relpath[1] == ":":
        return f"relpath must not contain drive prefix: {relpath}"
    parts = relpath.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        return f"relpath must not contain '..' traversal: {relpath}"
    if any(p == "" for p in parts):
        # disallow // or leading/trailing slash
        return f"relpath must not contain empty path segments: {relpath}"
    return None


def canonical_manifest_bytes_without_bundle_sha(manifest: Dict[str, Any]) -> bytes:
    """
    Match exporter rule:
      bundle_sha256 = sha256(json.dumps(manifest_without_bundle_sha256, indent=2, sort_keys=True).encode("utf-8"))
    """
    m2 = dict(manifest)
    m2.pop("bundle_sha256", None)
    return json.dumps(m2, indent=2, sort_keys=True).encode("utf-8")


# --------------------------
# IO Abstraction: dir or zip
# --------------------------

@dataclass
class PackSource:
    kind: str  # "dir" or "zip"
    root: Path
    zf: Optional[zipfile.ZipFile] = None
    zip_prefix: str = ""  # prefix for nested zip entries (e.g., "viewer_pack_v1/")

    def open_relpath(self, relpath: str) -> io.BufferedReader:
        if self.kind == "dir":
            fp = (self.root / relpath).resolve()
            # ensure within root
            if not str(fp).startswith(str(self.root.resolve())):
                raise ValueError(f"relpath escapes root: {relpath}")
            return open(fp, "rb")
        else:
            assert self.zf is not None
            return self.zf.open(self.zip_prefix + relpath, "r")  # type: ignore[return-value]

    def exists_relpath(self, relpath: str) -> bool:
        if self.kind == "dir":
            return (self.root / relpath).is_file()
        else:
            assert self.zf is not None
            try:
                self.zf.getinfo(self.zip_prefix + relpath)
                return True
            except KeyError:
                return False

    def read_text(self, relpath: str) -> str:
        with self.open_relpath(relpath) as f:
            data = f.read()
        return data.decode("utf-8", errors="strict")


def open_pack(path: str) -> PackSource:
    p = Path(path)
    if p.is_dir():
        return PackSource(kind="dir", root=p.resolve(), zf=None)

    if p.is_file() and p.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(str(p), "r")
        # Detect if manifest is at root or nested in a single top-level folder
        names = zf.namelist()
        if "manifest.json" in names:
            return PackSource(kind="zip", root=p.resolve(), zf=zf, zip_prefix="")
        # Check for single top-level folder containing manifest.json
        prefixes = set()
        for n in names:
            if "/" in n:
                prefixes.add(n.split("/")[0] + "/")
        if len(prefixes) == 1:
            prefix = list(prefixes)[0]
            if prefix + "manifest.json" in names:
                return PackSource(kind="zip", root=p.resolve(), zf=zf, zip_prefix=prefix)
        raise FileNotFoundError(f"manifest.json not found at root or in single top-level folder of zip: {path}")

    raise FileNotFoundError(f"Not a directory or .zip: {path}")


# --------------------------
# Validation
# --------------------------

def validate_manifest_shape(manifest: Dict[str, Any]) -> Optional[str]:
    # additionalProperties:false expectations
    err = assert_no_extra_keys(manifest, ALLOWED_MANIFEST_KEYS, "manifest")
    if err:
        return err

    required = [
        "schema_version",
        "schema_id",
        "created_at_utc",
        "source_capdir",
        "detected_phase",
        "measurement_only",
        "interpretation",
        "points",
        "contents",
        "files",
        "bundle_sha256",
    ]
    err = assert_required_keys(manifest, required, "manifest")
    if err:
        return err

    if manifest.get("schema_version") != "v1":
        return f"manifest.schema_version must be 'v1', got {manifest.get('schema_version')!r}"
    if manifest.get("schema_id") != "viewer_pack_v1":
        return f"manifest.schema_id must be 'viewer_pack_v1', got {manifest.get('schema_id')!r}"

    # contents strict keys
    contents = manifest.get("contents")
    if not isinstance(contents, dict):
        return "manifest.contents must be an object"
    err = assert_no_extra_keys(contents, ALLOWED_CONTENTS_KEYS, "manifest.contents")
    if err:
        return err
    err = assert_required_keys(contents, sorted(ALLOWED_CONTENTS_KEYS), "manifest.contents")
    if err:
        return err
    for k, v in contents.items():
        if not isinstance(v, bool):
            return f"manifest.contents.{k} must be boolean, got {type(v).__name__}"

    # files entries
    files = manifest.get("files")
    if not isinstance(files, list):
        return "manifest.files must be an array"
    for i, e in enumerate(files):
        if not isinstance(e, dict):
            return f"manifest.files[{i}] must be an object"
        err = assert_no_extra_keys(e, ALLOWED_FILE_ENTRY_KEYS, f"manifest.files[{i}]")
        if err:
            return err
        err = assert_required_keys(e, ["relpath", "sha256", "bytes", "mime", "kind"], f"manifest.files[{i}]")
        if err:
            return err
        if not isinstance(e["relpath"], str):
            return f"manifest.files[{i}].relpath must be string"
        rp_err = validate_relpath(e["relpath"])
        if rp_err:
            return f"manifest.files[{i}]: {rp_err}"
        if not isinstance(e["sha256"], str) or len(e["sha256"]) < 16:
            return f"manifest.files[{i}].sha256 must be string (looks like hash)"
        if not isinstance(e["bytes"], int) or e["bytes"] < 0:
            return f"manifest.files[{i}].bytes must be non-negative int"
        if not isinstance(e["mime"], str) or not e["mime"]:
            return f"manifest.files[{i}].mime must be non-empty string"
        if not isinstance(e["kind"], str) or not e["kind"]:
            return f"manifest.files[{i}].kind must be non-empty string"

    # points
    pts = manifest.get("points")
    if not isinstance(pts, list) or not all(isinstance(x, str) for x in pts):
        return "manifest.points must be an array of strings"

    return None


def validate_bundle_sha(manifest: Dict[str, Any]) -> Optional[str]:
    expected = sha256_bytes(canonical_manifest_bytes_without_bundle_sha(manifest))
    got = manifest.get("bundle_sha256")
    if got != expected:
        return f"bundle_sha256 mismatch: manifest={got!r} computed={expected!r}"
    return None


def validate_files(pack: PackSource, manifest: Dict[str, Any], *, max_errors: int = 50) -> Tuple[int, List[str]]:
    errors: List[str] = []
    files: List[Dict[str, Any]] = manifest["files"]

    for e in files:
        relpath = e["relpath"]
        if not pack.exists_relpath(relpath):
            errors.append(f"missing file in pack: {relpath}")
            if len(errors) >= max_errors:
                return (len(errors), errors)
            continue

        try:
            with pack.open_relpath(relpath) as f:
                got_sha, got_bytes = sha256_fileobj(f)  # reads fully
        except Exception as ex:
            errors.append(f"read error: {relpath}: {ex}")
            if len(errors) >= max_errors:
                return (len(errors), errors)
            continue

        if got_sha != e["sha256"]:
            errors.append(f"sha256 mismatch: {relpath}: manifest={e['sha256']} actual={got_sha}")
        if got_bytes != e["bytes"]:
            errors.append(f"bytes mismatch: {relpath}: manifest={e['bytes']} actual={got_bytes}")

        if len(errors) >= max_errors:
            return (len(errors), errors)

    return (len(errors), errors)


# --------------------------
# CLI
# --------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Validate viewer_pack_v1 bundle (dir or zip).")
    ap.add_argument("--pack", required=True, help="Path to viewer_pack_v1 directory or .zip")
    ap.add_argument("--manifest", default="manifest.json", help="Manifest path inside pack (default: manifest.json)")
    ap.add_argument("--max-errors", type=int, default=50, help="Max errors to print before truncating")
    ap.add_argument("--quiet", action="store_true", help="Only print failures")
    args = ap.parse_args()

    try:
        pack = open_pack(args.pack)
    except Exception as e:
        return die(f"cannot open pack: {e}", code=3)

    try:
        manifest_text = pack.read_text(args.manifest)
        manifest = json.loads(manifest_text)
    except Exception as e:
        return die(f"cannot read/parse manifest: {e}", code=3)
    finally:
        if pack.zf is not None:
            pack.zf.close()

    # Re-open for file validation (zip needs open handle during reads)
    try:
        pack = open_pack(args.pack)
    except Exception as e:
        return die(f"cannot reopen pack: {e}", code=3)

    # Shape checks
    err = validate_manifest_shape(manifest)
    if err:
        if pack.zf is not None:
            pack.zf.close()
        return die(err, code=2)

    # bundle_sha256 check
    err = validate_bundle_sha(manifest)
    if err:
        if pack.zf is not None:
            pack.zf.close()
        return die(err, code=2)

    # file checks
    n_err, errors = validate_files(pack, manifest, max_errors=args.max_errors)

    if pack.zf is not None:
        pack.zf.close()

    if n_err:
        print(f"[viewer-pack-validate] FAIL: {n_err} file validation errors", file=sys.stderr)
        for msg in errors[: args.max_errors]:
            print(f"  - {msg}", file=sys.stderr)
        if n_err > args.max_errors:
            print(f"  ... truncated (max-errors={args.max_errors})", file=sys.stderr)
        return 2

    if not args.quiet:
        ok("manifest shape OK")
        ok("bundle_sha256 OK")
        ok("all files present + hashes OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
