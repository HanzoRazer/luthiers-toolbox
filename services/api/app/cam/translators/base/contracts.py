"""
MRP-4A: Translator Contracts

Core protocol definitions and result types for the translator abstraction layer.

All governed translators implement ExportTranslator protocol.
BaseTranslator provides common implementation with governance enforcement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel

from app.export.body_export_bridge import BodyExportObject
from app.cam.export_object import ExportObject


ExportObjectType = Union[BodyExportObject, ExportObject]


class TranslatorErrorCode(str, Enum):
    """Standard translator error codes."""
    GATE_RED = "gate_red"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_ENTITY = "unsupported_entity"
    UNSUPPORTED_TARGET = "unsupported_target"
    UNSUPPORTED_VERSION = "unsupported_version"
    SERIALIZATION_FAILED = "serialization_failed"
    GOVERNANCE_VIOLATION = "governance_violation"
    TRANSLATOR_NOT_FOUND = "translator_not_found"


@dataclass
class TranslatorError:
    """Structured error from translator."""
    code: TranslatorErrorCode
    message: str
    entity_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslatorProvenance:
    """Provenance metadata embedded in output."""
    export_id: str
    translator_id: str
    translator_version: str
    translated_at: str
    target_format: str
    source_hash: Optional[str] = None
    ibg_session_id: Optional[str] = None
    instrument_spec: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "export_id": self.export_id,
            "translator_id": self.translator_id,
            "translator_version": self.translator_version,
            "translated_at": self.translated_at,
            "target_format": self.target_format,
            "source_hash": self.source_hash,
            "ibg_session_id": self.ibg_session_id,
            "instrument_spec": self.instrument_spec,
        }


class TranslatorOptions(BaseModel):
    """Options for translation request."""
    version: Optional[str] = None
    embed_provenance: bool = True
    close_contours: bool = True
    coordinate_precision: int = 3

    class Config:
        extra = "allow"


@dataclass
class TranslatorResult:
    """Result of translator execution."""
    success: bool
    output_format: str
    output_bytes: Optional[bytes] = None
    errors: List[TranslatorError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provenance: Optional[TranslatorProvenance] = None
    statistics: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_output(self) -> bool:
        return self.output_bytes is not None and len(self.output_bytes) > 0

    def content_hash(self) -> Optional[str]:
        """Compute hash of output content for determinism verification."""
        if not self.has_output:
            return None
        import hashlib
        return hashlib.sha256(self.output_bytes).hexdigest()


@runtime_checkable
class ExportTranslator(Protocol):
    """
    Protocol for governed translators.

    All translators must implement this protocol to participate in
    the governed translation layer.

    Key invariants:
      - Translators consume semantics, they do not create semantics
      - Translators are stateless
      - Translators cannot mutate the input Export Object
      - Output is deterministic given the same input (excluding timestamps)
    """

    @property
    def translator_id(self) -> str:
        """Unique translator identifier (matches capability registry)."""
        ...

    @property
    def translator_version(self) -> str:
        """Semantic version of translator."""
        ...

    @property
    def target_format(self) -> str:
        """Target format identifier (e.g., 'dxf', 'svg', 'step')."""
        ...

    def can_translate(
        self,
        export_object: ExportObjectType,
    ) -> bool:
        """Check if translator can handle this export object."""
        ...

    def translate(
        self,
        export_object: ExportObjectType,
        options: Optional[TranslatorOptions] = None,
    ) -> TranslatorResult:
        """
        Translate export object to target format.

        Args:
            export_object: Valid Export Object (gate green or yellow)
            options: Translation options

        Returns:
            TranslatorResult with output bytes or errors
        """
        ...


class BaseTranslator(ABC):
    """
    Abstract base class for translators.

    Provides common functionality and enforces governance:
      - Gate status checking
      - Provenance building
      - Error handling wrapper

    Subclasses implement _do_translate() for format-specific logic.
    """

    def __init__(
        self,
        translator_id: str,
        translator_version: str,
        target_format: str = None,
        output_format: str = None,  # MRP-3A backward compatibility
    ):
        self._translator_id = translator_id
        self._translator_version = translator_version
        # Accept either target_format (MRP-4A) or output_format (MRP-3A)
        self._target_format = target_format or output_format or "unknown"

    @property
    def translator_id(self) -> str:
        return self._translator_id

    @property
    def translator_version(self) -> str:
        return self._translator_version

    @property
    def target_format(self) -> str:
        return self._target_format

    @property
    def output_format(self) -> str:
        """Backward compatibility alias for target_format."""
        return self._target_format

    def _check_gate(
        self,
        export_object: ExportObjectType,
    ) -> Optional[TranslatorError]:
        """Check that gate allows translation."""
        gate_status = export_object.validation.gate_status
        if gate_status == "red":
            return TranslatorError(
                code=TranslatorErrorCode.GATE_RED,
                message="Export Object gate is red - translation blocked",
                details={
                    "gate_status": gate_status,
                    "issues": export_object.validation.issues,
                },
            )
        return None

    def _build_provenance(
        self,
        export_object: ExportObjectType,
    ) -> TranslatorProvenance:
        """Build provenance metadata for output."""
        source_hash = None
        ibg_session_id = None
        instrument_spec = None

        if hasattr(export_object.validation, "source_preview_hash"):
            source_hash = export_object.validation.source_preview_hash

        if hasattr(export_object, "extensions") and export_object.extensions:
            if hasattr(export_object.extensions, "ibg_morphology"):
                ibg = export_object.extensions.ibg_morphology
                if ibg:
                    ibg_session_id = ibg.session_id
                    instrument_spec = ibg.instrument_spec

        return TranslatorProvenance(
            export_id=export_object.export_id,
            translator_id=self._translator_id,
            translator_version=self._translator_version,
            translated_at=datetime.now(timezone.utc).isoformat(),
            target_format=self._target_format,
            source_hash=source_hash,
            ibg_session_id=ibg_session_id,
            instrument_spec=instrument_spec,
        )

    @abstractmethod
    def can_translate(
        self,
        export_object: ExportObjectType,
    ) -> bool:
        """Check if translator can handle this export object."""
        ...

    @abstractmethod
    def _do_translate(
        self,
        export_object: ExportObjectType,
        options: Optional[TranslatorOptions] = None,
    ) -> TranslatorResult:
        """Implementation-specific translation logic."""
        ...

    def translate(
        self,
        export_object: ExportObjectType,
        options: Optional[TranslatorOptions] = None,
    ) -> TranslatorResult:
        """
        Translate export object with governance checks.

        Subclasses should override _do_translate, not this method.
        """
        gate_error = self._check_gate(export_object)
        if gate_error:
            return TranslatorResult(
                success=False,
                output_format=self._target_format,
                errors=[gate_error],
            )

        if not self.can_translate(export_object):
            return TranslatorResult(
                success=False,
                output_format=self._target_format,
                errors=[
                    TranslatorError(
                        code=TranslatorErrorCode.INVALID_INPUT,
                        message="Translator cannot handle this export object type",
                        details={"export_type": export_object.export_type},
                    )
                ],
            )

        return self._do_translate(export_object, options)
