# Agentic Contracts — Engineer Handoff

**Version:** 1.0.0
**Date:** 2026-02-06
**Status:** Phase 1 Complete (Contract-First Foundation)

---

## Executive Summary

This document describes the cross-repo agentic contract layer implemented across:
- **luthiers-toolbox** (`services/api/app/agentic/`)
- **tap_tone_pi** (`tap_tone_pi/agentic/`)

The contracts define the "thin waist" between repos, enabling agent orchestration without tight coupling. This is a **contract-first** approach—no agent brain logic, just shared vocabulary.

---

## 1. What Was Built

### 1.1 Contract Suite

| Contract | Purpose | File |
|----------|---------|------|
| `ToolCapabilityV1` | Declares what tools can do (manifest, not execution) | `contracts/tool_capability.py` |
| `AttentionDirectiveV1` | How agents guide user focus without touching internals | `contracts/analyzer_attention.py` |
| `AgentEventV1` | Unified event vocabulary across all repos | `contracts/event_emission.py` |
| `UWSMv1` | User Working Style Model for preference adaptation | `contracts/uwsm.py` (luthiers-toolbox only) |

### 1.2 Repository Locations

```
luthiers-toolbox/
└── services/api/app/agentic/
    ├── __init__.py                    # Module entry point
    ├── ARCHITECTURE_MAPPING.md        # Maps existing AI modules to contracts
    ├── contracts/
    │   ├── __init__.py
    │   ├── tool_capability.py         # ToolCapabilityV1, CapabilityAction, SafeDefaults
    │   ├── analyzer_attention.py      # AttentionDirectiveV1, AttentionAction, FocusTarget
    │   ├── event_emission.py          # AgentEventV1, EventType, EventSource
    │   └── uwsm.py                    # UWSMv1, PreferenceDimension, DecayConfig
    └── capabilities/
        ├── __init__.py                # Registry: get_all_capabilities()
        └── tap_tone_analyzer.py       # TAP_TONE_ANALYZER capability declaration

tap_tone_pi/
└── tap_tone_pi/agentic/
    ├── __init__.py                    # Module entry point
    ├── contracts/
    │   ├── __init__.py
    │   ├── tool_capability.py         # Matches luthiers-toolbox (dataclasses)
    │   ├── analyzer_attention.py      # Matches luthiers-toolbox (dataclasses)
    │   └── event_emission.py          # Matches luthiers-toolbox (dataclasses)
    ├── capabilities.py                # TAP_TONE_ANALYZER, WOLF_DETECTOR, etc.
    └── events.py                      # emit_event(), create_wolf_tone_directive()
```

### 1.3 Implementation Differences

| Aspect | luthiers-toolbox | tap_tone_pi |
|--------|------------------|-------------|
| Base class | Pydantic `BaseModel` | stdlib `dataclasses` |
| Validation | Pydantic validators (`extra="forbid"`) | None (lightweight) |
| Serialization | `.model_dump()` | `.to_dict()` |
| Dependencies | pydantic required | Zero external deps |
| UWSM | ✅ Included | ❌ Not needed (desktop app) |

**Both serialize to identical JSON format** — cross-repo compatibility verified by tests.

---

## 2. Contract Specifications

### 2.1 Tool Capability Contract (`ToolCapabilityV1`)

**Purpose:** Let the agent reason about *what is possible* without knowing *how it's implemented*.

```python
# Declaring a capability (tap_tone_pi/agentic/capabilities.py)
TAP_TONE_ANALYZER = ToolCapabilityV1(
    tool_id="tap_tone_analyzer",
    version="2.0.0",
    display_name="Tap Tone Analyzer",

    actions=[
        CapabilityAction.ANALYZE_AUDIO,
        CapabilityAction.ANALYZE_SPECTRUM,
        CapabilityAction.GENERATE_REPORT,
        CapabilityAction.VALIDATE_SCHEMA,
    ],

    input_schemas=[
        "tap_tone_bundle_v1",
        "audio_wav",
    ],
    output_schemas=[
        "wolf_candidates_v1",
        "ods_snapshot_v1",
        "viewer_pack_v1",
    ],

    safe_defaults=SafeDefaults(
        redaction_layer=2,          # Privacy layer for outputs
        dry_run=False,              # Analysis is read-only
        require_confirmation=False, # Non-destructive
        timeout_seconds=120,
    ),

    source_repo="tap_tone_pi",
)
```

**Key Fields:**

