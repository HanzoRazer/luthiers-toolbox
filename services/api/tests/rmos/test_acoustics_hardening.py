"""
RMOS Acoustics Hardening Tests.

Tests for H7.2.2.1 security features:
1. No-path-disclosure: Response payloads must not contain filesystem paths
2. Signature verification: Valid signatures pass, expired fail, scope hierarchy works
3. Index rebuild: Creates correct _attachment_meta.json from run artifacts
4. Blob-exists truth table: All combinations of (in_index, blob_exists)
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest


# =============================================================================
# Test 1: No-Path-Disclosure
# =============================================================================


class TestNoPathDisclosure:
    """
    Verify that response schemas and data do NOT contain shard paths.

    A shard path looks like: /some/root/{sha[0:2]}/{sha[2:4]}/{sha}.ext
    or Windows-style: C:\\path\\ab\\cd\\abcdef...
    """

    PATH_PATTERNS = [
        # Unix absolute paths with sha256-like structure
        re.compile(r"/[a-zA-Z0-9_/.-]+/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{64}"),
        # Windows absolute paths
        re.compile(r"[A-Z]:\\[a-zA-Z0-9_\\.-]+\\[a-f0-9]{2}\\[a-f0-9]{2}\\[a-f0-9]{64}"),
        # Any path-like structure with shard directories
        re.compile(r"[/\\][a-f0-9]{2}[/\\][a-f0-9]{2}[/\\][a-f0-9]{64}"),
    ]

    def _contains_path(self, data: Any) -> bool:
        """Recursively check if data contains any shard path pattern."""
        if isinstance(data, str):
            for pattern in self.PATH_PATTERNS:
                if pattern.search(data):
                    return True
            return False
        elif isinstance(data, dict):
            for k, v in data.items():
                # Key "path" with sha256-like value is suspicious but allowed in some cases
                # But actual filesystem shard paths should fail
                if self._contains_path(v):
                    return True
            return False
        elif isinstance(data, (list, tuple)):
            for item in data:
                if self._contains_path(item):
                    return True
            return False
        return False

    def test_attachment_meta_public_no_path_fields(self):
        """AttachmentMetaPublic schema should not have path fields."""
        from app.rmos.runs_v2.acoustics_schemas import AttachmentMetaPublic

        # Get all field names
        fields = set(AttachmentMetaPublic.model_fields.keys())

        # These fields should NOT exist
        forbidden = {"path", "file_path", "shard_path", "storage_path", "blob_path"}
        overlap = fields & forbidden
        assert not overlap, f"AttachmentMetaPublic contains forbidden path fields: {overlap}"

    def test_attachment_exists_out_no_path_fields(self):
        """AttachmentExistsOut schema should not expose paths."""
        from app.rmos.runs_v2.acoustics_schemas import AttachmentExistsOut

        fields = set(AttachmentExistsOut.model_fields.keys())
        forbidden = {"path", "file_path", "shard_path", "storage_path", "blob_path"}
        overlap = fields & forbidden
        assert not overlap, f"AttachmentExistsOut contains forbidden path fields: {overlap}"

    def test_run_attachments_list_no_path_disclosure(self):
        """RunAttachmentsListOut should not leak paths in serialized output."""
        from app.rmos.runs_v2.acoustics_schemas import RunAttachmentsListOut, AttachmentMetaPublic

        sample = RunAttachmentsListOut(
            run_id="test-run-123",
            count=1,
            include_bytes=False,
            max_inline_bytes=2_000_000,
            attachments=[
                AttachmentMetaPublic(
                    sha256="abcd1234" * 8,
                    kind="test",
                    mime="application/json",
                    filename="test.json",
                    size_bytes=100,
                    download_url="/api/rmos/acoustics/attachments/abcd1234" * 8,
                )
            ],
        )

        # Serialize and check
        data = json.loads(sample.model_dump_json())
        assert not self._contains_path(data), "RunAttachmentsListOut contains path-like strings"

    def test_index_rebuild_out_no_path_disclosure(self):
        """IndexRebuildOut should not leak paths."""
        from app.rmos.runs_v2.acoustics_schemas import IndexRebuildOut

        sample = IndexRebuildOut(
            ok=True,
            runs_scanned=10,
            attachments_indexed=50,
            unique_sha256=45,
        )

        data = json.loads(sample.model_dump_json())
        assert not self._contains_path(data), "IndexRebuildOut contains path-like strings"


# =============================================================================
# Test 2: Signature Verification
# =============================================================================


class TestSignatureVerification:
    """
    Test HMAC signature creation and verification.

    Covers:
    - Valid signature passes
    - Expired signature fails
    - Wrong signature fails
    - Scope hierarchy: download token works for HEAD
    """

    @pytest.fixture(autouse=True)
    def setup_secret(self, monkeypatch):
        """Set up signing secret for tests."""
        monkeypatch.setenv("RMOS_SIGNED_URL_SECRET", "test-secret-key-12345")

    def test_valid_signature_passes(self):
        """A freshly created signature should verify."""
        from app.rmos.runs_v2.signed_urls import (
            sign_attachment_request,
            verify_attachment_request,
        )

        sha256 = "a" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256
        expires = int(time.time()) + 300

        sig = sign_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            scope="download",
        )

        result = verify_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            sig=sig,
            scope="download",
        )

        assert result is True

    def test_expired_signature_fails(self):
        """An expired signature should not verify."""
        from app.rmos.runs_v2.signed_urls import (
            sign_attachment_request,
            verify_attachment_request,
        )

        sha256 = "b" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256
        # Expired 10 seconds ago
        expires = int(time.time()) - 10

        sig = sign_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            scope="download",
        )

        result = verify_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            sig=sig,
            scope="download",
        )

        assert result is False

    def test_wrong_signature_fails(self):
        """A tampered signature should not verify."""
        from app.rmos.runs_v2.signed_urls import verify_attachment_request

        sha256 = "c" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256
        expires = int(time.time()) + 300

        result = verify_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            sig="invalid-signature-xxx",
            scope="download",
        )

        assert result is False

    def test_scope_hierarchy_download_implies_head(self):
        """A download-scoped token should work for HEAD requests."""
        from app.rmos.runs_v2.signed_urls import (
            sign_attachment_request,
            verify_attachment_request,
        )

        sha256 = "d" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256
        expires = int(time.time()) + 300

        # Sign with download scope
        sig = sign_attachment_request(
            method="HEAD",
            path=path,
            sha256=sha256,
            expires=expires,
            scope="download",
        )

        # Verify with required_scope=head (should pass due to hierarchy)
        result = verify_attachment_request(
            method="HEAD",
            path=path,
            sha256=sha256,
            expires=expires,
            sig=sig,
            scope="download",
            required_scope="head",
        )

        assert result is True

    def test_scope_hierarchy_head_cannot_download(self):
        """A head-scoped token should NOT work for download requests."""
        from app.rmos.runs_v2.signed_urls import (
            sign_attachment_request,
            verify_attachment_request,
        )

        sha256 = "e" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256
        expires = int(time.time()) + 300

        # Sign with head scope
        sig = sign_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            scope="head",
        )

        # Verify with required_scope=download (should fail)
        result = verify_attachment_request(
            method="GET",
            path=path,
            sha256=sha256,
            expires=expires,
            sig=sig,
            scope="head",
            required_scope="download",
        )

        assert result is False

    def test_make_signed_query_includes_scope(self):
        """make_signed_query should include scope in returned params."""
        from app.rmos.runs_v2.signed_urls import make_signed_query

        sha256 = "f" * 64
        path = "/api/rmos/acoustics/attachments/" + sha256

        params = make_signed_query(
            method="GET",
            path=path,
            sha256=sha256,
            scope="head",
            ttl_seconds=300,
        )

        assert params.scope == "head"
        assert params.expires > int(time.time())
        assert params.sig is not None


# =============================================================================
# Test 3: Index Rebuild
# =============================================================================


class TestIndexRebuild:
    """
    Test _attachment_meta.json rebuild from run artifacts.
    """

    def test_rebuild_creates_index_from_artifacts(self, tmp_path):
        """rebuild_from_run_artifacts should scan runs and create index."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        # Create a date partition with a run artifact
        date_dir = tmp_path / "2025-12-31"
        date_dir.mkdir()

        run_artifact = {
            "run_id": "test-run-001",
            "created_at_utc": "2025-12-31T12:00:00Z",
            "attachments": [
                {
                    "sha256": "a" * 64,
                    "kind": "manifest",
                    "mime": "application/json",
                    "filename": "manifest.json",
                    "size_bytes": 1234,
                    "created_at_utc": "2025-12-31T12:00:00Z",
                },
                {
                    "sha256": "b" * 64,
                    "kind": "audio",
                    "mime": "audio/wav",
                    "filename": "recording.wav",
                    "size_bytes": 56789,
                    "created_at_utc": "2025-12-31T12:00:01Z",
                },
            ],
        }

        (date_dir / "test-run-001.json").write_text(
            json.dumps(run_artifact), encoding="utf-8"
        )

        # Run rebuild
        idx = AttachmentMetaIndex(tmp_path)
        stats = idx.rebuild_from_run_artifacts()

        assert stats["runs_scanned"] == 1
        assert stats["attachments_indexed"] == 2
        assert stats["unique_sha256"] == 2

        # Verify index was created
        assert idx.path.exists()

        # Verify entries
        meta_a = idx.get("a" * 64)
        assert meta_a is not None
        assert meta_a["kind"] == "manifest"
        assert meta_a["filename"] == "manifest.json"

        meta_b = idx.get("b" * 64)
        assert meta_b is not None
        assert meta_b["kind"] == "audio"

    def test_rebuild_handles_duplicate_sha256(self, tmp_path):
        """Same sha256 in multiple runs should increment ref_count."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        # Create two date partitions with runs sharing an attachment
        for date, run_id in [("2025-12-30", "run-001"), ("2025-12-31", "run-002")]:
            date_dir = tmp_path / date
            date_dir.mkdir(exist_ok=True)

            run_artifact = {
                "run_id": run_id,
                "created_at_utc": f"{date}T12:00:00Z",
                "attachments": [
                    {
                        "sha256": "shared" + "0" * 58,
                        "kind": "shared-asset",
                        "mime": "application/octet-stream",
                        "filename": "shared.bin",
                        "size_bytes": 100,
                        "created_at_utc": f"{date}T12:00:00Z",
                    },
                ],
            }

            (date_dir / f"{run_id}.json").write_text(
                json.dumps(run_artifact), encoding="utf-8"
            )

        idx = AttachmentMetaIndex(tmp_path)
        stats = idx.rebuild_from_run_artifacts()

        assert stats["runs_scanned"] == 2
        assert stats["attachments_indexed"] == 2
        assert stats["unique_sha256"] == 1

        meta = idx.get("shared" + "0" * 58)
        assert meta is not None
        assert meta["ref_count"] == 2
        assert meta["first_seen_run_id"] == "run-001"
        assert meta["last_seen_run_id"] == "run-002"


# =============================================================================
# Test 4: Blob-Exists Truth Table
# =============================================================================


class TestBlobExistsTruthTable:
    """
    Test all combinations of (in_index, blob_exists).

    Truth table:
    | in_index | blob_exists | Expected behavior |
    |----------|-------------|-------------------|
    | True     | True        | Healthy state     |
    | True     | False       | Orphaned index    |
    | False    | True        | Unindexed blob    |
    | False    | False       | Not found         |
    """

    def test_in_index_true_blob_exists_true(self, tmp_path):
        """Both index and blob exist - healthy state."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        sha256 = "healthy" + "0" * 57

        # Create index entry
        idx = AttachmentMetaIndex(tmp_path)
        idx.write({
            sha256: {
                "sha256": sha256,
                "kind": "test",
                "mime": "application/octet-stream",
                "filename": "test.bin",
                "size_bytes": 100,
            }
        })

        # Create blob
        blob_dir = tmp_path / sha256[:2] / sha256[2:4]
        blob_dir.mkdir(parents=True)
        (blob_dir / sha256).write_bytes(b"x" * 100)

        # Verify
        meta = idx.get(sha256)
        assert meta is not None
        assert (blob_dir / sha256).exists()

    def test_in_index_true_blob_exists_false(self, tmp_path):
        """Index entry exists but blob missing - orphaned index."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        sha256 = "orphaned" + "0" * 56

        # Create index entry only
        idx = AttachmentMetaIndex(tmp_path)
        idx.write({
            sha256: {
                "sha256": sha256,
                "kind": "test",
                "mime": "application/octet-stream",
                "filename": "test.bin",
                "size_bytes": 100,
            }
        })

        # Verify index exists
        meta = idx.get(sha256)
        assert meta is not None

        # Blob should not exist
        blob_path = tmp_path / sha256[:2] / sha256[2:4] / sha256
        assert not blob_path.exists()

    def test_in_index_false_blob_exists_true(self, tmp_path):
        """Blob exists but not in index - unindexed blob."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        sha256 = "unindexed" + "0" * 55

        # Create blob only
        blob_dir = tmp_path / sha256[:2] / sha256[2:4]
        blob_dir.mkdir(parents=True)
        (blob_dir / sha256).write_bytes(b"y" * 50)

        # Empty index
        idx = AttachmentMetaIndex(tmp_path)
        idx.write({})

        # Verify blob exists
        assert (blob_dir / sha256).exists()

        # Index should not have entry
        meta = idx.get(sha256)
        assert meta is None

    def test_in_index_false_blob_exists_false(self, tmp_path):
        """Neither index nor blob exist - not found."""
        from app.rmos.runs_v2.attachment_meta import AttachmentMetaIndex

        sha256 = "notfound" + "0" * 56

        # Empty index
        idx = AttachmentMetaIndex(tmp_path)
        idx.write({})

        # Verify neither exists
        meta = idx.get(sha256)
        assert meta is None

        blob_path = tmp_path / sha256[:2] / sha256[2:4] / sha256
        assert not blob_path.exists()


# =============================================================================
# Integration: Incremental Index Update on Import
# =============================================================================


class TestIncrementalIndexUpdate:
    """
    Test that persist_import_plan updates _attachment_meta.json.
    """

    def test_persist_import_updates_meta_index(self, tmp_path, monkeypatch):
        """persist_import_plan should call _update_attachment_meta_index."""
        # This is a unit test that verifies the hook was added
        # We don't run the full import, just verify the function exists and is called

        from app.rmos.acoustics import persist_glue

        # Verify the function exists
        assert hasattr(persist_glue, "_update_attachment_meta_index")

        # Verify it's called in persist_import_plan by checking the source
        import inspect
        source = inspect.getsource(persist_glue.persist_import_plan)
        assert "_update_attachment_meta_index" in source, \
            "persist_import_plan should call _update_attachment_meta_index"
