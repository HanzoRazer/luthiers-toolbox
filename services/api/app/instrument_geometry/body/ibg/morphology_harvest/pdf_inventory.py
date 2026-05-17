"""
PDF Inventory — Corpus Scanner and Manifest Generator
======================================================

Implements configurable corpus scanning with:
- Absolute path support
- Repo-relative path support
- Future mounted storage support

No hardcoded paths.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
Governance: MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# PyMuPDF for PDF parsing (existing dependency)
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


# Instrument family detection patterns
FAMILY_PATTERNS: Dict[str, List[str]] = {
    "dreadnought": ["dreadnought", "dread", "d-28", "d28", "martin d"],
    "jumbo": ["jumbo", "j-45", "j45", "super jumbo", "sj-200"],
    "orchestra": ["orchestra", "om-", "om ", "000", "triple-0"],
    "parlor": ["parlor", "parlour", "size 0", "size 1"],
    "classical": ["classical", "nylon", "flamenco"],
    "stratocaster": ["stratocaster", "strat", "s-type"],
    "telecaster": ["telecaster", "tele", "t-type"],
    "les_paul": ["les paul", "lp", "singlecut", "single cut"],
    "sg": ["sg ", "sg-", "double cut"],
    "explorer": ["explorer", "exp"],
    "flying_v": ["flying v", "flying-v", "v shape"],
    "jazzmaster": ["jazzmaster", "jazz master", "offset"],
    "bass": ["bass", "p-bass", "j-bass", "precision", "jazz bass"],
    "ukulele": ["ukulele", "uke", "soprano", "concert", "tenor", "baritone"],
    "mandolin": ["mandolin", "mando", "a-style", "f-style"],
    "banjo": ["banjo", "5-string", "resonator"],
    "cuatro": ["cuatro", "puertorrique"],
}


@dataclass
class PDFInventoryEntry:
    """
    Single PDF inventory entry with metadata.

    Follows DXFInventory pattern from sandbox.
    """
    # Identity
    file_path: str
    file_name: str
    relative_path: str  # Relative to corpus root

    # File metadata
    file_size_bytes: int
    page_count: int
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    # Content classification
    has_text: bool = False
    has_images: bool = False
    has_vectors: bool = False
    vector_text_present: bool = False
    raster_content_present: bool = False

    # Dimension detection
    dimensions_detected: bool = False
    dimension_strings: List[str] = field(default_factory=list)

    # Instrument family guessing
    instrument_family_guess_raw: Optional[str] = None
    instrument_family_normalized: Optional[str] = None
    family_confidence: float = 0.0

    # Page dimensions
    page_dimensions: List[Dict[str, float]] = field(default_factory=list)

    # Keywords detected
    keywords_detected: List[str] = field(default_factory=list)

    # Parent folder (for diversity selection)
    parent_folder: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CorpusManifest:
    """
    Manifest for entire corpus inventory.

    Index file format: manifest.json
    """
    manifest_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    corpus_root: str = ""
    governance_doc: str = "docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md"

    # Statistics
    total_pdfs: int = 0
    with_text: int = 0
    with_dimensions: int = 0
    family_distribution: Dict[str, int] = field(default_factory=dict)

    # Entries
    entries: List[PDFInventoryEntry] = field(default_factory=list)

    # Representative sample suggestions
    suggested_representatives: List[str] = field(default_factory=list)

    def add_entry(self, entry: PDFInventoryEntry) -> None:
        """Add entry and update statistics."""
        self.entries.append(entry)
        self.total_pdfs = len(self.entries)
        self.with_text = sum(1 for e in self.entries if e.has_text)
        self.with_dimensions = sum(1 for e in self.entries if e.dimensions_detected)

        # Update family distribution
        if entry.instrument_family_normalized:
            family = entry.instrument_family_normalized
            self.family_distribution[family] = self.family_distribution.get(family, 0) + 1

    def suggest_representatives(self, count: int = 10) -> List[str]:
        """
        Auto-suggest representative PDFs based on diversity.

        Selection heuristics:
        - Distinct parent folders
        - Distinct filename family hints
        - Mix of vector-text and raster-heavy
        - Presence of dimension strings
        - Presence of body/neck/headstock keywords
        """
        candidates = []

        for entry in self.entries:
            score = 0

            # Prefer PDFs with dimensions
            if entry.dimensions_detected:
                score += 30

            # Prefer PDFs with text
            if entry.has_text:
                score += 20

            # Prefer PDFs with family classification
            if entry.instrument_family_normalized:
                score += 15

            # Prefer PDFs with keywords
            keywords_of_interest = {"body", "neck", "headstock", "fretboard", "scale"}
            matching_keywords = set(k.lower() for k in entry.keywords_detected) & keywords_of_interest
            score += len(matching_keywords) * 10

            # Prefer larger files (more content)
            if entry.file_size_bytes > 500_000:
                score += 5

            candidates.append((entry.file_path, score, entry))

        # Sort by score
        candidates.sort(key=lambda x: -x[1])

        # Select diverse representatives
        selected = []
        selected_folders = set()
        selected_families = set()

        for path, score, entry in candidates:
            if len(selected) >= count:
                break

            # Check diversity
            folder = entry.parent_folder
            family = entry.instrument_family_normalized or "unknown"

            # Prefer new folders and families
            folder_bonus = folder not in selected_folders
            family_bonus = family not in selected_families

            if folder_bonus or family_bonus or len(selected) < 3:
                selected.append(path)
                selected_folders.add(folder)
                selected_families.add(family)

        self.suggested_representatives = selected
        return selected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "created_at": self.created_at,
            "corpus_root": self.corpus_root,
            "governance_doc": self.governance_doc,
            "statistics": {
                "total_pdfs": self.total_pdfs,
                "with_text": self.with_text,
                "with_dimensions": self.with_dimensions,
                "family_distribution": self.family_distribution,
            },
            "suggested_representatives": self.suggested_representatives,
            "entries": [e.to_dict() for e in self.entries],
        }

    def save(self, path: str) -> None:
        """Save manifest to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "CorpusManifest":
        """Load manifest from JSON file."""
        with open(path) as f:
            data = json.load(f)

        manifest = cls(
            manifest_version=data.get("manifest_version", "1.0.0"),
            created_at=data.get("created_at", ""),
            corpus_root=data.get("corpus_root", ""),
        )

        stats = data.get("statistics", {})
        manifest.total_pdfs = stats.get("total_pdfs", 0)
        manifest.with_text = stats.get("with_text", 0)
        manifest.with_dimensions = stats.get("with_dimensions", 0)
        manifest.family_distribution = stats.get("family_distribution", {})
        manifest.suggested_representatives = data.get("suggested_representatives", [])

        # Load entries
        for entry_data in data.get("entries", []):
            entry = PDFInventoryEntry(
                file_path=entry_data["file_path"],
                file_name=entry_data["file_name"],
                relative_path=entry_data["relative_path"],
                file_size_bytes=entry_data["file_size_bytes"],
                page_count=entry_data["page_count"],
            )
            for key in ["has_text", "has_images", "dimensions_detected",
                       "instrument_family_guess_raw", "instrument_family_normalized"]:
                if key in entry_data:
                    setattr(entry, key, entry_data[key])
            manifest.entries.append(entry)

        return manifest