| Field | Purpose |
|-------|---------|
| `tool_id` | Unique identifier (snake_case) |
| `actions` | Closed vocabulary of what tool can do |
| `input_schemas` / `output_schemas` | Schema IDs for type discovery |
| `safe_defaults` | Explicit safety configuration |
| `source_repo` | Origin repository for tracing |

**CapabilityAction Vocabulary:**

```python
class CapabilityAction(str, Enum):
    # Analysis (read-only)
    ANALYZE_AUDIO = "analyze_audio"
    ANALYZE_GEOMETRY = "analyze_geometry"
    ANALYZE_TOOLPATH = "analyze_toolpath"
    ANALYZE_SPECTRUM = "analyze_spectrum"

    # Generation (creates artifacts)
    GENERATE_REPORT = "generate_report"
    GENERATE_GCODE = "generate_gcode"
    GENERATE_DXF = "generate_dxf"
    GENERATE_PREVIEW = "generate_preview"

    # Validation (conformance checks)
    VALIDATE_SCHEMA = "validate_schema"
    VALIDATE_FEASIBILITY = "validate_feasibility"
    VALIDATE_SAFETY = "validate_safety"

    # Transformation (modifies data)
    TRANSFORM_NORMALIZE = "transform_normalize"
    TRANSFORM_REDACT = "transform_redact"
    TRANSFORM_AGGREGATE = "transform_aggregate"
```

---

### 2.2 Attention Directive Contract (`AttentionDirectiveV1`)

**Purpose:** Allow the agent to guide *where the user looks* without touching *what the analyzer computes*.

```python
# Creating an attention directive (tap_tone_pi/agentic/events.py)
directive = AttentionDirectiveV1(
    directive_id="attn_abc123",
    action=AttentionAction.REVIEW,
    summary="Potential wolf tone at 247Hz",
    detail=(
        "The analyzer detected a potential wolf tone at 247Hz "
        "with 87% confidence. Consider adjusting bracing."
    ),
    focus=FocusTarget(
        target_type="spectrum_region",
        target_id="peak_3",
        highlight_region={"freq_hz": 247, "bandwidth_hz": 10},
    ),
    urgency=0.7,
    confidence=0.87,
    evidence_refs=["wolf_candidates_v1:abc123:peak_3"],
    source_tool="tap_tone_wolf_detector",
)
```

**AttentionAction Vocabulary (ordered by urgency):**

```python
class AttentionAction(str, Enum):
    # Low urgency - FYI
    INSPECT = "inspect"      # Look at this when you have time

    # Medium urgency - needs review
    REVIEW = "review"        # Please look at this soon
    COMPARE = "compare"      # Compare these two things

    # High urgency - needs decision
    DECIDE = "decide"        # Make a choice between options
    CONFIRM = "confirm"      # Approve or reject

    # Critical - needs immediate action
    INTERVENE = "intervene"  # Stop and fix this now
    ABORT = "abort"          # Stop everything
```

**Explicit Non-Goals (Critical for Repo Autonomy):**

The agent:
- ❌ Cannot change measurement parameters
- ❌ Cannot start/stop acquisition
- ❌ Cannot export data
- ❌ Cannot persist analyzer state
- ✅ Can only point, highlight, and reset view

---

### 2.3 Event Emission Contract (`AgentEventV1`)

**Purpose:** Ensure all repos emit the same event vocabulary so the agent can reason consistently.

```python
# Emitting an event (tap_tone_pi/agentic/events.py)
from tap_tone_pi.agentic import emit_analysis_completed

event = emit_analysis_completed(
    component="wolf_detector",
    run_id="run_abc123",
    artifacts_created=["wolf_candidates.json", "ods_snapshot.json"],
    metrics={"peak_count": 12, "max_confidence": 0.87},
)
```

**EventType Vocabulary:**

```python
class EventType(str, Enum):
    # Analysis lifecycle
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"

    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_VALIDATED = "artifact_validated"
    ARTIFACT_REJECTED = "artifact_rejected"
    ARTIFACT_PROMOTED = "artifact_promoted"

    # Decision events
    DECISION_REQUIRED = "decision_required"
    DECISION_MADE = "decision_made"
    DECISION_DEFERRED = "decision_deferred"

    # Attention events
    ATTENTION_REQUESTED = "attention_requested"
    ATTENTION_ACKNOWLEDGED = "attention_acknowledged"
    ATTENTION_DISMISSED = "attention_dismissed"

    # User interaction
    USER_ACTION = "user_action"
    USER_FEEDBACK = "user_feedback"
    USER_PREFERENCE_UPDATED = "user_preference_updated"

    # System events
    SYSTEM_HEALTH = "system_health"
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
```

