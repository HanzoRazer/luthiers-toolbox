"""LtbDesignSnapshotV1. Facts and opaque references only.

Schema id ``ltb_design_snapshot`` is not in an LTB naming registry that
requires a different value. ``InstrumentProjectData`` has a ``schema_version``
and no ``schema_id``; a missing source schema id stays null.
"""
from __future__ import annotations

import math
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping

from .errors import DesignSnapshotError
from .serialization import canonical_json, payload_digest, sha256_text

SCHEMA_ID = "ltb_design_snapshot"
SCHEMA_VERSION = "1.0"
JOB_SYSTEM = "CNC-Production-Shop"
UNVERIFIED_EXTERNAL_REFERENCE = "UNVERIFIED_EXTERNAL_REFERENCE"

_SNAPSHOT_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9_-])?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_RESERVED = frozenset({
    "aux", "clock$", "con", "nul", "prn",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})
_SECRET_KEYS = frozenset({
    "password", "secret", "token", "api_key", "authorization", "credential",
})
_NUMERIC_SUFFIXES = ("_mm", "_deg", "_degrees", "_lbs", "_pct")
_NUMERIC_KEYS = frozenset({
    "confidence", "symmetry_score", "interpretation_confidence",
    "fret_count", "string_count", "body_join_fret",
})
_ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)|\.\.(?:[/\\]|$)")


