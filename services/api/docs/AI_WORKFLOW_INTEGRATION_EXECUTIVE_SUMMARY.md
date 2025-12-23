# AI Workflow Integration - Executive Summary

## Overview

The RMOS AI system integrates with the customer workflow at **three critical touchpoints** where AI-generated designs transition into manufacturable artifacts:

1. **Design Generation** - AI creates candidate rosette designs based on customer constraints
2. **Attachment Binding** - Customer-approved designs attach to run artifacts with feasibility verification
3. **Workflow Progression** - Artifacts flow through approval gates into production toolpaths

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CUSTOMER WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ① Customer Input (Context + Constraints)                       │
│     └─> Material, Tool, Machine Specs                           │
│     └─> Design Intent (rings, patterns, complexity)             │
│                                                                   │
│  ② AI Generation (Domain Layer)                                 │
│     ┌──────────────────────────────────────────┐               │
│     │ POST /api/rmos/ai/constraint-search      │               │
│     │   → app/rmos/ai_search.py                │               │
│     │   → app/rmos/ai/generators.py            │               │
│     │   → app/ai/transport/llm_client.py       │               │
│     └──────────────────────────────────────────┘               │
│                         ↓                                        │
│     Customer Output: RosetteParamSpec JSON                      │
│                         ↓                                        │
│  ③ Attachment Storage (Content-Addressed)                       │
│     ┌──────────────────────────────────────────┐               │
│     │ POST /api/runs/{run_id}/attachments      │               │
│     │   → SHA256 verification                   │               │
│     │   → services/api/data/run_attachments/   │               │
│     └──────────────────────────────────────────┘               │
│                         ↓                                        │
│  ④ Binding + Feasibility Gate                                   │
│     ┌──────────────────────────────────────────┐               │
│     │ POST /api/runs/{run_id}/artifacts/       │               │
│     │      bind-art-studio-candidate            │               │
│     │   → Feasibility scoring                   │               │
│     │   → Decision: ALLOW or BLOCK              │               │
│     │   → Creates RunArtifact (audit trail)     │               │
│     └──────────────────────────────────────────┘               │
│                         ↓                                        │
│  ⑤ Workflow State Transition                                    │
│     ┌──────────────────────────────────────────┐               │
│     │ POST /api/rmos/workflow/approve          │               │
│     │   → Operator/System approval              │               │
│     │   → State: PENDING → APPROVED             │               │
│     └──────────────────────────────────────────┘               │
│                         ↓                                        │
│  ⑥ Toolpath Generation                                          │
│     Customer Output → Manufacturing Instructions                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code Integration Points

### 1. AI Generation Entry Point (Customer Request → AI Output)

**Location:** `app/rmos/api_ai_routes.py`

```python
@router.post("/constraint-search", response_model=AiSearchResponse)
async def constraint_search(
    request: AiSearchRequest,
    background_tasks: BackgroundTasks,
) -> AiSearchResponse:
    """
    Customer-facing API: Generate rosette design from constraints.
    
    Input (from customer):
    - context: {tool_id, material_id, machine_id, target_diameter}
    - search_budget: {max_attempts, time_limit_seconds}
    
    Output (to customer):
    - best_design: RosetteParamSpec (JSON)
    - status: "success" | "best_effort" | "exhausted"
    - attempts_made: int
    - feasibility_score: float (0-100)
    """
    # Policy validation (customer constraints within system limits)
    validate_request_against_policy(request)
    
    # Run AI search loop (domain layer)
    response = run_constraint_first_search(request)
    
    return response  # Customer receives JSON design spec
```

**Customer Input Schema:**
```python
class AiSearchRequest(BaseModel):
    workflow_mode: str = "constraint_first"
    context: Dict[str, Any]  # Material palette, dimensions, etc.
    search_budget: SearchBudget  # How much AI compute to use
```

**Customer Output Schema:**
```python
class AiSearchResponse(BaseModel):
    run_id: str  # Unique identifier for this generation run
    status: SearchStatus  # "success" | "best_effort" | "exhausted"
    best_design: Optional[Dict[str, Any]]  # RosetteParamSpec JSON
    feasibility_score: float  # 0-100 manufacturing score
    attempts_made: int
    time_elapsed_seconds: float
    attempts: List[SearchAttemptSummary]  # Audit trail
```