**Important Rule:** No repo emits "confusion," "expertise," or "intent." Only observable actions. Interpretation lives *above* this layer.

---

## 3. Integration Patterns

### 3.1 For Analyzer Repos (tap_tone_pi pattern)

**Step 1: Declare Capabilities**

```python
# In your_repo/agentic/capabilities.py
from .contracts import ToolCapabilityV1, CapabilityAction, SafeDefaults

YOUR_ANALYZER = ToolCapabilityV1(
    tool_id="your_analyzer",
    version="1.0.0",
    display_name="Your Analyzer",
    actions=[CapabilityAction.ANALYZE_AUDIO],
    input_schemas=["your_input_schema_v1"],
    output_schemas=["your_output_schema_v1"],
    safe_defaults=SafeDefaults(
        redaction_layer=2,
        require_confirmation=False,
    ),
    source_repo="your_repo",
)
```

**Step 2: Emit Events**

```python
# In your analysis pipeline
from your_repo.agentic import emit_analysis_started, emit_analysis_completed

def run_analysis(run_id: str, input_path: Path):
    # Emit start event
    emit_analysis_started("your_pipeline", run_id)

    try:
        result = do_analysis(input_path)

        # Emit completion event
        emit_analysis_completed(
            "your_pipeline",
            run_id,
            artifacts_created=[str(p) for p in result.output_paths],
            metrics=result.metrics,
        )
        return result

    except Exception as e:
        emit_analysis_failed("your_pipeline", run_id, str(e))
        raise
```

**Step 3: Create Attention Directives (Optional)**

```python
# When you find something noteworthy
from your_repo.agentic import AttentionDirectiveV1, AttentionAction, FocusTarget

def create_finding_directive(finding):
    return AttentionDirectiveV1(
        directive_id=f"attn_{uuid.uuid4().hex[:12]}",
        action=AttentionAction.REVIEW,
        summary=f"Found {finding.type} at {finding.location}",
        focus=FocusTarget(
            target_type="region",
            target_id=finding.id,
        ),
        urgency=finding.severity,
        confidence=finding.confidence,
        source_tool="your_analyzer",
    )
```

---

### 3.2 For Experience Shell (luthiers-toolbox pattern)

**Step 1: Discover Capabilities**

```python
from app.agentic import get_all_capabilities, get_capability_by_id

# List all available tools
for cap in get_all_capabilities():
    print(f"{cap.tool_id}: {cap.actions}")

# Look up specific tool
analyzer = get_capability_by_id("tap_tone_analyzer")
if analyzer and CapabilityAction.ANALYZE_SPECTRUM in analyzer.actions:
    # Can use spectrum analysis
    pass
```

**Step 2: Consume Events**

```python
# Events come as JSON, parse to contract
from app.agentic.contracts import AgentEventV1, EventType

def handle_event(event_json: dict):
    event = AgentEventV1(**event_json)

    if event.event_type == EventType.ANALYSIS_COMPLETED:
        # Update UI with results
        pass
    elif event.event_type == EventType.ATTENTION_REQUESTED:
        # Show notification
        directive = event.payload.get("directive")
        show_attention_toast(directive)
```

**Step 3: Render Attention Directives**

```python
# In Vue component or similar
def render_directive(directive: AttentionDirectiveV1):
    if directive.action == AttentionAction.REVIEW:
        show_toast(directive.summary, level="warning")
    elif directive.action == AttentionAction.INTERVENE:
        show_modal(directive.summary, directive.detail)

    # Highlight the focus target
    highlight_region(
        directive.focus.target_type,
        directive.focus.target_id,
        directive.focus.highlight_region,
    )
```

---

## 4. Designer Code Alignment Script

### 4.1 Contract Compliance Checklist

When adding a new tool/analyzer to the ecosystem:

