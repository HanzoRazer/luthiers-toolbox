#!/usr/bin/env python3
"""
Example: Complete guitar design and cost estimation workflow.

This example demonstrates the full capabilities of the Luthier's Toolbox,
from design through cost estimation.
"""

from luthiers_toolbox.cad import GuitarBody, GuitarNeck, Fretboard
from luthiers_toolbox.cam import ToolpathGenerator, GCodeGenerator, GCodeExporter
from luthiers_toolbox.costing import CostEstimator
from luthiers_toolbox.tonewood import TonewoodAnalyzer


def main():
    print("=" * 60)
    print("Luthier's Toolbox - Complete Workflow Example")
    print("=" * 60)

    # ========== PHASE 1: CAD DESIGN ==========
    print("\n" + "=" * 60)
    print("PHASE 1: CAD DESIGN")
    print("=" * 60)

    # Design body
    print("\n1. Designing guitar body...")
    body = GuitarBody(
        shape="stratocaster",
        scale_length=25.5,
        body_length=18.0,
        body_width=13.0,
        thickness=1.75,
    )
    print(f"   ✓ Body: {body.shape}")
    print(f"   Dimensions: {body.body_length}\" × {body.body_width}\" × {body.thickness}\"")

    # Design neck
    print("\n2. Designing neck...")
    neck = GuitarNeck(
        scale_length=25.5,
        frets=22,
        nut_width=1.65,
        profile="C",
    )
    print(f"   ✓ Neck: {neck.profile} profile")
    print(f"   Scale length: {neck.scale_length}\"")
    print(f"   Frets: {neck.frets}")

    # Design fretboard
    print("\n3. Designing fretboard...")
    fretboard = Fretboard(
        scale_length=25.5,
        frets=22,
        radius=9.5,
    )
    positions = fretboard.calculate_fret_positions()
    print(f"   ✓ Fretboard radius: {fretboard.radius}\"")
    print(f"   12th fret position: {positions[11]:.3f}\"")

    # ========== PHASE 2: TONEWOOD ANALYSIS ==========
    print("\n" + "=" * 60)
    print("PHASE 2: TONEWOOD ANALYSIS")
    print("=" * 60)

    analyzer = TonewoodAnalyzer()

    # Analyze wood combination
    print("\n1. Analyzing tonewood combination...")
    print("   Body: Mahogany")
    print("   Neck: Maple")
    print("   Fretboard: Rosewood")

    profile = analyzer.analyze_wood_combination(
        "mahogany", "maple", "rosewood"
    )

    if profile:
        print(f"\n   Overall character: {profile.overall_character}")
        print(f"   Bass: {profile.bass_response}")
        print(f"   Mids: {profile.midrange_response}")
        print(f"   Treble: {profile.treble_response}")
        print(f"   Sustain: {profile.sustain}")

    # Get recommendations for style
    print("\n2. Checking style recommendations...")
    recs = analyzer.recommend_for_style("rock")
    if recs:
        print(f"   Rock style recommendations:")
        print(f"   {recs.get('description', '')}")

    # ========== PHASE 3: CAM TOOLPATHS ==========
    print("\n" + "=" * 60)
    print("PHASE 3: CAM TOOLPATH GENERATION")
    print("=" * 60)

    print("\n1. Generating body profile toolpath...")
    toolpath_gen = ToolpathGenerator(stock_thickness=2.0)

    # Create profile toolpath from body outline
    outline_points = [(p.x, p.y) for p in body.get_outline()]
    profile_tp = toolpath_gen.generate_profile_toolpath(
        points=outline_points,
        depth=0.5,
        tool_diameter=0.25,
        feedrate=40.0,
        name="Body Profile",
    )
    print(f"   ✓ Profile toolpath: {len(profile_tp.points)} points")
    print(f"   Estimated time: {profile_tp.get_estimated_time():.1f} min")

    print("\n2. Generating neck pocket toolpath...")
    pocket_tp = toolpath_gen.generate_pocket_toolpath(
        bounds=(0, -1.5, 3, 1.5),  # Neck pocket area
        depth=0.625,  # 5/8" pocket depth
        tool_diameter=0.5,
        stepover=0.2,
        name="Neck Pocket",
    )
    print(f"   ✓ Pocket toolpath: {len(pocket_tp.points)} points")
    print(f"   Estimated time: {pocket_tp.get_estimated_time():.1f} min")

    # Export G-code
    print("\n3. Exporting G-code...")
    gcode_gen = GCodeGenerator(units="inches", spindle_speed=18000)
    exporter = GCodeExporter(gcode_gen)

    try:
        stats = exporter.export_with_stats(
            toolpath_gen.toolpaths,
            "/tmp/guitar_body.gcode"
        )
        print(f"   ✓ G-code exported: {stats['file']}")
        print(f"   Total toolpaths: {stats['toolpaths']}")
        print(f"   Estimated time: {stats['estimated_time_minutes']:.1f} min")
    except Exception as e:
        print(f"   Note: G-code export skipped ({e})")

    # ========== PHASE 4: COST ESTIMATION ==========
    print("\n" + "=" * 60)
    print("PHASE 4: COST ESTIMATION")
    print("=" * 60)

    estimator = CostEstimator()

    print("\n1. Estimating project costs...")
    project = estimator.estimate_guitar(
        body_wood="mahogany",
        neck_wood="maple",
        fretboard_wood="rosewood",
        hardware_level="standard",
        include_electronics=True,
        cnc_time_minutes=toolpath_gen.get_total_time(),
    )

    breakdown = project.get_breakdown()

    print(f"\n   Materials:  ${breakdown['materials']:>8.2f}")
    print(f"   Labor:      ${breakdown['labor']:>8.2f}")
    print(f"   Overhead:   ${breakdown['overhead']:>8.2f}")
    print(f"   " + "-" * 20)
    print(f"   TOTAL:      ${breakdown['total']:>8.2f}")

    # Show detailed breakdown
    print("\n2. Material breakdown:")
    detailed = project.get_detailed_breakdown()
    for mat in detailed['materials'][:5]:  # Show first 5 items
        print(f"   • {mat['name']}: ${mat['cost']:.2f}")

    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    print("\nThis example demonstrated:")
    print("  ✓ CAD design of body, neck, and fretboard")
    print("  ✓ Tonewood analysis and recommendations")
    print("  ✓ CAM toolpath generation and G-code export")
    print("  ✓ Complete cost estimation")
    print("\nNext steps:")
    print("  • Export body design to DXF: body.export_dxf('body.dxf')")
    print("  • Refine toolpaths for specific CNC machine")
    print("  • Adjust materials for budget or tonal goals")
    print("  • Generate detailed cut lists and assembly instructions")
    print("=" * 60)


if __name__ == "__main__":
    main()
