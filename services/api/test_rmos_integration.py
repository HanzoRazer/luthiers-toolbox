"""Quick test of RMOS + rosette_calc integration."""
from app.rmos.feasibility_scorer import score_design_feasibility, _check_rosette_channel
from app.rmos.api_contracts import RmosContext


class MockDesign:
    outer_diameter_mm = 100.0
    inner_diameter_mm = 20.0
    ring_count = 3
    pattern_type = 'herringbone'


if __name__ == '__main__':
    design = MockDesign()
    ctx = RmosContext(
        material_id='maple',
        tool_id='end_mill_6mm',
        tool_diameter_mm=6.0
    )

    # Test channel check
    channel = _check_rosette_channel(design, ctx)
    print('=== Rosette Channel Check ===')
    print(f'  Score: {channel.get("score")}')
    print(f'  Width: {channel.get("channel_width_mm")}mm')
    print(f'  Depth: {channel.get("channel_depth_mm")}mm')
    print(f'  Warning: {channel.get("warning")}')

    # Test full feasibility
    print()
    result = score_design_feasibility(design, ctx)
    print('=== Full Feasibility Result ===')
    print(f'  Score: {result.score}')
    print(f'  Risk: {result.risk_bucket}')
    print(f'  Efficiency: {result.efficiency}%')
    print(f'  Est. Cut Time: {result.estimated_cut_time_seconds}s')
    print(f'  Calculator Results: {list(result.calculator_results.keys())}')
    
    # Check rosette_channel is in results
    if 'rosette_channel' in result.calculator_results:
        print('  ✓ rosette_calc integrated into feasibility scoring')
    else:
        print('  ✗ rosette_calc NOT in calculator results')