```bash
#!/bin/bash
# contract_compliance_check.sh

REPO_PATH=$1

echo "=== Contract Compliance Check ==="

# 1. Check for capability declaration
echo "1. Checking for capability declaration..."
if grep -r "ToolCapabilityV1" "$REPO_PATH" > /dev/null; then
    echo "   ✅ ToolCapabilityV1 found"
else
    echo "   ❌ Missing ToolCapabilityV1 declaration"
fi

# 2. Check for event emission
echo "2. Checking for event emission..."
if grep -r "emit_event\|AgentEventV1" "$REPO_PATH" > /dev/null; then
    echo "   ✅ Event emission found"
else
    echo "   ⚠️  No event emission (optional but recommended)"
fi

# 3. Check for closed vocabulary usage
echo "3. Checking vocabulary usage..."
if grep -r "CapabilityAction\." "$REPO_PATH" > /dev/null; then
    echo "   ✅ Using CapabilityAction vocabulary"
else
    echo "   ❌ Not using CapabilityAction vocabulary"
fi

if grep -r "EventType\." "$REPO_PATH" > /dev/null; then
    echo "   ✅ Using EventType vocabulary"
else
    echo "   ⚠️  Not using EventType vocabulary"
fi

# 4. Check for safe defaults
echo "4. Checking safe defaults..."
if grep -r "SafeDefaults" "$REPO_PATH" > /dev/null; then
    echo "   ✅ SafeDefaults declared"
else
    echo "   ❌ Missing SafeDefaults"
fi

# 5. Check for source_repo declaration
echo "5. Checking source_repo..."
if grep -r "source_repo=" "$REPO_PATH" > /dev/null; then
    echo "   ✅ source_repo declared"
else
    echo "   ❌ Missing source_repo"
fi

echo ""
echo "=== Compliance Summary ==="
```

### 4.2 New Repo Bootstrap Script

```bash
#!/bin/bash
# bootstrap_agentic_contracts.sh
# Run from the root of a new repo that needs agentic contracts

REPO_NAME=$1
PACKAGE_PATH=$2  # e.g., "my_package/agentic"

if [ -z "$REPO_NAME" ] || [ -z "$PACKAGE_PATH" ]; then
    echo "Usage: bootstrap_agentic_contracts.sh <repo_name> <package_path>"
    exit 1
fi

echo "Bootstrapping agentic contracts for $REPO_NAME..."

# Create directory structure
mkdir -p "$PACKAGE_PATH/contracts"

# Create __init__.py files
cat > "$PACKAGE_PATH/__init__.py" << 'EOF'
"""
Agentic Layer — Cross-repo contracts for agent orchestration.
"""

__version__ = "1.0.0"

from .contracts import (
    ToolCapabilityV1,
    CapabilityAction,
    SafeDefaults,
    AttentionDirectiveV1,
    AttentionAction,
    FocusTarget,
    AgentEventV1,
    EventType,
    EventSource,
)

from .capabilities import get_capabilities, get_capability_by_id

__all__ = [
    "ToolCapabilityV1", "CapabilityAction", "SafeDefaults",
    "AttentionDirectiveV1", "AttentionAction", "FocusTarget",
    "AgentEventV1", "EventType", "EventSource",
    "get_capabilities", "get_capability_by_id",
]
EOF

echo "Created $PACKAGE_PATH/__init__.py"

# Create contracts/__init__.py
cat > "$PACKAGE_PATH/contracts/__init__.py" << 'EOF'
"""Agentic Layer Contracts"""
from .tool_capability import ToolCapabilityV1, CapabilityAction, SafeDefaults
from .analyzer_attention import AttentionDirectiveV1, AttentionAction, FocusTarget
from .event_emission import AgentEventV1, EventType, EventSource

__all__ = [
    "ToolCapabilityV1", "CapabilityAction", "SafeDefaults",
    "AttentionDirectiveV1", "AttentionAction", "FocusTarget",
    "AgentEventV1", "EventType", "EventSource",
]
EOF

echo "Created $PACKAGE_PATH/contracts/__init__.py"

echo ""
echo "=== Next Steps ==="
echo "1. Copy contract files from tap_tone_pi/tap_tone_pi/agentic/contracts/"
echo "2. Create capabilities.py with your tool's capability declaration"
echo "3. Create events.py with convenience emitters"
echo "4. Add tests in tests/test_agentic_contracts.py"
echo ""
echo "Reference implementations:"
echo "  - tap_tone_pi/tap_tone_pi/agentic/ (dataclasses, zero deps)"
echo "  - luthiers-toolbox/services/api/app/agentic/ (pydantic)"
```

---

## 5. Cross-Repo Coordination Rules

### 5.1 Contract Versioning

| Version | Meaning |
|---------|---------|
| `1.0.x` | Additive only (new optional fields) |
| `1.x.0` | New optional features |
| `2.0.0` | Breaking changes (requires migration) |

### 5.2 Compatibility Rules

1. **Closed Vocabularies:** Only use enum values defined in contracts
2. **Forward Compatibility:** Ignore unknown fields when parsing
3. **Backward Compatibility:** New fields must have defaults
4. **Graceful Degradation:** Agent must handle missing capabilities

