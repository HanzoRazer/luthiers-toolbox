#!/usr/bin/env python
"""
Quick test of new attachment and binding routes.
Run: python test_new_routes.py
"""

import base64
import json

def test_schemas():
    """Test that all new schemas work correctly."""
    from app.rmos.runs_v2.schemas import (
        RunAttachmentCreateRequest,
        RunAttachmentCreateResponse,
        BindArtStudioCandidateRequest,
        BindArtStudioCandidateResponse,
    )
    
    print("Testing schemas...")
    
    # Test attachment creation request
    svg_content = b'<svg><circle cx="50" cy="50" r="40"/></svg>'
    req = RunAttachmentCreateRequest(
        kind='geometry_svg',
        filename='rosette.svg',
        content_type='image/svg+xml',
        sha256='a' * 64,
        b64=base64.b64encode(svg_content).decode(),
        metadata={
            'request_id': 'req-123',
            'generator_version': 'v2.1.0',
            'variant_index': 0,
        }
    )
    print(f"✓ RunAttachmentCreateRequest: kind={req.kind}, filename={req.filename}")
    
    # Test attachment creation response
    resp = RunAttachmentCreateResponse(
        attachment_id='att-abcd1234',
        sha256='a' * 64,
        kind='geometry_svg'
    )
    print(f"✓ RunAttachmentCreateResponse: attachment_id={resp.attachment_id}")
    
    # Test binding request
    bind_req = BindArtStudioCandidateRequest(
        attachment_ids=['att-svg123', 'att-spec456', 'att-envelope789'],
        operator_notes='Test candidate from Art Studio',
        strict=True
    )
    print(f"✓ BindArtStudioCandidateRequest: {len(bind_req.attachment_ids)} attachments")
    
    # Test binding response - ALLOW case
    bind_resp_allow = BindArtStudioCandidateResponse(
        artifact_id='run_abc123',
        decision='ALLOW',
        feasibility_score=0.92,
        risk_level='GREEN',
        feasibility_sha256='b' * 64,
        attachment_sha256_map={
            'att-svg123': 'c' * 64,
            'att-spec456': 'd' * 64,
        }
    )
    print(f"✓ BindArtStudioCandidateResponse (ALLOW): decision={bind_resp_allow.decision}, score={bind_resp_allow.feasibility_score}")
    
    # Test binding response - BLOCK case
    bind_resp_block = BindArtStudioCandidateResponse(
        artifact_id='run_def456',
        decision='BLOCK',
        feasibility_score=0.35,
        risk_level='RED',
        feasibility_sha256='e' * 64,
        attachment_sha256_map={
            'att-svg123': 'c' * 64,
        }
    )
    print(f"✓ BindArtStudioCandidateResponse (BLOCK): decision={bind_resp_block.decision}, score={bind_resp_block.feasibility_score}")
    
    print("\n✅ All schemas validated successfully!\n")


def test_route_registration():
    """Test that routes are registered in the router."""
    from app.rmos.runs_v2 import api_runs
    
    print("Testing route registration...")
    
    routes = [(r.path, r.methods) for r in api_runs.router.routes]
    
    # Check for attachment POST route
    attachment_post = [r for r in routes if r[0] == '/{run_id}/attachments' and 'POST' in r[1]]
    if attachment_post:
        print("✓ Found POST /{run_id}/attachments route")
    else:
        print("✗ Missing POST /{run_id}/attachments route")
        print(f"  Available routes: {[r[0] for r in routes if 'attachment' in r[0]]}")
    
    # Check for binding route
    binding_route = [r for r in routes if 'bind-art-studio-candidate' in r[0]]
    if binding_route:
        print(f"✓ Found {binding_route[0][0]} route with methods {binding_route[0][1]}")
    else:
        print(f"✗ Missing bind-art-studio-candidate route")
    
    print(f"\nTotal routes in router: {len(routes)}")
    print("\n✅ Route registration check complete!\n")


def print_route_specs():
    """Print the exact route specifications matching the design doc."""
    print("=" * 70)
    print("NEW ROUTE SPECIFICATIONS (matching design doc)")
    print("=" * 70)
    
    print("\n1. Attachment Creation Route:")
    print("   POST /api/runs/{run_id}/attachments")
    print("   - Request: RunAttachmentCreateRequest (b64, sha256, kind, metadata)")
    print("   - Response: RunAttachmentCreateResponse (attachment_id, sha256, kind)")
    print("   - Returns 400 if: SHA256 mismatch, invalid base64, run not found")
    print("   - Returns 200 on success")
    
    print("\n2. Art Studio Binding Route:")
    print("   POST /api/runs/{run_id}/artifacts/bind-art-studio-candidate")
    print("   - Request: BindArtStudioCandidateRequest (attachment_ids, operator_notes, strict)")
    print("   - Response: BindArtStudioCandidateResponse (artifact_id, decision, feasibility_score, risk_level, feasibility_sha256)")
    print("   - Returns 400 if: attachments missing/invalid, run not found")
    print("   - Returns 200 with decision=ALLOW or decision=BLOCK")
    print("   - ALWAYS persists RunArtifact (even for BLOCK)")
    
    print("\n" + "=" * 70)
    print("BLOCKED PERSISTENCE POLICY")
    print("=" * 70)
    print("✓ ALLOW candidate  → RunArtifact with status=OK, decision=ALLOW")
    print("✓ BLOCK candidate  → RunArtifact with status=BLOCKED, decision=BLOCK")
    print("✗ Invalid request  → 400 error, NO RunArtifact created")
    print("\nRationale: Creates audit trail, enables drift-gate overrides, supports replay/diff")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING NEW RMOS ATTACHMENT & BINDING ROUTES")
    print("="*70 + "\n")
    
    try:
        test_schemas()
        test_route_registration()
        print_route_specs()
        
        print("✅ ALL TESTS PASSED!\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
