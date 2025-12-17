# Extracted Code from Two Governance Documents
**Date:** December 17, 2025

## Source Documents

| Document | Lines | Purpose |
|----------|-------|---------|
| `Patch_Add_RMOS_Feasibility_Toolpaths_routers_.docx` | 1,070 | Tactical router wiring |
| `CNC_Saw_Labs__single_author_bidirectional_workflows_.docx` | 3,671 | Strategic governance backbone |

## File Inventory

### From Patch Document (5 files, 633 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `backend/rmos/api/rmos_toolpaths_router.py` | 245 | POST /api/rmos/toolpaths with safety blocking |
| `backend/rmos/api/rmos_feasibility_router.py` | 108 | POST /api/rmos/feasibility canonical endpoint |
| `backend/ai_graphics/llm_client_image_gen_patch.py` | 164 | OpenAI image generation method |
| `main_py.patch` | 29 | Unified diff for main.py router wiring |
| `tests/test_db_migrations.py` | 87 | Migration verification tests |

### From CNC Saw Labs Document (27 files, 2,775 lines)

#### Workflow State Machine
| File | Lines | Purpose |
|------|-------|---------|
| `backend/workflow/state_machine.py` | 474 | Basic workflow controller |
| `backend/workflow/state_machine_v2.py` | 512 | Artifact-driven version |
| `backend/workflow/session_store.py` | 26 | In-memory session storage |

#### Database Layer
| File | Lines | Purpose |
|------|-------|---------|
| `backend/db/base.py` | 5 | SQLAlchemy declarative base |
| `backend/db/session.py` | 21 | DB session management |
| `backend/db/migrate.py` | 165 | Migration runner |
| `backend/workflow/db/models.py` | 31 | WorkflowSession ORM model |
| `backend/workflow/db/store.py` | 75 | DB-backed session store |

#### RMOS Integration
| File | Lines | Purpose |
|------|-------|---------|
| `backend/rmos/engine.py` | 60 | RMOS engine protocol |
| `backend/rmos/hashing.py` | 20 | Deterministic hashing |
| `backend/rmos/impl.py` | 122 | Real RMOS adapter stub |
| `backend/rmos/run_artifacts/index.py` | 116 | Artifact indexing/query |

#### Routers
| File | Lines | Purpose |
|------|-------|---------|
| `backend/routers/run_artifacts_router.py` | 137 | /api/runs/* endpoints |
| `backend/routers/workflow_router.py` | 49 | In-memory workflow API |
| `backend/routers/workflow_router_db.py` | 69 | DB-backed workflow API |
| `backend/routers/rmos_workflow_router.py` | 95 | RMOS workflow integration |

#### Frontend (Vue)
| File | Lines | Purpose |
|------|-------|---------|
| `frontend/components/runArtifacts/RunArtifactPanel.vue` | 170 | Artifact list/detail panel |
| `frontend/components/runArtifacts/RunDiffViewer.vue` | 71 | Side-by-side diff view |
| `frontend/pages/RunArtifactsPage.vue` | 14 | Page wrapper |

#### Tests (8 files)
| File | Lines | Purpose |
|------|-------|---------|
| `tests/test_run_artifacts_e2e.py` | 107 | Artifact CRUD tests |
| `tests/test_run_artifacts_toolpaths_e2e.py` | 117 | Toolpath artifact tests |
| `tests/test_toolpaths_with_approval_e2e.py` | 69 | Approval flow tests |
| `tests/test_db_backed_approval_flow_e2e.py` | 55 | DB persistence tests |
| `tests/test_db_migrations.py` | 57 | Migration tests |
| `tests/test_rmos_artifact_wiring_e2e.py` | 61 | RMOS integration tests |
| `tests/test_rmos_hashing_and_versions.py` | 58 | Hash/version tests |
| `tests/fake_rmos_engine.py` | 19 | Test double |

## Key Governance Invariants

These documents enforce:
1. **No toolpaths without feasibility** — State machine blocks
2. **No bypass of RED** — Hard stop on RED risk level
3. **Server-side feasibility mandatory** — Never trust client
4. **Every action produces artifact** — Full audit trail

## Integration Order

1. Apply `main_py.patch` to wire routers
2. Deploy `state_machine.py` (choose v1 or v2)
3. Deploy RMOS routers + run_artifacts
4. Deploy DB layer (optional, can use in-memory first)
5. Deploy Vue components
6. Run tests

## Totals

- **32 files**
- **3,408 lines**