### 5.3 Privacy Rules

| Layer | Retention | Content |
|-------|-----------|---------|
| 0 | Ephemeral | Raw events, UWSM signals |
| 1 | Session | Session-scoped aggregates |
| 2 | 30 days | Analysis results, artifacts |
| 3 | 1 year | Anonymized metrics |
| 4 | Indefinite | Aggregate statistics |
| 5 | Cohort-only | No individual data |

Default: `privacy_layer=3` for events, `privacy_layer=0` for UWSM.

---

## 6. Testing Requirements

### 6.1 Required Tests Per Repo

```python
# tests/test_agentic_contracts.py

class TestContractCompliance:
    """Every repo must pass these tests."""

    def test_capability_declaration_exists(self):
        """At least one capability must be declared."""
        caps = get_capabilities()
        assert len(caps) >= 1

    def test_capability_has_source_repo(self):
        """All capabilities must declare source_repo."""
        for cap in get_capabilities():
            assert cap.source_repo != ""

    def test_capability_has_safe_defaults(self):
        """All capabilities must have safe_defaults."""
        for cap in get_capabilities():
            assert cap.safe_defaults is not None
            assert cap.safe_defaults.timeout_seconds > 0

    def test_event_serialization(self):
        """Events must serialize to JSON."""
        event = AgentEventV1(
            event_id="test",
            event_type=EventType.ANALYSIS_STARTED,
            source=EventSource(repo="test", component="test"),
        )
        d = event.to_dict()
        import json
        json.dumps(d)  # Must not raise

    def test_event_has_required_fields(self):
        """Serialized events must have required fields."""
        event = AgentEventV1(
            event_id="test",
            event_type=EventType.ANALYSIS_STARTED,
            source=EventSource(repo="test", component="test"),
        )
        d = event.to_dict()
        assert "event_id" in d
        assert "event_type" in d
        assert "source" in d
        assert "occurred_at" in d
```

### 6.2 Cross-Repo Compatibility Tests

```python
# Run in luthiers-toolbox to verify tap_tone_pi compatibility

def test_tap_tone_event_parseable():
    """Events from tap_tone_pi must parse in luthiers-toolbox."""
    # Simulated event from tap_tone_pi
    tap_tone_event = {
        "event_id": "evt_abc123",
        "event_type": "analysis_completed",
        "source": {"repo": "tap_tone_pi", "component": "wolf_detector", "version": "2.0.0"},
        "payload": {"candidates_found": 3},
        "privacy_layer": 2,
        "occurred_at": "2026-02-06T12:00:00Z",
        "schema_version": "1.0.0",
    }

    # Must parse without error
    from app.agentic.contracts import AgentEventV1
    event = AgentEventV1(**tap_tone_event)
    assert event.source.repo == "tap_tone_pi"
```

---

## 7. Rollout Phases

### Phase 1: Contract Foundation ✅ COMPLETE
- [x] Define contracts in luthiers-toolbox
- [x] Mirror contracts in tap_tone_pi
- [x] Add unit tests
- [x] Push to both repos

### Phase 2: Event Integration (Next)
- [ ] Wire event emission into tap_tone_pi analysis pipeline
- [ ] Add event consumer in luthiers-toolbox
- [ ] Shadow mode logging (events logged but not acted upon)

### Phase 3: Attention Layer
- [ ] tap_tone_pi emits attention directives for findings
- [ ] luthiers-toolbox renders directives in UI
- [ ] Dismissal tracking

### Phase 4: UWSM Integration
- [ ] Signal collection from user interactions
- [ ] Preference-aware agent behavior
- [ ] Local-only storage (privacy layer 0)

---

## 8. Reference Links

| Resource | Location |
|----------|----------|
| luthiers-toolbox contracts | `services/api/app/agentic/` |
| tap_tone_pi contracts | `tap_tone_pi/agentic/` |
| Architecture mapping | `services/api/app/agentic/ARCHITECTURE_MAPPING.md` |
| luthiers-toolbox tests | `services/api/tests/test_agentic_contracts.py` |
| tap_tone_pi tests | `tests/test_agentic_contracts.py` |

---

## 9. Contact & Ownership

| Component | Owner |
|-----------|-------|
| Contract definitions | Shared (both repos) |
| tap_tone_pi implementation | tap_tone_pi maintainers |
| luthiers-toolbox implementation | luthiers-toolbox maintainers |
| Agent orchestration | luthiers-toolbox (future) |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-02-06
**Generated by:** Claude Code