def _token(value: object, message: str, *, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DesignSnapshotError(message, code=code)
    if any(ord(ch) < 32 for ch in value):
        raise DesignSnapshotError(message, code=code)
    return value


def require_snapshot_id(value: object) -> str:
    if not isinstance(value, str) or _SNAPSHOT_ID.fullmatch(value) is None:
        raise DesignSnapshotError("design_snapshot_id is not filename-safe", code="SNAPSHOT_ID")
    if value.split(".", 1)[0] in _WINDOWS_RESERVED:
        raise DesignSnapshotError("design_snapshot_id is not filename-safe", code="SNAPSHOT_ID")
    return value


def require_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise DesignSnapshotError(f"{name} must be a lowercase sha256", code="MALFORMED_DIGEST")
    return value


def require_time(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise DesignSnapshotError(f"{name} must be timezone-aware", code="TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        raise DesignSnapshotError(f"{name} must be timezone-aware", code="TIMESTAMP") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DesignSnapshotError(f"{name} must be timezone-aware", code="TIMESTAMP")
    return value


def stamp(value: datetime, name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DesignSnapshotError(f"{name} must be timezone-aware", code="TIMESTAMP")
    return value.isoformat()


def new_design_snapshot_id() -> str:
    """Millisecond prefix plus the full ``uuid4().hex``. Not a global identity authority."""
    return f"dsn_{int(time.time() * 1000)}_{uuid.uuid4().hex}"


def _secret_key(key: str) -> bool:
    folded = key.casefold()
    if folded in _SECRET_KEYS:
        return True
    return any(folded.startswith(secret + "_") or folded.endswith("_" + secret) for secret in _SECRET_KEYS)


def _reject_string(value: str) -> None:
    if _ABSOLUTE_PATH.search(value):
        raise DesignSnapshotError("absolute or parent path", code="ABSOLUTE_PATH")


def _reject_number(key: str | None, value: object) -> None:
    numeric = key in _NUMERIC_KEYS or (key is not None and key.endswith(_NUMERIC_SUFFIXES))
    if isinstance(value, bool):
        if numeric:
            raise DesignSnapshotError("boolean is not a number", code="BOOLEAN_AS_NUMBER")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise DesignSnapshotError("non-finite number", code="NON_FINITE")


def _copy_json(value: object, key: str | None = None) -> object:
    _reject_number(key, value)
    if value is None or (isinstance(value, (str, int, float)) and not isinstance(value, bool)):
        if isinstance(value, str):
            _reject_string(value)
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return [_copy_json(item, key) for item in value]
    if isinstance(value, dict):
        return _copy_object(value)
    raise DesignSnapshotError("unsupported design value", code="UNSUPPORTED_VALUE")


def _copy_object(value: dict) -> dict[str, object]:
    copied: dict[str, object] = {}
    for raw_key, item in value.items():
        if not isinstance(raw_key, str) or not raw_key.strip() or raw_key != raw_key.strip():
            raise DesignSnapshotError("design payload key is required", code="PAYLOAD_KEY")
        if _secret_key(raw_key):
            raise DesignSnapshotError("design payload key is not portable", code="SECRET_KEY")
        copied[raw_key] = _copy_json(item, raw_key)
    return copied


def copy_design_payload(value: object) -> dict[str, object]:
    """Deep-copy a JSON object. Does not drop engineering fields."""
    if not isinstance(value, dict):
        raise DesignSnapshotError("design payload must be an object", code="PAYLOAD")
    return _copy_object(value)


def _optional_sha(value: object, name: str) -> str | None:
    if value is None:
        return None
    return require_sha256(value, name)


def _relative_hint(value: object) -> str | None:
    if value is None:
        return None
    text = _token(value, "source_path_hint must be a relative path", code="ABSOLUTE_PATH")
    _reject_string(text)
    if "\\" in text or text.startswith("/") or "://" in text:
        raise DesignSnapshotError("source_path_hint must be a relative path", code="ABSOLUTE_PATH")
    return text


@dataclass(frozen=True)
class ExternalJobReferenceV1:
    system: str
    job_id: str
    verification_status: str

    def __post_init__(self) -> None:
        if self.system != JOB_SYSTEM:
            raise DesignSnapshotError("job system must be CNC-Production-Shop", code="JOB_SYSTEM")
        _token(self.job_id, "job_id is required", code="JOB_ID")
        if self.verification_status != UNVERIFIED_EXTERNAL_REFERENCE:
            raise DesignSnapshotError(
                "job verification must be UNVERIFIED_EXTERNAL_REFERENCE",
                code="JOB_UNVERIFIED_ONLY",
            )


@dataclass(frozen=True)
class LtbProjectReferenceV1:
    project_id: str
    project_schema_id: str | None
    project_schema_version: str | None
    source_state_digest: str

    def __post_init__(self) -> None:
        _token(self.project_id, "project_id is required", code="PROJECT_ID")
        if self.project_schema_id is not None:
            _token(self.project_schema_id, "project_schema_id is required", code="PROJECT_SCHEMA")
        if self.project_schema_version is not None:
            _token(self.project_schema_version, "project_schema_version is required", code="PROJECT_SCHEMA")
        require_sha256(self.source_state_digest, "source_state_digest")


@dataclass(frozen=True)
class ActorReferenceV1:
    actor_id: str

    def __post_init__(self) -> None:
        _token(self.actor_id, "captured_by is required", code="ACTOR")


@dataclass(frozen=True)
class ArtifactReferenceV1:
    artifact_id: str
    artifact_kind: str
    content_digest: str
    media_type: str | None = None
    source_path_hint: str | None = None

    def __post_init__(self) -> None:
        _token(self.artifact_id, "artifact_id is required", code="ARTIFACT")
        _token(self.artifact_kind, "artifact_kind is required", code="ARTIFACT")
        require_sha256(self.content_digest, "content_digest")
        if self.media_type is not None:
            _token(self.media_type, "media_type is required", code="ARTIFACT")
        object.__setattr__(self, "source_path_hint", _relative_hint(self.source_path_hint))


@dataclass(frozen=True)
class GeneratorReferenceV1:
    generator_id: str
    generator_version: str
    input_digest: str | None = None
    output_digest: str | None = None

    def __post_init__(self) -> None:
        _token(self.generator_id, "generator_id is required", code="GENERATOR")
        _token(self.generator_version, "generator_version is required", code="GENERATOR")
        object.__setattr__(self, "input_digest", _optional_sha(self.input_digest, "input_digest"))
        object.__setattr__(self, "output_digest", _optional_sha(self.output_digest, "output_digest"))


def _unique(items: tuple, attr: str, code: str) -> None:
    seen = [getattr(item, attr) for item in items]
    if len(seen) != len(set(seen)):
        raise DesignSnapshotError(f"{attr} repeats", code=code)


@dataclass(frozen=True)
class LtbDesignSnapshotV1:
    schema_id: str
    schema_version: str
    design_snapshot_id: str
    external_job_ref: ExternalJobReferenceV1
    project_ref: LtbProjectReferenceV1
    captured_at: str
    captured_by: ActorReferenceV1
    design_payload: dict[str, object]
    design_payload_digest: str
    artifact_refs: tuple[ArtifactReferenceV1, ...]
    generator_refs: tuple[GeneratorReferenceV1, ...]
    snapshot_digest: str

    def __post_init__(self) -> None:
        if self.schema_id != SCHEMA_ID:
            raise DesignSnapshotError("schema identity is not the LTB design snapshot", code="SCHEMA")
        if self.schema_version != SCHEMA_VERSION:
            raise DesignSnapshotError("unsupported schema version", code="UNKNOWN_SCHEMA_VERSION")
        require_snapshot_id(self.design_snapshot_id)
        if not isinstance(self.external_job_ref, ExternalJobReferenceV1):
            raise DesignSnapshotError("external job reference is required", code="JOB_ID")
        if not isinstance(self.project_ref, LtbProjectReferenceV1):
            raise DesignSnapshotError("project reference is required", code="PROJECT_ID")
        require_time(self.captured_at, "captured_at")
        if not isinstance(self.captured_by, ActorReferenceV1):
            raise DesignSnapshotError("captured_by is required", code="ACTOR")
        if not isinstance(self.design_payload, dict):
            raise DesignSnapshotError("design payload must be an object", code="PAYLOAD")
        _require_payload_integrity(self)
        _unique(self.artifact_refs, "artifact_id", "ARTIFACT")
        _unique(self.generator_refs, "generator_id", "GENERATOR")


def _require_payload_integrity(record: LtbDesignSnapshotV1) -> None:
    """Re-check the stored payload. An absolute path or a bad digest fails closed."""
    copied = copy_design_payload(record.design_payload)
    digest = sha256_text(canonical_json(copied))
    if record.design_payload_digest != digest or record.project_ref.source_state_digest != digest:
        raise DesignSnapshotError("DIGEST_MISMATCH", code="DIGEST_MISMATCH")
    if payload_digest(snapshot_fields(record)) != record.snapshot_digest:
        raise DesignSnapshotError("DIGEST_MISMATCH", code="DIGEST_MISMATCH")


def artifact_fields(item: ArtifactReferenceV1) -> dict[str, object]:
    return {
        "artifact_id": item.artifact_id,
        "artifact_kind": item.artifact_kind,
        "content_digest": item.content_digest,
        "media_type": item.media_type,
        "source_path_hint": item.source_path_hint,
    }


def generator_fields(item: GeneratorReferenceV1) -> dict[str, object]:
    return {
        "generator_id": item.generator_id,
        "generator_version": item.generator_version,
        "input_digest": item.input_digest,
        "output_digest": item.output_digest,
    }


def snapshot_fields(record: LtbDesignSnapshotV1) -> dict[str, object]:
    """Canonical field map. ``snapshot_digest`` is present and excluded by the digest helper."""
    return {
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "design_snapshot_id": record.design_snapshot_id,
        "external_job_ref": {
            "system": record.external_job_ref.system,
            "job_id": record.external_job_ref.job_id,
            "verification_status": record.external_job_ref.verification_status,
        },
        "project_ref": {
            "project_id": record.project_ref.project_id,
            "project_schema_id": record.project_ref.project_schema_id,
            "project_schema_version": record.project_ref.project_schema_version,
            "source_state_digest": record.project_ref.source_state_digest,
        },
        "captured_at": record.captured_at,
        "captured_by": {"actor_id": record.captured_by.actor_id},
        "design_payload": record.design_payload,
        "design_payload_digest": record.design_payload_digest,
        "artifact_refs": [artifact_fields(item) for item in record.artifact_refs],
        "generator_refs": [generator_fields(item) for item in record.generator_refs],
        "snapshot_digest": record.snapshot_digest,
    }


def _schema_text(payload: Mapping[str, object], key: str) -> str | None:
    if key not in payload or payload[key] is None:
        return None
    return _token(payload[key], f"{key} is required", code="PROJECT_SCHEMA")


def make_design_snapshot(
    *,
    design_snapshot_id: str,
    job_id: str,
    project_id: str,
    design_payload: Mapping[str, object],
    captured_at: datetime,
    captured_by: str,
    artifact_refs: tuple[ArtifactReferenceV1, ...] = (),
    generator_refs: tuple[GeneratorReferenceV1, ...] = (),
) -> LtbDesignSnapshotV1:
    payload = copy_design_payload(design_payload)
    digest = sha256_text(canonical_json(payload))
    draft = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "design_snapshot_id": design_snapshot_id,
        "external_job_ref": ExternalJobReferenceV1(JOB_SYSTEM, job_id, UNVERIFIED_EXTERNAL_REFERENCE),
        "project_ref": LtbProjectReferenceV1(
            project_id, _schema_text(payload, "schema_id"), _schema_text(payload, "schema_version"), digest,
        ),
        "captured_at": stamp(captured_at, "captured_at"),
        "captured_by": ActorReferenceV1(captured_by),
        "design_payload": payload,
        "design_payload_digest": digest,
        "artifact_refs": tuple(artifact_refs),
        "generator_refs": tuple(generator_refs),
    }
    snapshot_digest = payload_digest({**snapshot_fields_from_parts(draft), "snapshot_digest": ""})
    return LtbDesignSnapshotV1(**draft, snapshot_digest=snapshot_digest)


def snapshot_fields_from_parts(draft: Mapping[str, object]) -> dict[str, object]:
    job = draft["external_job_ref"]
    project = draft["project_ref"]
    actor = draft["captured_by"]
    if not isinstance(job, ExternalJobReferenceV1):
        raise DesignSnapshotError("external job reference is required", code="JOB_ID")
    if not isinstance(project, LtbProjectReferenceV1):
        raise DesignSnapshotError("project reference is required", code="PROJECT_ID")
    if not isinstance(actor, ActorReferenceV1):
        raise DesignSnapshotError("captured_by is required", code="ACTOR")
    return {
        "schema_id": draft["schema_id"],
        "schema_version": draft["schema_version"],
        "design_snapshot_id": draft["design_snapshot_id"],
        "external_job_ref": {
            "system": job.system, "job_id": job.job_id, "verification_status": job.verification_status,
        },
        "project_ref": {
            "project_id": project.project_id,
            "project_schema_id": project.project_schema_id,
            "project_schema_version": project.project_schema_version,
            "source_state_digest": project.source_state_digest,
        },
        "captured_at": draft["captured_at"],
        "captured_by": {"actor_id": actor.actor_id},
        "design_payload": draft["design_payload"],
        "design_payload_digest": draft["design_payload_digest"],
        "artifact_refs": [artifact_fields(item) for item in draft["artifact_refs"]],
        "generator_refs": [generator_fields(item) for item in draft["generator_refs"]],
        "snapshot_digest": "",
    }
