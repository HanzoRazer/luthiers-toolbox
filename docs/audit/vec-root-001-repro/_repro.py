"""Shared environment resolution for the VEC-ROOT-001 reproduction scripts.

Every script in this directory imports from here. It exists so that the eleven scripts have
**one** set of environment assumptions, stated in one place and checked before any of them runs.

What it guarantees, and why each one is here:

1. **The repository is found, not assumed.** REPO_ROOT is discovered by walking up from this
   file to the enclosing .git. No absolute path is written down anywhere.

2. **The pinned revision is verified, not asserted.** The audit's numbers were measured against
   blob f3e7d802 of services/photo-vectorizer/edge_to_dxf.py. check_pinned_source() hashes the
   file actually imported and says which revision you are on -- including naming the +26 line
   offset if you are on main. A document that pins a revision and then imports whatever happens
   to be on disk has pinned nothing.

3. **The corpus is addressed by name, and by content.** Inputs are third-party plan material and
   are not in this repository (owner ruling R1 / SC-A02). corpus() resolves a logical name
   against --corpus-root / LTB_CORPUS_ROOT, then checks the file's SHA-256 against the value
   recorded in README.md. A run against a different file is caught immediately, not argued about
   afterwards.

4. **Nothing is written inside the repository.** work_dir() and out_path() return locations under
   a temporary directory by default, and refuse any --work-dir or --out-dir that resolves inside
   the checkout. Working copies and renders are run artifacts, not repository content.

5. **Absence is loud.** A missing corpus file exits NOT_RUN_SOURCE_ABSENT (2) naming what it
   looked for and where. A reproduction record that quietly skips the run it was meant to make is
   a record that cannot fail.

Usage, from a fresh clone:

    pip install opencv-python numpy
    python docs/audit/vec-root-001-repro/cuatro_stage_census.py \
        --corpus-root /path/to/your/plans --out-dir /tmp/vec-root-001

--corpus-root may be given as LTB_CORPUS_ROOT instead. --repo-root / LTB_REPO_ROOT overrides
discovery when running against a checkout other than the one holding this file.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

__all__ = [
    "REPO_ROOT", "ARGS", "etd", "extract_blueprint_to_dxf",
    "corpus", "work_dir", "out_path", "imread", "banner",
    "NOT_RUN_SOURCE_ABSENT", "ENVIRONMENT_MISMATCH",
]

NOT_RUN_SOURCE_ABSENT = 2
ENVIRONMENT_MISMATCH = 3

# The revision the audit's measurements were taken at, and the one it merges into.
PINNED_BLOB = "f3e7d802fefaa95b4304d3d6d41f3087b836e8c9"   # ffd155e4, edge_to_dxf.py
MAIN_BLOB = "c847c04365d37230d7d43d8e872909fbbee942cd"     # main, after BR-037 (97460755)
SUBJECT = "services/photo-vectorizer/edge_to_dxf.py"

# Logical name -> (path relative to --corpus-root, SHA-256 as recorded in README.md section 2).
# The archtop pair is one AI-generated image and its rembg foreground; the other two are plans.
CORPUS = {
    "cuatro": (
        "cuatro_ascii.png",
        "2d7f85f5040d3d21f5fe9918e7e8d40205406240534fa858af34ce91e0fcd0f9",
    ),
    "l00": (
        "Gibson-L0-IN.png",
        "2a3fea551282feef07a4ed58d1c1d7880518c690a0a6d6e9ab3148112f80fda7",
    ),
    "archtop_foreground": (
        "Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_02_foreground.jpg",
        "ee2db7346c9fb29b27b48a1eade4e7d473b194b198e552705d51c6f25a383f86",
    ),
    "archtop_original": (
        "Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_00_original.jpg",
        "997634c9fc4eb3a39b417ce193850fe36d979decfd26c0b81750e6c7272a98ad",
    ),
}


def _die(code, *lines):
    print()
    for ln in lines:
        print(ln)
    sys.exit(code)


def _find_repo_root(start):
    override = os.environ.get("LTB_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    for d in [start, *start.parents]:
        if (d / ".git").exists():
            return d
    _die(ENVIRONMENT_MISMATCH,
         "ENVIRONMENT_MISMATCH: no enclosing .git found above",
         "  %s" % start,
         "Set LTB_REPO_ROOT or pass --repo-root to name the checkout to run against.")


def _parse_args():
    ap = argparse.ArgumentParser(
        add_help=True,
        description="VEC-ROOT-001 reproduction script. See docs/audit/vec-root-001-repro/README.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=os.environ.get("LTB_REPO_ROOT"),
                    help="checkout to import edge_to_dxf from (default: discovered from .git)")
    ap.add_argument("--corpus-root", default=os.environ.get("LTB_CORPUS_ROOT"),
                    help="directory holding the source plans (not in this repository)")
    ap.add_argument("--work-dir", default=None,
                    help="scratch directory for working copies (default: a temp directory)")
    ap.add_argument("--out-dir", default=os.environ.get("LTB_OUT_DIR"),
                    help="where renders are written (default: a temp directory). "
                         "Must not be inside the repository.")
    ap.add_argument("--allow-revision-drift", action="store_true",
                    help="run even though the imported edge_to_dxf.py is not the pinned blob")
    args, _unknown = ap.parse_known_args()
    return args


ARGS = _parse_args()
REPO_ROOT = (Path(ARGS.repo_root).expanduser().resolve() if ARGS.repo_root
             else _find_repo_root(Path(__file__).resolve().parent))


def _git_blob_sha1(path):
    """Git's blob id: sha1 over the header 'blob <len>' NUL, then the raw bytes."""
    data = path.read_bytes()
    h = hashlib.sha1()
    h.update(("blob %d" % len(data)).encode("ascii") + b"\x00")
    h.update(data)
    return h.hexdigest()


