"""
Acoustic STEP Translator.

Sprint: MRP-5J
Status: PROTOTYPE

Serializes validated acoustic topology to STEP Part 21 format.

Key Boundaries:
    - Accepts ONLY CertifiedTopology (not raw topology)
    - Does NOT build topology (topology_builder does that)
    - Does NOT validate (topology_validation does that)
    - Does NOT repair geometry
    - Does NOT infer missing semantics
    - Does NOT bypass validation

Output Classification:
    PROTOTYPE_SERIALIZATION (not PRODUCTION_CAD)

This translator produces syntactically valid STEP Part 21 text
with embedded provenance and validation metadata. It does NOT
produce production-grade B-rep geometry (no CAD kernel).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


@dataclass
class AcousticStepTranslationArtifact:
    """
    Translation artifact for acoustic STEP output.

    MRP-5J: Thin artifact that captures output content, provenance,
    and validation signature. Can later adapt to TranslationArtifact.
    """

    artifact_id: str
    target: str = "step"
    format_version: str = "STEP_PART21_PROTOTYPE"
    content: bytes = field(default=b"")
    maturity: str = "prototype"
    provenance: Dict[str, Any] = field(default_factory=dict)
    validation_signature: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def content_hash(self) -> str:
        """SHA256 hash of content for determinism verification."""
        return hashlib.sha256(self.content).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "target": self.target,
            "format_version": self.format_version,
            "content_length": len(self.content),
            "content_hash": self.content_hash,
            "maturity": self.maturity,
            "provenance": self.provenance,
            "validation_signature": self.validation_signature,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class AcousticStepTranslator:
    """
    Prototype STEP translator for acoustic topology.

    Accepts ONLY CertifiedTopology — refuses raw topology objects.
    Produces STEP Part 21 text with embedded provenance.

    This is a prototype serializer, NOT a production CAD exporter.
    """

    TRANSLATOR_ID = "step_acoustic_prototype"
    TRANSLATOR_VERSION = "0.1.0"
    TARGET_FORMAT = "step"
    OUTPUT_FORMAT_VERSION = "STEP_PART21_PROTOTYPE"

    def __init__(self):
        """Initialize the translator."""
        self._artifact_counter = 0

    def can_translate(self, obj: Any) -> bool:
        """
        Check if this translator can handle the object.

        Only accepts CertifiedTopology from topology_validation.
        """
        from app.cam.topology_validation import CertifiedTopology
        return isinstance(obj, CertifiedTopology)

    def translate(
        self,
        certified_topology: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> AcousticStepTranslationArtifact:
        """
        Translate certified topology to STEP Part 21 format.

        Args:
            certified_topology: CertifiedTopology from TopologyValidator.certify()
            options: Optional translation options

        Returns:
            AcousticStepTranslationArtifact with STEP content

        Raises:
            TypeError: If input is not CertifiedTopology
        """
        from app.cam.topology_validation import CertifiedTopology

        if not isinstance(certified_topology, CertifiedTopology):
            raise TypeError(
                f"AcousticStepTranslator accepts only CertifiedTopology, "
                f"not {type(certified_topology).__name__}. "
                f"Use TopologyValidator.certify() to obtain CertifiedTopology."
            )

        options = options or {}

        # Generate STEP content
        step_content = self._generate_step_content(certified_topology, options)

        # Build artifact
        self._artifact_counter += 1
        artifact_id = f"step_acoustic_{certified_topology.request_id}_{self._artifact_counter}"

        return AcousticStepTranslationArtifact(
            artifact_id=artifact_id,
            target=self.TARGET_FORMAT,
            format_version=self.OUTPUT_FORMAT_VERSION,
            content=step_content.encode("utf-8"),
            maturity="prototype",
            provenance=self._build_provenance(certified_topology),
            validation_signature=certified_topology.signature.to_dict(),
            metadata={
                "translator_id": self.TRANSLATOR_ID,
                "translator_version": self.TRANSLATOR_VERSION,
                "shell_count": len(certified_topology.shells),
                "tier": certified_topology.tier.value,
                "classification": "PROTOTYPE_SERIALIZATION",
            },
        )

    def _generate_step_content(
        self,
        certified_topology: Any,
        options: Dict[str, Any],
    ) -> str:
        """
        Generate STEP Part 21 content.

        This produces syntactically valid STEP text with:
        - Header section with provenance
        - Data section with shell descriptors
        - Embedded validation certificate

        NOTE: This is PROTOTYPE output. It does not contain
        production B-rep geometry (no ADVANCED_FACE, etc.).
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        request_id = certified_topology.request_id
        tier = certified_topology.tier.value
        signature = certified_topology.signature

        lines = []

        # ISO-10303-21 header
        lines.append("ISO-10303-21;")
        lines.append("HEADER;")
        lines.append("")

        # FILE_DESCRIPTION
        lines.append("FILE_DESCRIPTION(")
        lines.append(f"  ('PROTOTYPE_ACOUSTIC_STEP - MRP-5J',")
        lines.append(f"   'Acoustic topology serialization',")
        lines.append(f"   'NOT PRODUCTION B-REP'),")
        lines.append(f"  '2;1');")
        lines.append("")

        # FILE_NAME
        lines.append("FILE_NAME(")
        lines.append(f"  '{request_id}.step',")
        lines.append(f"  '{timestamp}',")
        lines.append(f"  ('Luthiers Toolbox'),")
        lines.append(f"  ('MRP-5J Acoustic Topology'),")
        lines.append(f"  'STEP_PART21_PROTOTYPE',")
        lines.append(f"  'AcousticStepTranslator {self.TRANSLATOR_VERSION}',")
        lines.append(f"  '');")
        lines.append("")

        # FILE_SCHEMA
        lines.append("FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));")
        lines.append("")
        lines.append("ENDSEC;")
        lines.append("")

        # DATA section
        lines.append("DATA;")
        lines.append("")

        # Validation certificate as comment block
        lines.append("/* VALIDATION CERTIFICATE")
        lines.append(f"   Request ID: {request_id}")
        lines.append(f"   Tier: {tier}")
        lines.append(f"   Validation Passed: {certified_topology.validation.passed}")
        lines.append(f"   Input Hash: {signature.input_hash}")
        lines.append(f"   Validation Hash: {signature.validation_hash}")
        lines.append(f"   Timestamp: {signature.timestamp_iso}")
        lines.append("*/")
        lines.append("")

        # Entity counter
        entity_id = 1

        # APPLICATION_CONTEXT
        lines.append(f"#{entity_id} = APPLICATION_CONTEXT(")
        lines.append(f"  'acoustic instrument topology');")
        app_context_id = entity_id
        entity_id += 1
        lines.append("")

        # APPLICATION_PROTOCOL_DEFINITION
        lines.append(f"#{entity_id} = APPLICATION_PROTOCOL_DEFINITION(")
        lines.append(f"  'acoustic_prototype',")
        lines.append(f"  'acoustic instrument body topology',")
        lines.append(f"  2026,")
        lines.append(f"  #{app_context_id});")
        entity_id += 1
        lines.append("")

        # PRODUCT for each shell
        shell_product_ids = []
        for shell in certified_topology.shells:
            shell_id = shell.get("shell_id", f"shell_{entity_id}")
            component = shell.get("component_name", "unknown")
            shell_type = shell.get("shell_type", "unknown")

            lines.append(f"/* Shell: {shell_id} ({component}) */")

            # PRODUCT
            lines.append(f"#{entity_id} = PRODUCT(")
            lines.append(f"  '{shell_id}',")
            lines.append(f"  '{component}',")
            lines.append(f"  'Shell type: {shell_type}',")
            lines.append(f"  ());")
            product_id = entity_id
            shell_product_ids.append(product_id)
            entity_id += 1

            # PRODUCT_DEFINITION_CONTEXT
            lines.append(f"#{entity_id} = PRODUCT_DEFINITION_CONTEXT(")
            lines.append(f"  'prototype',")
            lines.append(f"  #{app_context_id},")
            lines.append(f"  'acoustic_topology');")
            pdc_id = entity_id
            entity_id += 1

            # PRODUCT_DEFINITION
            lines.append(f"#{entity_id} = PRODUCT_DEFINITION(")
            lines.append(f"  '{shell_id}_def',")
            lines.append(f"  '',")
            lines.append(f"  #{product_id},")
            lines.append(f"  #{pdc_id});")
            entity_id += 1

            # Shell metadata as DESCRIPTIVE_REPRESENTATION_ITEM
            is_closed = shell.get("is_closed", False)
            is_manifold = shell.get("is_manifold", False)
            surface_count = shell.get("surface_count", 0)
            edge_count = shell.get("edge_count", 0)
            vertex_count = shell.get("vertex_count", 0)

            lines.append(f"#{entity_id} = DESCRIPTIVE_REPRESENTATION_ITEM(")
            lines.append(f"  'shell_metadata',")
            lines.append(f"  'is_closed={is_closed}; is_manifold={is_manifold}; "
                        f"F={surface_count}; E={edge_count}; V={vertex_count}');")
            entity_id += 1
            lines.append("")

        # Provenance metadata
        lines.append("/* PROVENANCE */")
        lines.append(f"#{entity_id} = DESCRIPTIVE_REPRESENTATION_ITEM(")
        lines.append(f"  'translator_provenance',")
        lines.append(f"  'translator_id={self.TRANSLATOR_ID}; "
                    f"version={self.TRANSLATOR_VERSION}; "
                    f"classification=PROTOTYPE_SERIALIZATION');")
        entity_id += 1
        lines.append("")

        # Close DATA section
        lines.append("ENDSEC;")
        lines.append("")
        lines.append("END-ISO-10303-21;")

        return "\n".join(lines)

    def _build_provenance(
        self,
        certified_topology: Any,
    ) -> Dict[str, Any]:
        """Build provenance dictionary."""
        return {
            "translator_id": self.TRANSLATOR_ID,
            "translator_version": self.TRANSLATOR_VERSION,
            "target_format": self.TARGET_FORMAT,
            "format_version": self.OUTPUT_FORMAT_VERSION,
            "request_id": certified_topology.request_id,
            "tier": certified_topology.tier.value,
            "translated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "PROTOTYPE_SERIALIZATION",
        }