---

### 2. AI Search Loop (Core Generation Logic)

**Location:** `app/rmos/ai_search.py`

```python
def run_constraint_first_search(request: AiSearchRequest) -> AiSearchResponse:
    """
    Core search loop: Generate → Score → Track Best → Repeat
    
    This is where customer creativity meets AI capability.
    The AI does NOT decide what rosette to make - it explores
    the design space defined by customer constraints.
    """
    run_id = new_run_id()
    budget = request.search_budget
    ctx = request.context
    
    # Create generator factory (domain-specific, NOT platform layer)
    from app.rmos.ai import make_candidate_generator_for_request
    from app.rmos.models import SearchBudgetSpec
    
    generator = make_candidate_generator_for_request(
        ctx=RmosContext(**ctx),
        budget=SearchBudgetSpec(**budget.model_dump()),
    )
    
    best_design = None
    best_score = 0.0
    attempts = []
    start_time = time.time()
    
    for attempt_num in range(budget.max_attempts):
        # Generate candidate (AI platform call happens here)
        candidate = generator(prev=best_design, attempt=attempt_num)
        
        # Score feasibility (manufacturing constraints)
        feasibility = score_design_feasibility(candidate, ctx)
        
        # Track best result
        if feasibility.score > best_score:
            best_design = candidate
            best_score = feasibility.score
        
        # Log attempt (audit trail for customer)
        attempts.append(SearchAttemptSummary(
            attempt_num=attempt_num,
            candidate_hash=_hash_candidate(candidate),
            feasibility_score=feasibility.score,
            risk_bucket=feasibility.risk_bucket,
        ))
        
        # Budget checks
        if time.time() - start_time > budget.time_limit_seconds:
            status = SearchStatus.TIMEOUT
            break
        
        if best_score >= budget.min_feasibility_score:
            status = SearchStatus.SUCCESS
            break
    
    # Return best design found to customer
    return AiSearchResponse(
        run_id=run_id,
        status=status,
        best_design=_design_to_dict(best_design),
        feasibility_score=best_score,
        attempts_made=len(attempts),
        time_elapsed_seconds=time.time() - start_time,
        attempts=attempts,
    )
```

---

### 3. Domain Generator Factory (Rosette-Specific Logic)

**Location:** `app/rmos/ai/generators.py`

```python
def make_candidate_generator_for_request(
    *,
    ctx: RmosContext,
    budget: SearchBudgetSpec,
) -> CandidateGenerator:
    """
    Factory pattern: Returns callable generator (NOT direct JSON).
    
    This preserves the RMOS search loop's ability to control timing
    and iterate with previous results.
    
    User Creativity Invariant:
    - AI prompts here reflect RMOS domain knowledge
    - Platform layer (app/ai/*) is goal-agnostic
    - Customer intent flows through ctx parameters
    """
    from app.rmos.ai.constraints import constraints_from_context
    from app.rmos.ai.coercion import coerce_to_rosette_spec
    from app.ai import generate_structured  # Platform transport
    
    # Build domain-specific constraints from customer context
    constraints_text = constraints_from_context(ctx)
    
    def generator(prev: Optional[RosetteParamSpec], attempt: int) -> RosetteParamSpec:
        """
        Callable generator invoked by search loop.
        
        Args:
            prev: Previous best design (for iterative refinement)
            attempt: Attempt number (for temperature/diversity control)
        
        Returns:
            RosetteParamSpec: Customer-facing design specification
        """
        # Build prompt with customer constraints + iteration context
        prompt = f"""
        Generate a manufacturable rosette design.
        
        Customer Constraints:
        {constraints_text}
        
        Iteration Context:
        - Attempt {attempt + 1}
        - Previous best: {prev.model_dump() if prev else "None"}
        
        Requirements:
        - Must satisfy all material/tool constraints
        - Dimensions must fit within bounds
        - Ring patterns must be geometrically valid
        """
        
        # Call AI platform (transport layer, goal-agnostic)
        result = generate_structured(
            prompt=prompt,
            response_model=RosetteParamSpec,
            temperature=0.7 + (attempt * 0.05),  # Increase diversity
        )
        
        # Coerce/validate to final spec
        return coerce_to_rosette_spec(result, ctx)
    
    return generator  # Return callable, not direct result
```

