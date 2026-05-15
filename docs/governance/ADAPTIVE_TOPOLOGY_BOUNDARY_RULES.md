# Adaptive Topology Boundary Rules

**Sprint:** MRP-5G  
**Status:** ACTIVE  
**Authority:** CAD Topology Governance

---

## Purpose

Document explicit separation between deterministic morphology systems and adaptive/AI-assisted intelligence. These rules ensure topology authority remains with deterministic, auditable systems.

---

## Core Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   DETERMINISTIC MORPHOLOGY SPINE = AUTHORITATIVE               │
│                                                                 │
│   ADAPTIVE INTELLIGENCE LAYER = ADVISORY ONLY                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Topology authority MUST remain with deterministic systems.

---

## What Adaptive Systems May NOT Do

### 1. Topology Authority

```
NO: LLM-based topology construction
NO: AI geometry mutation
NO: Probabilistic shell generation
NO: Neural network surface fitting
NO: Adaptive geometry override
```

### 2. Geometry Modification

```
NO: AI-suggested coordinate changes to BOE points
NO: ML-based profile smoothing
NO: Automatic geometry "improvement"
NO: Unsupervised geometry optimization
```

### 3. Semantic Override

```
NO: LLM interpretation of cad_semantics
NO: AI-inferred thickness values
NO: Adaptive semantic extension
NO: ML-predicted body categories
```

### 4. Validation Bypass

```
NO: AI-approved topology validation
NO: ML confidence as validation substitute
NO: Neural-network manifold verification
NO: Probabilistic closure checking
```

---

## What Adaptive Systems MAY Do

### 1. Strategy Recommendation

```
YES: Recommend topology construction approach
YES: Suggest parameter values for user approval
YES: Rank extraction strategies
YES: Classify input quality
```

**Key Rule:** Recommendations require explicit user/system acceptance.

### 2. Contour Classification

```
YES: Classify contour types (body, void, annotation)
YES: Rank contour extraction confidence
YES: Flag ambiguous geometry for review
YES: Suggest layer assignments
```

**Key Rule:** Classification is advisory; user confirms final assignment.

### 3. Quality Assessment

```
YES: Score extraction quality
YES: Identify likely problem areas
YES: Recommend resolution strategies
YES: Predict failure likelihood
```

**Key Rule:** Assessment informs user; does not gate topology.

### 4. Parameter Suggestion

```
YES: Suggest thickness values based on instrument type
YES: Recommend continuity targets
YES: Propose taper profiles
YES: Estimate material requirements
```

**Key Rule:** Suggestions populate defaults; user explicitly confirms.

---

## Architectural Boundary

### Deterministic Layer (Authoritative)

```
┌─────────────────────────────────────────┐
│         DETERMINISTIC SPINE             │
│                                         │
│  BOE → cad_semantics → Topology Builder │
│                                         │
│  - Approved geometry                    │
│  - Validated semantics                  │
│  - Deterministic construction           │
│  - Auditable output                     │
│                                         │
│  Authority: FINAL                       │
└─────────────────────────────────────────┘
```

### Adaptive Layer (Advisory)

```
┌─────────────────────────────────────────┐
│         ADAPTIVE INTELLIGENCE           │
│                                         │
│  - Strategy recommendation              │
│  - Quality assessment                   │
│  - Parameter suggestion                 │
│  - Failure prediction                   │
│                                         │
│  Authority: ADVISORY ONLY               │
│  Requires: Explicit acceptance          │
└─────────────────────────────────────────┘
```

### Integration Pattern

```
User Input
    │
    ▼
┌─────────────────────┐
│ Adaptive Assistant  │ ──── Suggests parameters
└─────────────────────┘
    │
    │ Advisory suggestions
    ▼
┌─────────────────────┐
│ User Confirmation   │ ──── User accepts/modifies
└─────────────────────┘
    │
    │ Confirmed values
    ▼
┌─────────────────────┐
│ Deterministic Spine │ ──── Executes with confirmed values
└─────────────────────┘
    │
    │ Auditable output
    ▼
Result
```

