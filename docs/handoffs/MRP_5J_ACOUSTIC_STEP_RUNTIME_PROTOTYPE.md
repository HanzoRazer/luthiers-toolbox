# MRP Dev Order 5J — Acoustic STEP Runtime Prototype Handoff

**Date:** 2026-05-19  
**Dev Order:** MRP-5J  
**Status:** COMPLETE

---

## Summary

MRP-5J implemented the Acoustic STEP Runtime prototype, enforcing the boundary between validated topology and translator serialization:

1. **CertifiedTopology** — Wrapper that can only be created when validation passes
2. **TopologyValidator.certify()** — Returns CertifiedTopology only on passing validation
3. **AcousticStepTranslator** — Accepts ONLY CertifiedTopology, refuses raw objects
4. **STEP Part 21 Output** — Syntactically valid prototype STEP with provenance
5. **Capability Registration** — step_acoustic_prototype in translator registry

**Sprint Type:** Prototype serializer (no CAD kernel)

---

## Architecture Rationale

The key boundary enforced:

```
TopologyValidator.validate() → ValidationResult
TopologyValidator.certify()  → CertifiedTopology (only if passes)
                                    ↓
AcousticStepTranslator       → accepts CertifiedTopology
                             → refuses raw PrototypeTopologyObject
```

This makes the contract **executable** instead of merely documented.

The translator:
- Does NOT build topology (topology_builder does that)
- Does NOT validate (topology_validation does that)
- Does NOT repair geometry
- Does NOT infer missing semantics
- Does NOT bypass validation

---

## Deliverables

### 1. CertifiedTopology (topology_validation)

**Location:** `app/cam/topology_validation/contracts.py`

```python
class CertifiedTopology:
    """Can only be instantiated by TopologyValidator.certify()"""

    def __init__(self) -> None:
        raise TypeError(
            "CertifiedTopology cannot be instantiated directly. "
            "Use TopologyValidator.certify() instead."
        )

    @classmethod
    def _create(cls, topology_dict, validation, signature):
        """Private factory for TopologyValidator only"""
        if not validation.passed:
            raise ValueError("Cannot certify topology that failed validation")
        ...
```

### 2. TopologyValidator.certify()

**Location:** `app/cam/topology_validation/validators.py`

```python
def certify(
    self,
    topology_dict: Dict[str, Any],
    continuity_targets: Optional[Dict[str, str]] = None,
) -> CertifiedTopology:
    """
    Validate and certify topology for translator consumption.
    Returns CertifiedTopology only if validation passes.
    Raises ValidationError if validation fails.
    """
    result = self.validate_topology_object(topology_dict, continuity_targets)

    if not result.passed:
        raise ValidationError(
            message="Cannot certify topology: validation failed",
            classification="CERTIFICATION_DENIED",
            ...
        )

    return CertifiedTopology._create(
        topology_dict=topology_dict,
        validation=result,
        signature=result.signature,
    )
```

### 3. AcousticStepTranslator

**Location:** `app/cam/translators/step/acoustic.py`

```python
class AcousticStepTranslator:
    TRANSLATOR_ID = "step_acoustic_prototype"
    TRANSLATOR_VERSION = "0.1.0"

    def can_translate(self, obj: Any) -> bool:
        from app.cam.topology_validation import CertifiedTopology
        return isinstance(obj, CertifiedTopology)

    def translate(
        self,
        certified_topology: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> AcousticStepTranslationArtifact:
        if not isinstance(certified_topology, CertifiedTopology):
            raise TypeError("Accepts only CertifiedTopology")
        ...
```

### 4. STEP Part 21 Output

The translator produces syntactically valid ISO-10303-21 text:

```
ISO-10303-21;
HEADER;

FILE_DESCRIPTION(
  ('PROTOTYPE_ACOUSTIC_STEP - MRP-5J',
   'Acoustic topology serialization',
   'NOT PRODUCTION B-REP'),
  '2;1');

FILE_NAME(
  'request_id.step',
  '2026-05-19T...',
  ('Luthiers Toolbox'),
  ('MRP-5J Acoustic Topology'),
  'STEP_PART21_PROTOTYPE',
  'AcousticStepTranslator 0.1.0',
  '');

ENDSEC;

DATA;

/* VALIDATION CERTIFICATE
   Request ID: ...
   Validation Passed: True
   Input Hash: ...
   Validation Hash: ...
*/

#1 = APPLICATION_CONTEXT('acoustic instrument topology');
#2 = PRODUCT('shell_id', 'component', 'Shell type: flat_extrusion', ());
...

ENDSEC;

END-ISO-10303-21;
```

### 5. Capability Registration

**Location:** `app/cam/translator_capability_registry.py`