---

### 4. Attachment Storage (Customer Output → Content-Addressed Storage)

**Location:** `app/rmos/runs_v2/api_runs.py`

```python
@router.post("/{run_id}/attachments", response_model=RunAttachmentCreateResponse)
def create_run_attachment(run_id: str, req: RunAttachmentCreateRequest):
    """
    Store customer-approved AI output as verified attachment.
    
    Customer workflow:
    1. Receive AI-generated RosetteParamSpec JSON
    2. Review design in UI
    3. Upload as attachment with SHA256 verification
    4. Proceed to binding + feasibility gate
    
    Content-addressed storage:
    - SHA256 prevents corruption
    - Automatic deduplication
    - Immutable artifact trail
    """
    import base64
    from .attachments import put_bytes_attachment
    from .hashing import sha256_of_bytes
    
    # Decode customer payload
    data = base64.b64decode(req.b64)
    
    # Verify integrity (fail closed on mismatch)
    actual_sha = sha256_of_bytes(data)
    if actual_sha != req.sha256:
        raise HTTPException(
            status_code=400,
            detail=f"SHA256 mismatch: customer declared {req.sha256}, actual {actual_sha}"
        )
    
    # Store with metadata
    attachment, path = put_bytes_attachment(
        data=data,
        kind=req.kind,  # "geometry_spec_json", "geometry_svg", etc.
        mime=req.content_type,
        filename=req.filename,
        ext="",
    )
    
    # Return content-addressed ID to customer
    return RunAttachmentCreateResponse(
        attachment_id=attachment.sha256,  # SHA256 IS the attachment ID
        sha256=attachment.sha256,
        kind=attachment.kind,
    )
```

---

### 5. Art Studio Binding (Feasibility Gate)

**Location:** `app/rmos/runs_v2/api_runs.py`

```python
@router.post(
    "/{run_id}/artifacts/bind-art-studio-candidate",
    response_model=BindArtStudioCandidateResponse
)
def bind_art_studio_candidate(run_id: str, req: BindArtStudioCandidateRequest):
    """
    Bind customer-approved design to run artifact with feasibility gate.
    
    Customer workflow gate:
    - Customer uploads AI-generated design (via POST attachments)
    - System verifies feasibility (manufacturing constraints)
    - Decision: ALLOW or BLOCK
    - BOTH create RunArtifact (audit trail)
    
    Blocked Persistence Policy:
    - ALLOW → status=OK, customer proceeds to toolpaths
    - BLOCK → status=BLOCKED, customer notified, artifact persisted
    - Invalid → 400 error, no artifact (fail closed)
    """
    from .attachments import get_attachment_path
    from .hashing import sha256_of_obj
    from .store import create_blocked_artifact_for_violations
    
    # Verify customer's attachments exist
    attachment_sha_map = {}
    for att_id in req.attachment_ids:
        sha256 = att_id.replace("att-", "")
        path = get_attachment_path(sha256)
        if path is None:
            if req.strict:
                raise HTTPException(
                    status_code=400,
                    detail=f"Customer attachment {att_id} not found"
                )
        attachment_sha_map[att_id] = sha256
    
    # Run feasibility check (manufacturing constraints)
    # TODO: Replace mock with real feasibility engine
    feasibility_data = {
        "decision": "ALLOW",  # or "BLOCK"
        "score": 0.85,  # 0.0 - 1.0
        "risk_level": "GREEN",  # GREEN | YELLOW | RED
        "attachment_ids": list(attachment_sha_map.keys()),
    }
    feasibility_sha = sha256_of_obj(feasibility_data)
    
    # Create RunArtifact (persisted for ALLOW and BLOCK)
    artifact_id = create_run_id()
    
    if feasibility_data["decision"] == "BLOCK":
        # Persist blocked artifact (audit trail)
        artifact = create_blocked_artifact_for_violations(
            run_id=artifact_id,
            mode="art_studio_candidate",
            spec={"attachment_ids": list(attachment_sha_map.keys())},
            violations=[{"code": "FEASIBILITY_BLOCKED"}],
        )
    else:
        # Persist allowed artifact
        artifact = RunArtifact(
            run_id=artifact_id,
            status="OK",
            hashes=Hashes(feasibility_sha256=feasibility_sha),
            decision=RunDecision(
                risk_level="GREEN",
                score=85.0,
            ),
        )
        persist_run(artifact)
    
    # Return decision to customer (200 for ALLOW and BLOCK)
    return BindArtStudioCandidateResponse(
        artifact_id=artifact_id,
        decision=feasibility_data["decision"],
        feasibility_score=feasibility_data["score"],
        risk_level=feasibility_data["risk_level"],
        feasibility_sha256=feasibility_sha,
        attachment_sha256_map=attachment_sha_map,
    )
```