---

## AGE Pattern Applicability

### Existing AGE Pattern

The codebase includes an AGE (Agentic Guidance Engine) pattern from tap_tone_pi:
- Stage-aware prompt construction
- Silent fallback when API unavailable
- Suppression logic for repeated guidance

### AGE Boundary in Topology

```
AGE MAY:
- Evaluate extraction quality
- Recommend extraction strategy
- Explain topology decisions
- Assist with failure diagnosis

AGE MAY NOT:
- Construct topology directly
- Modify approved geometry
- Override validation results
- Bypass deterministic pipeline
```

### Example: Allowed AGE Integration

```python
class TopologyGuidanceEngine:
    """AGE for topology construction guidance."""
    
    def suggest_construction_approach(
        self, semantics: CadSemantics, profile: Profile
    ) -> ConstructionSuggestion:
        """
        Suggest topology construction approach.
        
        Returns advisory suggestion; does not execute construction.
        """
        prompt = self._build_suggestion_prompt(semantics, profile)
        
        try:
            response = self._call_claude_api(prompt)
            return self._parse_suggestion(response)
        except Exception:
            # Silent fallback — never block deterministic pipeline
            return self._default_suggestion(semantics)
    
    def explain_failure(
        self, failure: TopologyFailure
    ) -> FailureExplanation:
        """
        Explain topology failure in user-friendly terms.
        
        Purely informational; does not affect failure handling.
        """
        ...
```

### Example: Prohibited AGE Integration

```python
# PROHIBITED: AGE constructing topology
class TopologyConstructionEngine:  # ← WRONG
    def build_topology_with_ai(self, profile, semantics):
        # This violates adaptive boundary rules
        response = self._call_claude_api(
            f"Generate shell topology for {profile}"
        )
        return self._parse_topology(response)  # ← PROHIBITED
```

---

## Enforcement

### Code Review Checklist

When reviewing topology-related code:

- [ ] No LLM calls that produce geometry
- [ ] No AI output used as topology authority
- [ ] Adaptive suggestions require explicit acceptance
- [ ] Deterministic pipeline has no AI dependencies
- [ ] Fallback behavior is deterministic

### Automated Checks

```python
# Prohibited import patterns in topology code
PROHIBITED_IN_TOPOLOGY = [
    "openai",
    "anthropic",
    "langchain",
    "transformers",
    "torch",
    "tensorflow",
]

def check_topology_module(module_path):
    """Verify topology code has no AI dependencies."""
    imports = extract_imports(module_path)
    for imp in imports:
        if any(prohibited in imp for prohibited in PROHIBITED_IN_TOPOLOGY):
            raise AdaptiveBoundaryViolation(
                f"Prohibited import {imp} in topology module"
            )
```

### Exception Process

If adaptive integration is truly needed:

1. Document specific use case
2. Governance review required
3. Must be advisory-only
4. Must have deterministic fallback
5. Must be behind feature flag
6. Must have explicit user acceptance

---

## Future Adaptive Opportunities

### Allowed Future Work

| Feature | Boundary Compliance |
|---------|---------------------|
| AI-assisted parameter tuning | ✓ Advisory, user confirms |
| ML extraction quality scoring | ✓ Advisory, does not gate |
| LLM failure explanation | ✓ Informational only |
| Neural contour classification | ✓ Advisory, user confirms |

### Prohibited Future Work

| Feature | Reason |
|---------|--------|
| AI topology generation | Violates determinism |
| ML geometry optimization | Violates BOE authority |
| Neural validation bypass | Violates safety |
| LLM semantic interpretation | Violates determinism |

---

## Related Documents

- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `VECTORIZER ARCHITECTURE DECISION` (CLAUDE.md) — AGE pattern reference