def check_pinned_source():
    """Report which revision of the subject file is about to be imported.

    Returns "pinned", "main" or "unknown". Exits ENVIRONMENT_MISMATCH on an unknown revision
    unless --allow-revision-drift was passed.
    """
    subject = REPO_ROOT / SUBJECT
    if not subject.is_file():
        _die(ENVIRONMENT_MISMATCH,
             "ENVIRONMENT_MISMATCH: %s not found under" % SUBJECT,
             "  %s" % REPO_ROOT,
             "This is not a luthiers-toolbox checkout, or the path has moved.")
    blob = _git_blob_sha1(subject)
    if blob == PINNED_BLOB:
        print("[revision] %s is the PINNED blob %s (ffd155e4) -- the audit's line numbers "
              "apply as written." % (SUBJECT, blob[:12]))
        return "pinned"
    if blob == MAIN_BLOB:
        print("[revision] %s is MAIN blob %s (after BR-037, 97460755)." % (SUBJECT, blob[:12]))
        print("           The eligibility block is byte-identical but sits 26 lines later: "
              "967-976, not 941-950.")
        print("           Measurements are expected to reproduce; audit section 0a has the "
              "full line map.")
        return "main"
    print("[revision] %s is blob %s, which is NEITHER the pinned revision (%s)"
          % (SUBJECT, blob[:12], PINNED_BLOB[:12]))
    print("           nor main (%s). Results are not comparable to the audit."
          % MAIN_BLOB[:12])
    if not ARGS.allow_revision_drift:
        _die(ENVIRONMENT_MISMATCH,
             "Refusing to run. Check out ffd155e4, or pass --allow-revision-drift to",
             "measure this revision anyway (the audit's numbers will not apply).")
    print("           --allow-revision-drift given; continuing.")
    return "unknown"


REVISION = check_pinned_source()

sys.path.insert(0, str(REPO_ROOT / "services" / "api"))
sys.path.insert(0, str(REPO_ROOT / "services" / "photo-vectorizer"))

try:
    import edge_to_dxf as etd                                            # noqa: E402
    from app.services.blueprint_extract import extract_blueprint_to_dxf  # noqa: E402
