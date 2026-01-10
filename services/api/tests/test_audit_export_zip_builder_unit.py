from __future__ import annotations

import io
import json
import zipfile

from app.rmos.runs_v2.audit_export import AuditExportPorts, build_batch_audit_zip


class _FakePorts:
    def __init__(self, artifacts, attachments):
        self._arts = {a["id"]: a for a in artifacts}
        self._attachments = attachments  # {artifact_id: [{"id":..., "name":..., "bytes":...}]}

    def list_runs_filtered(self, **kwargs):
        sid = kwargs.get("session_id")
        bl = kwargs.get("batch_label")
        tool_kind = kwargs.get("tool_kind")
        out = []
        for a in self._arts.values():
            meta = a.get("index_meta", {})
            if sid and meta.get("session_id") != sid:
                continue
            if bl and meta.get("batch_label") != bl:
                continue
            if tool_kind and meta.get("tool_kind") != tool_kind:
                continue
            out.append(a)
        return {"items": out}

    def get_run(self, artifact_id: str):
        return self._arts.get(artifact_id)

    def list_attachments(self, artifact_id: str):
        return [{"id": x["id"], "name": x["name"]} for x in self._attachments.get(artifact_id, [])]

    def get_attachment_bytes(self, artifact_id: str, att_key: str) -> bytes:
        for x in self._attachments.get(artifact_id, []):
            if x["id"] == att_key or x["name"] == att_key:
                return x["bytes"]
        raise KeyError(att_key)


def test_build_batch_audit_zip_writes_manifest_and_artifacts_and_attachments():
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}, "payload": {"tool_id": "saw:thin_140", "items": [{"material_id": "maple"}]}},
        {"id": "plan1", "kind": "saw_batch_plan", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw", "parent_batch_spec_artifact_id": "spec1"}, "payload": {"batch_spec_artifact_id": "spec1"}},
    ]
    attachments = {"plan1": [{"id": "att1", "name": "toolpaths.gcode", "bytes": b"G0 X0 Y0\n"}]}
    ports = _FakePorts(artifacts, attachments)
    zip_bytes, manifest = build_batch_audit_zip(
        AuditExportPorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
            list_attachments=ports.list_attachments,
            get_attachment_bytes=ports.get_attachment_bytes,
        ),
        session_id="s1",
        batch_label="b1",
        tool_kind="saw",
        include_attachments=True,
    )
    assert manifest["root_artifact_id"] == "spec1"

    z = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    names = set(z.namelist())
    assert "manifest.json" in names
    assert any(n.startswith("artifacts/") for n in names)
    assert "attachments/plan1/toolpaths.gcode" in names

    m = json.loads(z.read("manifest.json").decode("utf-8"))
    assert m["session_id"] == "s1"
    assert m["batch_label"] == "b1"


def test_build_batch_audit_zip_without_attachments():
    """Test that include_attachments=False skips attachment writing."""
    artifacts = [
        {"id": "spec1", "kind": "saw_batch_spec", "index_meta": {"session_id": "s1", "batch_label": "b1", "tool_kind": "saw"}},
    ]
    attachments = {"spec1": [{"id": "att1", "name": "data.bin", "bytes": b"binary data"}]}
    ports = _FakePorts(artifacts, attachments)
    zip_bytes, manifest = build_batch_audit_zip(
        AuditExportPorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
            list_attachments=ports.list_attachments,
            get_attachment_bytes=ports.get_attachment_bytes,
        ),
        session_id="s1",
        batch_label="b1",
        include_attachments=False,
    )

    z = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    names = set(z.namelist())
    assert "manifest.json" in names
    # No attachments folder
    assert not any(n.startswith("attachments/") for n in names)


def test_build_batch_audit_zip_empty_batch():
    """Test that empty batch produces valid ZIP with empty manifest."""
    ports = _FakePorts([], {})
    zip_bytes, manifest = build_batch_audit_zip(
        AuditExportPorts(
            list_runs_filtered=ports.list_runs_filtered,
            get_run=ports.get_run,
            list_attachments=ports.list_attachments,
            get_attachment_bytes=ports.get_attachment_bytes,
        ),
        session_id="s1",
        batch_label="b1",
    )

    assert manifest["root_artifact_id"] is None
    assert manifest["node_count"] == 0

    z = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    assert "manifest.json" in z.namelist()
