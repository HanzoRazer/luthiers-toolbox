"""
Command-line interface for Luthier's Toolbox.
"""

import click
from . import __version__
from .cad import GuitarBody, GuitarNeck, Fretboard
from .cam import ToolpathGenerator, GCodeGenerator, GCodeExporter
from .costing import CostEstimator
from .tonewood import TonewoodDatabase, TonewoodAnalyzer


@click.group()
@click.version_option(version=__version__)
def main():
    """
    Luthier's Toolbox - Parametric CAD/CAM suite for guitar makers.
    
    Design, cost, and machine guitars with integrated tools for CAD, CAM,
    costing, and tonewood analytics.
    """
    pass


@main.group()
def cad():
    """CAD design tools for guitar components."""
    pass


@cad.command("body")
@click.option("--shape", default="stratocaster", help="Body shape")
@click.option("--scale", default=25.5, help="Scale length in inches")
@click.option("--length", default=18.0, help="Body length in inches")
@click.option("--width", default=13.0, help="Body width in inches")
@click.option("--output", default="body.dxf", help="Output DXF file")
def design_body(shape, scale, length, width, output):
    """Design a guitar body."""
    try:
        body = GuitarBody(
            shape=shape,
            scale_length=scale,
            body_length=length,
            body_width=width,
        )
        body.export_dxf(output)
        click.echo(f"✓ Body design exported to {output}")
        click.echo(f"  Shape: {body.shape}")
        click.echo(f"  Dimensions: {length}\" × {width}\"")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cad.command("neck")
@click.option("--scale", default=25.5, help="Scale length in inches")
@click.option("--frets", default=22, help="Number of frets")
@click.option("--profile", default="C", help="Neck profile")
def design_neck(scale, frets, profile):
    """Design a guitar neck."""
    try:
        neck = GuitarNeck(
            scale_length=scale,
            frets=frets,
            profile=profile,
        )
        dims = neck.get_dimensions()
        click.echo(f"✓ Neck design created")
        click.echo(f"  Scale length: {scale}\"")
        click.echo(f"  Frets: {frets}")
        click.echo(f"  Profile: {profile}")
        click.echo(f"  Total length: {dims['total_length']:.2f}\"")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cad.command("fretboard")
@click.option("--scale", default=25.5, help="Scale length in inches")
@click.option("--frets", default=22, help="Number of frets")
@click.option("--radius", default=9.5, help="Fretboard radius in inches")
def design_fretboard(scale, frets, radius):
    """Design a fretboard with fret positions."""
    try:
        fb = Fretboard(
            scale_length=scale,
            frets=frets,
            radius=radius,
        )
        positions = fb.calculate_fret_positions()
        click.echo(f"✓ Fretboard design created")
        click.echo(f"  Scale length: {scale}\"")
        click.echo(f"  Frets: {frets}")
        click.echo(f"  Radius: {radius}\"")
        click.echo(f"\nFret positions from nut:")
        for i, pos in enumerate(positions[:12], 1):
            click.echo(f"    Fret {i:2d}: {pos:6.3f}\"")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@main.group()
def cam():
    """CAM toolpath generation and G-code export."""
    pass


@cam.command("generate")
@click.option("--operation", type=click.Choice(["profile", "pocket"]), required=True)
@click.option("--depth", default=0.5, help="Cutting depth in inches")
@click.option("--tool", default=0.25, help="Tool diameter in inches")
@click.option("--output", default="output.gcode", help="Output G-code file")
def generate_toolpath(operation, depth, tool, output):
    """Generate CNC toolpaths and G-code."""
    try:
        generator = ToolpathGenerator()

        if operation == "profile":
            # Example profile points
            points = [
                (0, 0),
                (5, 0),
                (5, 3),
                (0, 3),
            ]
            toolpath = generator.generate_profile_toolpath(
                points=points,
                depth=depth,
                tool_diameter=tool,
            )
        else:
            # Example pocket
            toolpath = generator.generate_pocket_toolpath(
                bounds=(0, 0, 5, 3),
                depth=depth,
                tool_diameter=tool,
            )

        # Export to G-code
        gcode_gen = GCodeGenerator()
        exporter = GCodeExporter(gcode_gen)
        stats = exporter.export_with_stats([toolpath], output)

        click.echo(f"✓ G-code exported to {output}")
        click.echo(f"  Operation: {operation}")
        click.echo(f"  Tool: {tool}\" diameter")
        click.echo(f"  Depth: {depth}\"")
        click.echo(f"  Estimated time: {stats['estimated_time_minutes']:.1f} min")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@main.group()