class PDFInventoryScanner:
    """
    Scans corpus directory for PDF files and generates inventory.

    Supports:
    - Absolute paths
    - Repo-relative paths
    - Future mounted storage paths
    """

    def __init__(self, corpus_root: str):
        """
        Initialize scanner with corpus root.

        Args:
            corpus_root: Path to corpus directory (absolute or relative)
        """
        self.corpus_root = self._resolve_path(corpus_root)

        if not self.corpus_root.exists():
            raise FileNotFoundError(f"Corpus root not found: {corpus_root}")

        if not self.corpus_root.is_dir():
            raise NotADirectoryError(f"Corpus root is not a directory: {corpus_root}")

    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve path to absolute Path object.

        Handles:
        - Absolute paths
        - Relative paths (resolved from cwd)
        - Home directory expansion (~)
        """
        path = Path(path_str).expanduser()

        if path.is_absolute():
            return path

        # Try repo-relative first
        repo_root = Path(__file__).parents[7]  # services/api/app/.../morphology_harvest -> repo root
        repo_relative = repo_root / path_str
        if repo_relative.exists():
            return repo_relative

        # Fall back to cwd-relative
        return Path.cwd() / path_str

    def scan(
        self,
        pattern: str = "**/*.pdf",
        max_files: Optional[int] = None,
        progress_callback=None,
    ) -> CorpusManifest:
        """
        Scan corpus and generate manifest.

        Args:
            pattern: Glob pattern for finding PDFs
            max_files: Maximum files to scan (None for all)
            progress_callback: Optional callback(current, total, path)

        Returns:
            CorpusManifest with all entries
        """
        manifest = CorpusManifest(corpus_root=str(self.corpus_root))

        pdf_paths = list(self.corpus_root.glob(pattern))
        total = len(pdf_paths) if max_files is None else min(len(pdf_paths), max_files)

        for i, pdf_path in enumerate(pdf_paths[:total] if max_files else pdf_paths):
            if progress_callback:
                progress_callback(i + 1, total, str(pdf_path))

            try:
                entry = self._scan_pdf(pdf_path)
                manifest.add_entry(entry)
            except Exception as e:
                print(f"  SKIP {pdf_path.name}: {e}")

        # Generate representative suggestions
        manifest.suggest_representatives()

        return manifest

    def _scan_pdf(self, pdf_path: Path) -> PDFInventoryEntry:
        """
        Scan single PDF and extract metadata.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFInventoryEntry with metadata
        """
        entry = PDFInventoryEntry(
            file_path=str(pdf_path),
            file_name=pdf_path.name,
            relative_path=str(pdf_path.relative_to(self.corpus_root)),
            file_size_bytes=pdf_path.stat().st_size,
            page_count=0,
            parent_folder=pdf_path.parent.name,
        )

        # Get file dates
        stat = pdf_path.stat()
        entry.modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

        if not HAS_FITZ:
            return entry

        # Scan with PyMuPDF
        try:
            doc = fitz.open(str(pdf_path))
            entry.page_count = len(doc)

            all_text = []
            all_dimensions = []
            page_dims = []

            for page in doc:
                # Page dimensions
                rect = page.rect
                page_dims.append({
                    "width_pt": rect.width,
                    "height_pt": rect.height,
                    "width_mm": rect.width * 0.352778,
                    "height_mm": rect.height * 0.352778,
                })

                # Text extraction
                text = page.get_text()
                if text.strip():
                    entry.has_text = True
                    entry.vector_text_present = True
                    all_text.append(text)

                # Image detection
                images = page.get_images()
                if images:
                    entry.has_images = True
                    entry.raster_content_present = True

                # Vector detection (drawings)
                drawings = page.get_drawings()
                if drawings:
                    entry.has_vectors = True

            doc.close()

            entry.page_dimensions = page_dims

            # Process extracted text
            full_text = " ".join(all_text).lower()

            # Dimension detection
            dim_patterns = [
                r'\d+\.?\d*\s*(?:mm|cm|in|inch|inches|")',
                r'\d+\s*/\s*\d+\s*(?:"|in)',
                r'\d+\.?\d*\s*x\s*\d+\.?\d*',
            ]
            for pattern in dim_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    entry.dimensions_detected = True
                    entry.dimension_strings.extend(matches[:20])

            # Keyword detection
            keywords = ["body", "neck", "headstock", "fretboard", "bridge",
                       "nut", "scale", "fret", "soundhole", "bracing",
                       "top", "back", "side", "binding"]
            for kw in keywords:
                if kw in full_text:
                    entry.keywords_detected.append(kw)

            # Instrument family guessing
            entry.instrument_family_guess_raw, entry.instrument_family_normalized, entry.family_confidence = \
                self._guess_instrument_family(pdf_path.name, full_text)

        except Exception as e:
            print(f"  Warning scanning {pdf_path.name}: {e}")

        return entry

    def _guess_instrument_family(
        self,
        filename: str,
        text_content: str
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Guess instrument family from filename and content.

        Returns:
            (raw_guess, normalized_family, confidence)
        """
        search_text = (filename + " " + text_content).lower()

        best_family = None
        best_match = None
        best_confidence = 0.0

        for family, patterns in FAMILY_PATTERNS.items():
            for pattern in patterns:
                if pattern in search_text:
                    # Confidence based on specificity
                    confidence = min(0.9, 0.5 + len(pattern) * 0.05)

                    if confidence > best_confidence:
                        best_family = family
                        best_match = pattern
                        best_confidence = confidence

        return best_match, best_family, best_confidence


