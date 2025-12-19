#!/usr/bin/env python3
"""
Test DALL-E Integration

Run this locally with your OPENAI_API_KEY set:
    export OPENAI_API_KEY=sk-proj-...
    python test_dalle_advisory.py

This will:
1. Generate a guitar image via DALL-E
2. Store it as an AdvisoryAsset (not approved)
3. Show you the result
"""
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        print("Run: export OPENAI_API_KEY=sk-proj-...")
        return 1
    
    print(f"✓ OPENAI_API_KEY detected ({api_key[:20]}...)")
    
    # Import after path setup
    from _experimental.ai_graphics.image_transport import OpenAIImageTransport
    from _experimental.ai_graphics.image_providers import GuitarVisionEngine, ImageSize, ImageQuality
    from _experimental.ai_graphics.schemas.advisory_schemas import AdvisoryAsset, AdvisoryAssetType
    from _experimental.ai_graphics.advisory_store import AdvisoryAssetStore, compute_content_hash
    
    # Check transport health
    print("\n--- Transport Health Check ---")
    transport = OpenAIImageTransport()
    print(f"Configured: {transport.is_configured}")
    
    if transport.health_check():
        print("✓ OpenAI API reachable")
    else:
        print("✗ OpenAI API not reachable")
        return 1
    
    # Generate image
    print("\n--- Generating Image ---")
    prompt = "sunburst les paul gold hardware, professional product photography"
    print(f"Prompt: {prompt}")
    
    engine = GuitarVisionEngine()
    result = engine.generate(
        user_prompt=prompt,
        num_images=1,
        size=ImageSize.SQUARE_LG,
        quality=ImageQuality.STANDARD,
    )
    
    if not result.success:
        print(f"✗ Generation failed: {result.error}")
        return 1
    
    print(f"✓ Generated in {result.images[0].generation_time_ms:.0f}ms")
    print(f"  Cost: ${result.actual_cost:.4f}")
    print(f"  Provider: {result.request.provider.value}")
    
    # Get image bytes
    generated = result.images[0]
    if generated._result and generated._result.image_bytes:
        image_bytes = generated._result.image_bytes
    else:
        import base64
        image_bytes = base64.b64decode(generated.base64_data)
    
    print(f"  Image size: {len(image_bytes):,} bytes")
    
    # Create advisory asset
    print("\n--- Creating Advisory Asset ---")
    content_hash = compute_content_hash(image_bytes)
    
    asset = AdvisoryAsset(
        asset_type=AdvisoryAssetType.IMAGE,
        source="ai_graphics",
        provider=result.request.provider.value,
        model="dall-e-3",
        prompt=prompt,
        content_hash=content_hash,
        image_width=1024,
        image_height=1024,
        image_format="png",
        generation_time_ms=int(result.images[0].generation_time_ms),
        cost_usd=result.actual_cost,
        reviewed=False,
        approved_for_workflow=False,
    )
    
    # Save to store
    store = AdvisoryAssetStore()
    store.save_asset(asset, content=image_bytes)
    
    print(f"✓ Asset created: {asset.asset_id}")
    print(f"  Approved: {asset.approved_for_workflow}")
    print(f"  Content URI: {asset.content_uri}")
    
    # Verify retrieval
    loaded = store.get_asset(asset.asset_id)
    if loaded:
        print(f"✓ Asset retrieved successfully")
        print(f"  Pending review: {not loaded.reviewed}")
    
    # Save image locally for viewing
    output_path = f"generated_{asset.asset_id}.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"\n✓ Image saved to: {output_path}")
    
    print("\n--- Summary ---")
    print(f"Asset ID: {asset.asset_id}")
    print(f"Status: PENDING REVIEW (approved_for_workflow=False)")
    print(f"To approve: POST /api/advisory/assets/{asset.asset_id}/review")
    print(f'  Body: {{"approved": true, "reviewer": "your_name"}}')
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
