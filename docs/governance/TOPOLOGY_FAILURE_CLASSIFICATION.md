# Topology Failure Classification

**Sprint:** MRP-5G  
**Status:** ACTIVE  
**Authority:** CAD Topology Governance

---

## Purpose

Define failure classifications for acoustic topology generation. These classifications ensure failures are handled consistently and no silent degradation occurs.

---

## Classification Levels

### BLOCKING

**Impact:** Topology generation cannot proceed. No output produced.

**Response:** Immediate rejection with error details.

**Logging:** ERROR level with full context.

### MAJOR

**Impact:** Output may be unsafe or incorrect. Requires investigation.

**Response:** 
- PROTOTYPE: Warning flag, output produced
- PRODUCTION: Blocking error, no output

**Logging:** WARNING level with context.

### WARNING

**Impact:** Minor issue, output usable but not ideal.

**Response:** Warning logged, output produced.

**Logging:** WARNING level.

### ACCEPTABLE

**Impact:** Expected variance, not a failure.

**Response:** None required.

**Logging:** DEBUG level if any.

---

## Failure Classification Table

### Shell Construction Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| Open shell | BLOCKING | REJECT | REJECT | Cannot close shell |
| Self-intersection | BLOCKING | REJECT | REJECT | Topology self-intersects |
| Non-manifold edge | MAJOR | WARNING | BLOCKING | Edge has ≠2 faces |
| Degenerate face | MAJOR | WARNING | BLOCKING | Face has zero area |
| Gap > 0.1mm | MAJOR | WARNING | BLOCKING | Excessive gap between edges |
| Gap 0.01-0.1mm | WARNING | LOG | BLOCKING | Minor gap detected |
| Gap < 0.01mm | ACCEPTABLE | — | LOG | Within tolerance |

### Continuity Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| G1 not achievable | MAJOR | WARNING | BLOCKING | Cannot achieve tangent continuity |
| G0 gap > tolerance | MAJOR | WARNING | BLOCKING | Positional discontinuity |
| Curvature spike | WARNING | LOG | WARNING | Sharp curvature change |

### Geometry Preservation Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| BOE point missing | BLOCKING | REJECT | REJECT | Approved point not in output |
| Drift > 0.01mm | MAJOR | WARNING | BLOCKING | Point position shifted |
| Drift > 0.001mm | WARNING | LOG | WARNING | Minor drift detected |
| Drift < 0.001mm | ACCEPTABLE | — | — | Within tolerance |

### Loft Generation Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| Unresolved loft | BLOCKING | REJECT | REJECT | Cannot interpolate profiles |
| Loft self-intersection | BLOCKING | REJECT | REJECT | Loft surface self-intersects |
| Loft deviation > 1mm | MAJOR | WARNING | BLOCKING | Poor interpolation |
| Loft deviation 0.1-1mm | WARNING | LOG | WARNING | Acceptable deviation |

### Semantic Input Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| Missing required field | BLOCKING | REJECT | REJECT | Required semantic missing |
| Invalid enum | BLOCKING | REJECT | REJECT | Unknown enum value |
| Ambiguous side profile | WARNING | LOG | LOG | Incomplete taper spec |
| Unsupported arch profile | UNSUPPORTED | REJECT | REJECT | Feature not implemented |

### Kernel Failures

| Failure | Severity | PROTOTYPE | PRODUCTION | Description |
|---------|----------|-----------|------------|-------------|
| Kernel crash | BLOCKING | REJECT | REJECT | CAD kernel failed |
| Kernel timeout | BLOCKING | REJECT | REJECT | Operation timed out |
| Kernel memory error | BLOCKING | REJECT | REJECT | Out of memory |
| Kernel unknown error | BLOCKING | REJECT | REJECT | Unclassified kernel error |

---

## Failure Response Matrix

### BLOCKING Response

```python
def handle_blocking(failure: TopologyFailure) -> TopologyResult:
    logger.error(
        "topology_blocking_failure",
        failure_type=failure.type,
        message=failure.message,
        context=failure.context,
    )
    
    return TopologyResult(
        success=False,
        shell=None,
        errors=[TopologyError(
            classification="BLOCKING",
            type=failure.type,
            message=failure.message,
        )],
    )
```

### MAJOR Response (PROTOTYPE)

```python
def handle_major_prototype(failure: TopologyFailure, partial_result) -> TopologyResult:
    logger.warning(
        "topology_major_warning",
        failure_type=failure.type,
        message=failure.message,
        tier="PROTOTYPE",
    )
    
    return TopologyResult(
        success=True,
        shell=partial_result.shell,
        warnings=[TopologyWarning(
            classification="MAJOR",
            type=failure.type,
            message=failure.message,
        )],
        tier=Tier.PROTOTYPE,
        marked_unsafe=True,
    )
```

### MAJOR Response (PRODUCTION)

```python
def handle_major_production(failure: TopologyFailure) -> TopologyResult:
    # MAJOR failures block production tier
    return handle_blocking(failure)
```

---

## Safe Rejection Protocol

### Principle: No Silent Degradation

```
NEVER produce incorrect output silently.
ALWAYS fail clearly when quality cannot be guaranteed.
NEVER fall back to lower-quality output without explicit marking.
```

### Rejection Message Format

```python
@dataclass
class TopologyRejection:
    failure_type: str
    severity: str
    message: str
    context: Dict[str, Any]
    suggestions: List[str]
    
    def to_user_message(self) -> str:
        return f"""
Topology generation failed: {self.failure_type}

Severity: {self.severity}
Details: {self.message}

Context:
{json.dumps(self.context, indent=2)}

Suggestions:
{chr(10).join(f"- {s}" for s in self.suggestions)}
"""
```

### Example Rejection

```
Topology generation failed: OPEN_SHELL

Severity: BLOCKING
Details: Cannot close shell - 3 edges have only 1 adjacent face

Context:
{
  "body_category": "acoustic_flat_top",
  "edge_count": 156,
  "open_edges": [12, 45, 89],
  "tier": "PROTOTYPE"
}

Suggestions:
- Verify profile is closed (first point = last point)
- Check for self-intersecting profile
- Reduce profile complexity
```

---

## Logging Standards

### BLOCKING

```python
logger.error(
    "topology_failure",
    severity="BLOCKING",
    failure_type=failure.type,
    body_category=semantics.body_category,
    profile_point_count=len(outline.points),
    message=failure.message,
)
```

### MAJOR

```python
logger.warning(
    "topology_failure",
    severity="MAJOR",
    failure_type=failure.type,
    tier=tier,
    body_category=semantics.body_category,
    message=failure.message,
)
```

### WARNING

```python
logger.warning(
    "topology_warning",
    severity="WARNING",
    warning_type=warning.type,
    message=warning.message,
)
```

---

## Telemetry

### Metrics to Track

| Metric | Description |
|--------|-------------|
| `topology_success_rate` | % successful builds |
| `topology_blocking_count` | Count of blocking failures |
| `topology_major_count` | Count of major failures |
| `topology_tier_distribution` | PROTOTYPE vs PRODUCTION |
| `topology_failure_types` | Distribution by failure type |

### Alerting Thresholds

| Condition | Alert Level |
|-----------|-------------|
| Success rate < 95% | WARNING |
| Success rate < 90% | CRITICAL |
| Blocking rate > 5% | WARNING |
| Kernel crash rate > 1% | CRITICAL |

---

## Related Documents

- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
- `CAD_REGRESSION_CLASSIFICATION_MODEL.md` — Related classification model