---

### 6. Workflow State Transition (Approval Gate)

**Location:** `app/rmos/api/rmos_workflow_router.py`

```python
@router.post("/approve", response_model=WorkflowSessionResponse)
def approve_session(req: ApproveRequest) -> WorkflowSessionResponse:
    """
    Customer/operator approval gate for AI-generated design.
    
    Transitions workflow from FEASIBILITY_READY → APPROVED.
    Creates immutable RunArtifact via WorkflowRunsBridge.
    
    Customer workflow:
    1. AI generates design → attachment uploaded
    2. Feasibility verified → artifact created (ALLOW/BLOCK)
    3. Operator reviews → approves or rejects
    4. Approved → proceed to toolpath generation
    """
    session = STORE.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate current state (must have feasibility)
    if session.state != WorkflowState.FEASIBILITY_READY:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve from state {session.state}"
        )
    
    # Execute approval transition
    updated_session = approve(session, req.actor, req.note)
    
    # Persist state change
    STORE.put(updated_session)
    
    # Create RunArtifact via bridge (immutable audit trail)
    bridge = get_workflow_runs_bridge()
    run_id = bridge.on_approval(
        session_id=updated_session.session_id,
        actor=req.actor,
        note=req.note,
        snapshot=to_comparable_snapshot(updated_session),
    )
    
    # Customer proceeds to toolpath generation
    return WorkflowSessionResponse(
        session_id=updated_session.session_id,
        state=updated_session.state.value,
        run_id=run_id,
        next_step="request_toolpaths",
    )
```

---

## Customer Data Flow Summary

### Input → Output Transformation

| Stage                  | Customer Input                                  | AI Processing                              | Customer Output                           |
| ---------------------- | ----------------------------------------------- | ------------------------------------------ | ----------------------------------------- |
| **1. Context**         | Material, tool, machine specs                   | Constraint extraction                      | RmosContext object                        |
| **2. Generation**      | Design intent (ring count, complexity)          | AI prompt construction → LLM call          | RosetteParamSpec JSON                     |
| **3. Attachment**      | JSON design + SHA256                            | Content-addressed storage                  | Attachment ID (sha256)                    |
| **4. Binding**         | Attachment IDs                                  | Feasibility scoring                        | Decision (ALLOW/BLOCK) + RunArtifact      |
| **5. Approval**        | Operator review                                 | State transition                           | Approved artifact + Run ID                |
| **6. Toolpaths** | Approved design                                 | CAM engine                                 | G-code (manufacturing instructions)       |

---

## Key Design Principles

### 1. User Creativity Invariant
**"AI should not design a rosette or guitar — it should take prompts at the user's creativity."**

- Customer provides constraints (material, dimensions, intent)
- AI explores design space within those constraints
- Domain layer (`app/rmos/ai/*`) constructs prompts
- Platform layer (`app/ai/*`) is goal-agnostic transport

### 2. Blocked Persistence Policy
**"Persist even BLOCKED. Always."**