def costing():
    """Material and labor cost estimation."""
    pass


@costing.command("estimate")
@click.option("--body-wood", default="mahogany", help="Body wood species")
@click.option("--neck-wood", default="maple", help="Neck wood species")
@click.option("--fretboard-wood", default="rosewood", help="Fretboard wood species")
@click.option("--electronics/--no-electronics", default=True, help="Include electronics")
def estimate_guitar(body_wood, neck_wood, fretboard_wood, electronics):
    """Estimate the cost of building a guitar."""
    try:
        estimator = CostEstimator()
        project = estimator.estimate_guitar(
            body_wood=body_wood,
            neck_wood=neck_wood,
            fretboard_wood=fretboard_wood,
            include_electronics=electronics,
        )

        breakdown = project.get_breakdown()

        click.echo("✓ Cost Estimate for Electric Guitar Build")
        click.echo(f"\n  Body: {body_wood.title()}")
        click.echo(f"  Neck: {neck_wood.title()}")
        click.echo(f"  Fretboard: {fretboard_wood.title()}")
        click.echo(f"  Electronics: {'Yes' if electronics else 'No'}")
        click.echo(f"\n  Materials:  ${breakdown['materials']:.2f}")
        click.echo(f"  Labor:      ${breakdown['labor']:.2f}")
        click.echo(f"  Overhead:   ${breakdown['overhead']:.2f}")
        click.echo(f"  ─────────────────────")
        click.echo(f"  Total:      ${breakdown['total']:.2f}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@main.group()
def tonewood():
    """Tonewood database and analysis."""
    pass


@tonewood.command("list")
@click.option("--use", help="Filter by use (body, neck, fretboard)")
def list_woods(use):
    """List available tonewoods."""
    try:
        db = TonewoodDatabase()

        if use:
            woods = db.find_by_use(use)
            click.echo(f"✓ Tonewoods suitable for {use}:")
            for wood in woods:
                click.echo(f"  • {wood.name} - {wood.acoustics.tonal_character}")
        else:
            woods = db.list_woods()
            click.echo(f"✓ Available tonewoods ({len(woods)}):")
            for name in woods:
                wood = db.get_wood(name)
                click.echo(f"  • {wood.name} - {', '.join(wood.common_uses)}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@tonewood.command("analyze")
@click.option("--body", required=True, help="Body wood")
@click.option("--neck", required=True, help="Neck wood")
@click.option("--fretboard", required=True, help="Fretboard wood")
def analyze_combination(body, neck, fretboard):
    """Analyze a tonewood combination."""
    try:
        analyzer = TonewoodAnalyzer()
        profile = analyzer.analyze_wood_combination(body, neck, fretboard)

        if profile:
            click.echo("✓ Tonal Analysis")
            click.echo(profile.get_summary())
        else:
            click.echo("✗ One or more woods not found in database", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@tonewood.command("recommend")
@click.option("--style", required=True, help="Playing style (blues, rock, jazz, metal)")
def recommend_woods(style):
    """Get wood recommendations for a playing style."""
    try:
        analyzer = TonewoodAnalyzer()
        recs = analyzer.recommend_for_style(style)

        if recs:
            click.echo(f"✓ Recommendations for {style.title()}")
            click.echo(f"  {recs.get('description', '')}")
            click.echo(f"\n  Body: {', '.join([w.title() for w in recs.get('body', [])])}")
            click.echo(f"  Neck: {', '.join([w.title() for w in recs.get('neck', [])])}")
            click.echo(
                f"  Fretboard: {', '.join([w.title() for w in recs.get('fretboard', [])])}"
            )
        else:
            click.echo(f"✗ No recommendations for style: {style}", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


if __name__ == "__main__":
    main()
