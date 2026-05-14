# Translator Onboarding Rules

**Date:** 2026-05-14  
**Sprint:** MRP-4B  
**Status:** ACTIVE

---

## Purpose

Defines the process for adding new translators to the governed translator architecture (MRP-4A).

---

## Prerequisites

Before creating a new translator:

1. **Export Object exists** — The canonical Export Object schema must support the entity type
2. **Target format identified** — DXF, SVG, STEP, PDF, or new format
3. **No existing translator** — Check registry for existing translator serving same purpose
4. **Governance approval** — For new target formats, governance review required

---

## Step 1: Create Translator Module

Create package structure:

```
app/cam/translators/{target}/
├── __init__.py          # Package exports
└── translator.py        # Translator implementation
```

### Implementation Template

```python
"""
{EntityType} {Target} Translator

Converts {EntityType} Export Objects to {Target} format.
"""
from dataclasses import dataclass
from typing import Optional

from app.cam.translators.base import (
    BaseTranslator,
    TranslatorResult,
    TranslatorOptions,
)


@dataclass
class {EntityType}{Target}TranslatorOptions:
    """Options for {EntityType} {Target} translation."""
    embed_provenance: bool = True
    coordinate_precision: int = 3
    # Add format-specific options


class {EntityType}{Target}Translator(BaseTranslator):
    """
    Translator: {EntityType} Export Object → {Target} format
    
    Execution state: governed_execution
    Target format: {target}
    Target version: {version}
    """
    
    def __init__(self):
        super().__init__(
            translator_id="{entity_type}_{target}_{version}",
            translator_version="1.0.0",
            target_format="{target}",
        )
    
    def translate(
        self,
        export_object,
        options: Optional[{EntityType}{Target}TranslatorOptions] = None,
    ) -> TranslatorResult:
        """
        Translate Export Object to {Target} format.
        
        Args:
            export_object: Canonical {EntityType}ExportObject
            options: Translation options (optional)
        
        Returns:
            TranslatorResult with artifact bytes and metadata
        
        Raises:
            TranslatorError: If translation fails or gate is RED
        """
        options = options or {EntityType}{Target}TranslatorOptions()
        
        # 1. Validate export object
        if not self._validate_export_object(export_object):
            return self._error_result("VALIDATION_FAILED", "...")
        
        # 2. Check gate status
        gate = getattr(export_object, "gate", None)
        if gate == "red":
            return self._error_result("GATE_RED", "Export blocked by red gate")
        
        # 3. Generate artifact
        artifact = self._generate_artifact(export_object, options)
        
        # 4. Build provenance
        provenance = self._build_provenance(export_object) if options.embed_provenance else None
        
        # 5. Return result
        return TranslatorResult(
            success=True,
            artifact=artifact,
            content_type="{content_type}",
            export_id=export_object.export_id,
            translator_id=self.translator_id,
            provenance=provenance,
        )
    
    def _validate_export_object(self, export_object) -> bool:
        # Implement validation logic
        return True
    
    def _generate_artifact(self, export_object, options) -> bytes:
        # Implement serialization logic
        raise NotImplementedError
    
    def _build_provenance(self, export_object) -> dict:
        return {
            "export_id": export_object.export_id,
            "translator_id": self.translator_id,
            "translator_version": self.translator_version,
            "translated_at": datetime.utcnow().isoformat() + "Z",
        }
```

---

## Step 2: Define Capabilities

Create capabilities dataclass in translator module:

```python
from app.cam.translators.base import (
    TranslatorCapabilities,
    TranslatorCategory,
    ExecutionState,
)

{ENTITY_TYPE}_{TARGET}_CAPABILITIES = TranslatorCapabilities(
    translator_id="{entity_type}_{target}_{version}",
    category=TranslatorCategory.SERIALIZATION,  # or VISUALIZATION
    execution_state=ExecutionState.GOVERNED_EXECUTION,
    target_format="{target}",
    target_version="{version}",
    supports_provenance=True,
    deterministic=True,
    description="{EntityType} to {Target} translator",
)
```

---

## Step 3: Register with Registry

In `app/cam/translators/base/registry.py`, add registration in `_initialize_default_translators()`:

```python
def _initialize_default_translators(self) -> None:
    # ... existing registrations ...
    
    # {EntityType} {Target} translator
    from app.cam.translators.{target}.translator import (
        {EntityType}{Target}Translator,
        {ENTITY_TYPE}_{TARGET}_CAPABILITIES,
    )
    self.register(
        {EntityType}{Target}Translator,
        {ENTITY_TYPE}_{TARGET}_CAPABILITIES,
    )
```