except ImportError as exc:                                               # pragma: no cover
    _die(ENVIRONMENT_MISMATCH,
         "ENVIRONMENT_MISMATCH: could not import the vectorizer: %s" % exc,
         "  repo root: %s" % REPO_ROOT,
         "Install the runtime dependencies (opencv-python, numpy, ezdxf, and the API's "
         "requirements) and re-run.")

_WORK = None


def _sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _reject_if_inside_repo(p, flag):
    try:
        p.relative_to(REPO_ROOT)
    except ValueError:
        return
    _die(ENVIRONMENT_MISMATCH,
         "ENVIRONMENT_MISMATCH: %s resolves inside the repository:" % flag,
         "  %s" % p,
         "  repo: %s" % REPO_ROOT,
         "These scripts do not write into the checkout. Choose a location outside it.")


def corpus(name, required=True):
    """Resolve a source image by logical name and verify its SHA-256.

    The corpus is not in this repository and will not be: the inputs are third-party plan
    material under owner ruling R1 / SC-A02. Point --corpus-root at your own copy.
    """
    rel, expected = CORPUS[name]
    root = ARGS.corpus_root
    if not root:
        if not required:
            return None
        _die(NOT_RUN_SOURCE_ABSENT,
             "NOT_RUN_SOURCE_ABSENT: no corpus root given, needed '%s' (%s)." % (name, rel),
             "Pass --corpus-root <dir> or set LTB_CORPUS_ROOT.",
             "The source plans are not in this repository -- README.md section 2 lists the",
             "file names and their SHA-256.")
    src = Path(root).expanduser().resolve() / rel
    if not src.is_file():
        if not required:
            return None
        _die(NOT_RUN_SOURCE_ABSENT,
             "NOT_RUN_SOURCE_ABSENT: '%s' not found." % name,
             "  looked for: %s" % rel,
             "  under     : %s" % root,
             "  sha256    : %s" % expected,
             "Place the file there, or point --corpus-root at the directory holding it.")
    actual = _sha256(src)
    if actual != expected:
        _die(ENVIRONMENT_MISMATCH,
             "ENVIRONMENT_MISMATCH: '%s' is not the file the audit measured." % name,
             "  %s" % src,
             "  expected sha256 %s" % expected,
             "  actual   sha256 %s" % actual,
             "Results from a different input are not comparable to the audit's numbers.")
    print("[corpus] %s: %s  sha256 %s... OK" % (name, src.name, actual[:16]))
    return src


def work_dir():
    """A scratch directory for working copies. Never inside the repository."""
    global _WORK
    if _WORK is None:
        if ARGS.work_dir:
            w = Path(ARGS.work_dir).expanduser().resolve()
            _reject_if_inside_repo(w, "--work-dir")
            w.mkdir(parents=True, exist_ok=True)
        else:
            w = Path(tempfile.mkdtemp(prefix="vec-root-001-"))
        _WORK = w
        print("[work] %s" % w)
    return _WORK


def out_path(name):
    """Where a render is written. Defaults to a temp directory; never inside the repository."""
    if ARGS.out_dir:
        d = Path(ARGS.out_dir).expanduser().resolve()
        _reject_if_inside_repo(d, "--out-dir")
    else:
        d = work_dir() / "renders"
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def imread(path):
    """Read an image, failing loudly rather than returning None into the arithmetic below."""
    import cv2
    import numpy as np
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        _die(ENVIRONMENT_MISMATCH,
             "ENVIRONMENT_MISMATCH: OpenCV could not decode %s" % path,
             "The file exists and hashed correctly, so this is a codec problem, not a "
             "missing input.")
    return img


def banner(doc=None):
    """One line naming what is about to run, so a transcript says which script produced it."""
    script = Path(sys.argv[0]).name
    first = (doc or "").strip().splitlines()[0] if doc else ""
    print("\n=== VEC-ROOT-001 repro: %s ===" % script)
    if first:
        print(first)
    print()