def scan_corpus(
    corpus_root: str,
    pattern: str = "**/*.pdf",
    max_files: Optional[int] = None,
    output_manifest: Optional[str] = None,
) -> CorpusManifest:
    """
    Convenience function to scan corpus and optionally save manifest.

    Args:
        corpus_root: Path to corpus directory
        pattern: Glob pattern for PDFs
        max_files: Maximum files to scan
        output_manifest: Optional path to save manifest

    Returns:
        CorpusManifest
    """
    scanner = PDFInventoryScanner(corpus_root)

    def progress(current, total, path):
        print(f"  [{current}/{total}] {Path(path).name}")

    manifest = scanner.scan(pattern, max_files, progress)

    if output_manifest:
        manifest.save(output_manifest)
        print(f"Saved manifest: {output_manifest}")

    return manifest


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan PDF corpus and generate inventory manifest"
    )
    parser.add_argument(
        "--corpus-root",
        required=True,
        help="Path to corpus directory (absolute or relative)"
    )
    parser.add_argument(
        "--pattern",
        default="**/*.pdf",
        help="Glob pattern for finding PDFs (default: **/*.pdf)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum files to scan (default: all)"
    )
    parser.add_argument(
        "--output",
        default="manifest.json",
        help="Output manifest path (default: manifest.json)"
    )

    args = parser.parse_args()

    print(f"Scanning corpus: {args.corpus_root}")
    manifest = scan_corpus(
        args.corpus_root,
        args.pattern,
        args.max_files,
        args.output,
    )

    print(f"\nInventory complete:")
    print(f"  Total PDFs: {manifest.total_pdfs}")
    print(f"  With text: {manifest.with_text}")
    print(f"  With dimensions: {manifest.with_dimensions}")
    print(f"  Family distribution: {manifest.family_distribution}")
    print(f"\nSuggested representatives:")
    for path in manifest.suggested_representatives:
        print(f"  - {path}")