---

## Step 4: Add Target Mapping

In `app/cam/translators/base/negotiation.py`, add target mapping:

```python
TARGET_TRANSLATOR_MAP: Dict[str, Dict[str, str]] = {
    # ... existing mappings ...
    
    "{target}": {
        "default": "{entity_type}_{target}_{version}",
        "{version}": "{entity_type}_{target}_{version}",
    },
}
```

---

## Step 5: Update Package Exports

In `app/cam/translators/{target}/__init__.py`:

```python
"""
{Target} Translators Package
"""
from .translator import (
    {EntityType}{Target}Translator,
    {EntityType}{Target}TranslatorOptions,
    {ENTITY_TYPE}_{TARGET}_CAPABILITIES,
)

__all__ = [
    "{EntityType}{Target}Translator",
    "{EntityType}{Target}TranslatorOptions",
    "{ENTITY_TYPE}_{TARGET}_CAPABILITIES",
]
```

---

## Step 6: Write Tests

Create test file `tests/translators/test_{target}_translator.py`:

```python
"""Tests for {EntityType} {Target} translator."""
import pytest

from app.cam.translators.{target} import {EntityType}{Target}Translator
from app.cam.translators import get_translator_registry


def test_translator_registered():
    """Translator appears in registry."""
    registry = get_translator_registry()
    assert "{entity_type}_{target}_{version}" in registry.list_all()


def test_translator_capabilities():
    """Translator has correct capabilities."""
    registry = get_translator_registry()
    cap = registry.get_capabilities("{entity_type}_{target}_{version}")
    assert cap.execution_state.value == "governed_execution"
    assert cap.target_format == "{target}"


def test_translate_green_gate():
    """Translator produces valid output for green gate export."""
    translator = {EntityType}{Target}Translator()
    export_object = _make_test_export_object(gate="green")
    result = translator.translate(export_object)
    assert result.success
    assert result.artifact is not None


def test_translate_red_gate_blocked():
    """Translator rejects red gate exports."""
    translator = {EntityType}{Target}Translator()
    export_object = _make_test_export_object(gate="red")
    result = translator.translate(export_object)
    assert not result.success
    assert "GATE_RED" in result.error_code


def test_deterministic_output():
    """Same input produces same output (sans timestamp)."""
    translator = {EntityType}{Target}Translator()
    export_object = _make_test_export_object(gate="green")
    options = {EntityType}{Target}TranslatorOptions(embed_provenance=False)
    
    result1 = translator.translate(export_object, options)
    result2 = translator.translate(export_object, options)
    
    assert result1.artifact == result2.artifact
```

---

## Step 7: Update Documentation

### Update Capability Matrix

In `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md`:

```markdown
| {entity_type}_{target}_{version} | {target} | {Version} | governed | yes | yes |
```

### Update Migration Matrix

In `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md`:

```markdown
| `app.cam.translators.{target}.translator` | `translate()` | {Target} | **GOVERNED** | MRP-4A |
```

---

## Step 8: API Endpoint (Optional)

If the translator needs a dedicated API endpoint beyond `/api/translate/{target}`:

```python
# app/routers/export/{target}_router.py

from fastapi import APIRouter
from app.cam.translators import resolve_translator

router = APIRouter(tags=["Export", "{Target}"])

@router.post("/{target}")
def export_to_{target}(export_object: ExportObjectModel):
    translator = resolve_translator("{target}")
    result = translator.translate(export_object)
    # ... handle result ...
```

---

## Checklist

Before submitting PR:

- [ ] Translator implements `ExportTranslator` protocol
- [ ] Capabilities declared with `ExecutionState.GOVERNED_EXECUTION`
- [ ] Registered in `TranslatorRegistry`
- [ ] Target mapping added to `negotiation.py`
- [ ] Gate enforcement implemented (red gate = error)
- [ ] Deterministic output (sans timestamp) verified
- [ ] Provenance embedding implemented
- [ ] Tests written and passing
- [ ] Capability matrix updated
- [ ] Migration matrix updated

---

## References

- `docs/governance/TRANSLATOR_LAYER_RULES.md` — core rules
- `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md` — target policy
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md` — architecture
- `app/cam/translators/dxf/` — reference implementation