```python
"step_acoustic_prototype": TranslatorCapability(
    translator_id="step_acoustic_prototype",
    translator_name="Acoustic STEP Prototype Translator",
    translator_version="0.1.0",
    translator_category="translator",
    output_class="step",
    output_format_version="STEP_PART21_PROTOTYPE",
    execution_state="validation_only",
    maturity="placeholder",
    execution_supported=False,
    notes="Consumes CertifiedTopology. NOT production B-rep. "
          "Classification: PROTOTYPE_SERIALIZATION.",
)
```

---

## Test Coverage

**Location:** `tests/cam/test_step_acoustic_translator.py`

| Test Class | Tests | Status |
|------------|-------|--------|
| TestCertifiedTopology | 6 | PASS |
| TestAcousticStepTranslator | 9 | PASS |
| TestStepFormat | 6 | PASS |
| TestCapabilityRegistry | 3 | PASS |
| TestIntegration | 4 | PASS |
| **Total** | **28** | **ALL PASS** |

**Combined MRP-5H/5I/5J:** 132 tests passing

---

## Key Boundaries Enforced

| Boundary | Enforcement |
|----------|-------------|
| Cannot instantiate CertifiedTopology directly | TypeError from __init__ |
| Cannot certify failing topology | ValidationError from certify() |
| Cannot translate without certification | TypeError from translate() |
| Cannot translate ValidationResult | can_translate() returns False |
| Cannot translate raw dict | can_translate() returns False |

---

## Output Classification

| Classification | Meaning |
|----------------|---------|
| PROTOTYPE_SERIALIZATION | What this translator produces |
| PRODUCTION_CAD | What this translator does NOT produce |

The output is syntactically valid STEP Part 21, but:
- No B-rep geometry (ADVANCED_FACE, etc.)
- No CAD kernel dependency
- Metadata and provenance only
- Clearly marked as prototype

---

## Files Created/Modified

### Created

| File | Purpose |
|------|---------|
| `app/cam/translators/step/__init__.py` | Package exports |
| `app/cam/translators/step/acoustic.py` | AcousticStepTranslator |
| `tests/cam/test_step_acoustic_translator.py` | Test suite |
| `docs/handoffs/MRP_5J_ACOUSTIC_STEP_RUNTIME_PROTOTYPE.md` | This document |

### Modified

| File | Change |
|------|--------|
| `app/cam/topology_validation/contracts.py` | Added CertifiedTopology |
| `app/cam/topology_validation/validators.py` | Added certify() method |
| `app/cam/topology_validation/__init__.py` | Export CertifiedTopology |
| `app/cam/translator_capability_registry.py` | Added step_acoustic_prototype |

---

## Usage Example

```python
from app.cam.topology_validation import certify_topology, ValidationError
from app.cam.translators.step import AcousticStepTranslator

# Build topology (MRP-5H)
topology_dict = {
    "request_id": "guitar-001",
    "tier": "PROTOTYPE",
    "shells": [{"shell_id": "body", "is_closed": True, "is_manifold": True, ...}],
}

# Certify topology (MRP-5I + 5J)
try:
    certified = certify_topology(topology_dict)
except ValidationError as e:
    print(f"Cannot certify: {e.message}")
    # Handle validation failure — cannot proceed to translation
    raise

# Translate to STEP (MRP-5J)
translator = AcousticStepTranslator()
artifact = translator.translate(certified)

# Use artifact
step_content = artifact.content.decode("utf-8")
print(f"Generated {len(step_content)} bytes of STEP")
print(f"Content hash: {artifact.content_hash}")
print(f"Provenance: {artifact.provenance}")
```

---

## Future Implementation Roadmap

| Sprint | Focus | Depends On |
|--------|-------|------------|
| MRP-5H | Topology builder prototype | MRP-5G |
| MRP-5I | Shell validation prototype | MRP-5H |
| MRP-5J | Acoustic STEP runtime prototype | MRP-5H, MRP-5I (this sprint) |
| MRP-5K | CAD kernel adapter abstraction | MRP-5J |
| MRP-5L | Continuity verification corpus | MRP-5K |

---

## Definition of Done

✅ CertifiedTopology cannot be instantiated directly  
✅ TopologyValidator.certify() returns CertifiedTopology only when passing  
✅ AcousticStepTranslator accepts only CertifiedTopology  
✅ AcousticStepTranslator rejects raw topology objects  
✅ STEP Part 21 output is syntactically valid  
✅ STEP output includes validation certificate  
✅ STEP output includes provenance metadata  
✅ step_acoustic_prototype registered in capability registry  
✅ 28 tests passing  
✅ No regression in MRP-5H/5I tests (132 total passing)  
✅ Handoff exists

---

## Related Documents

- `MRP_5H_ACOUSTIC_TOPOLOGY_BUILDER_PROTOTYPE.md` — Construction layer
- `MRP_5I_ACOUSTIC_SHELL_VALIDATION_PROTOTYPE.md` — Validation layer
- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