- ALLOW candidate → RunArtifact with status=OK
- BLOCK candidate → RunArtifact with status=BLOCKED
- Creates audit trail for all decisions
- Enables drift-gate overrides ("accept anyway")
- Supports deterministic replay/diff

### 3. Content-Addressed Storage
**"SHA256 IS the attachment ID."**

- Prevents corruption (mismatch = fail)
- Automatic deduplication (same content = same ID)
- Immutable artifact trail (can't modify, only append)
- Supports cryptographic verification

---

## API Endpoints Summary

### Customer-Facing APIs

```
┌─────────────────────────────────────────────────────────────┐
│ AI GENERATION                                                │
├─────────────────────────────────────────────────────────────┤
│ POST /api/rmos/ai/constraint-search                         │
│   → Input: context + search_budget                           │
│   → Output: best_design (RosetteParamSpec JSON)             │
│                                                               │
│ POST /api/rmos/ai/quick-check                               │
│   → Fast preview (5 attempts, 5 seconds)                     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ ATTACHMENT STORAGE                                           │
├─────────────────────────────────────────────────────────────┤
│ POST /api/runs/{run_id}/attachments                         │
│   → Input: b64 payload + sha256 + metadata                  │
│   → Output: attachment_id (content-addressed)                │
│                                                               │
│ GET /api/runs/{run_id}/attachments                          │
│   → List all attachments for run                             │
│                                                               │
│ GET /api/runs/{run_id}/attachments/{sha256}                 │
│   → Download attachment blob                                 │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ FEASIBILITY BINDING                                          │
├─────────────────────────────────────────────────────────────┤
│ POST /api/runs/{run_id}/artifacts/bind-art-studio-candidate │
│   → Input: attachment_ids + operator_notes                   │
│   → Output: decision (ALLOW/BLOCK) + artifact_id            │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ WORKFLOW PROGRESSION                                         │
├─────────────────────────────────────────────────────────────┤
│ POST /api/rmos/workflow/approve                             │
│   → Operator approves AI-generated design                    │
│   → Creates immutable RunArtifact                            │
│   → Proceeds to toolpath generation                          │
│                                                               │
│ POST /api/rmos/workflow/reject                              │
│   → Operator rejects design                                  │
│   → Customer returns to generation or manual editing         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Status

| Component                        | Status | Location                                   |
| -------------------------------- | ------ | ------------------------------------------ |
| AI Generation API                | ✅      | `app/rmos/api_ai_routes.py`                |
| Search Loop                      | ✅      | `app/rmos/ai_search.py`                    |
| Domain Generator Factory         | ✅      | `app/rmos/ai/generators.py`                |
| Attachment Upload                | ✅      | `app/rmos/runs_v2/api_runs.py`             |
| Art Studio Binding               | ✅      | `app/rmos/runs_v2/api_runs.py`             |
| Workflow State Machine           | ✅      | `app/workflow/state_machine.py`            |
| Workflow API                     | ✅      | `app/rmos/api/rmos_workflow_router.py`     |
| Content-Addressed Storage        | ✅      | `app/rmos/runs_v2/attachments.py`          |
| Feasibility Scorer (Real Engine) | ⏳      | TODO: Replace mock in binding route       |
| UI Integration                   | ⏳      | Frontend needs attachment upload + binding |

---

## Next Steps for Production Readiness

1. **Replace Mocked Feasibility Check**
   - Location: `app/rmos/runs_v2/api_runs.py` line ~716
   - Current: Returns ALLOW with score=0.85
   - Needed: Real engine that loads geometry, checks constraints

2. **Frontend Integration**
   - Add attachment upload widget after AI generation
   - Display binding decision (ALLOW/BLOCK) to operator
   - Show feasibility score + risk level in UI

3. **Monitoring & Observability**
   - Track AI generation success rates
   - Monitor blocked artifact rates
   - Alert on high BLOCK percentages

4. **Load Testing**
   - Concurrent AI searches with budget limits
   - Attachment upload performance (large SVGs)
   - Binding route throughput

---

## Document Version
- **Version:** 1.0
- **Date:** 2025-12-22
- **Author:** AI Workflow Integration Team
- **Status:** Production Implementation
