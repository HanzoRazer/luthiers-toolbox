#!/usr/bin/env python3
"""
archtop_pipeline.py

Complete pipeline from measurement to mode prediction:
1. CSV points -> Contours + Stiffness Map
2. Stiffness Map -> Mode shapes + Frequencies

Usage:
python archtop_pipeline.py --points sample_top_points.csv --out-prefix my_guitar --E 11.0 --thickness 4.0
"""

import subprocess
import argparse
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    parser = argparse.ArgumentParser(description="Complete archtop analysis pipeline")
    parser.add_argument("--points", required=True, help="CSV with x,y,height (mm)")
    parser.add_argument("--out-prefix", required=True, help="Output prefix for all files")
    parser.add_argument("--E", type=float, required=True, help="Young's modulus (GPa)")
    parser.add_argument("--thickness", type=float, required=True, help="Plate thickness (mm)")
    parser.add_argument("--levels", default="0,1,2,3,4,5", help="Contour levels (mm)")
    parser.add_argument("--density", type=float, default=450, help="Wood density (kg/m³)")
    parser.add_argument("--res", type=float, default=2.0, help="Grid resolution (mm)")
    parser.add_argument("--num-modes", type=int, default=6, help="Number of modes to compute")
    
    args = parser.parse_args()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     COMPLETE ARCHTOP ANALYSIS PIPELINE                       ║
    ║     Geometry → Stiffness → Modes → Frequencies              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Generate contours and stiffness map
    step1_cmd = [
        sys.executable, "archtop_surface_tools.py", "csv",
        "--in", args.points,
        "--levels", args.levels,
        "--res", str(args.res),
        "--out-prefix", args.out_prefix,
        "--E", str(args.E),
        "--thickness", str(args.thickness),
        "--alpha", "1.0",
        "--Lref", "250"
    ]
    
    if not run_command(step1_cmd, "Generating contours and stiffness map"):
        sys.exit(1)
    
    # Step 2: Modal analysis from stiffness map
    stiffness_map = f"{args.out_prefix}_stiffness_map.csv"
    step2_cmd = [
        sys.executable, "archtop_modal_analysis.py",
        "--stiffness-map", stiffness_map,
        "--out-prefix", f"{args.out_prefix}_modal",
        "--density", str(args.density),
        "--thickness", str(args.thickness),
        "--num-modes", str(args.num_modes)
    ]
    
    if not run_command(step2_cmd, "Modal analysis from stiffness map"):
        sys.exit(1)
    
    print("\n" + "🎸" * 30)
    print("PIPELINE COMPLETE! Your archtop is now analyzed.")
    print("🎸" * 30)
    print(f"\nOutput files:")
    print(f"  Contours: {args.out_prefix}_Contours.dxf/svg/png")
    print(f"  Stiffness map: {args.out_prefix}_stiffness_map.csv")
    print(f"  Mode shapes: {args.out_prefix}_modal_modes.png")
    print(f"  Frequencies: {args.out_prefix}_modal_frequencies.json")
    print(f"  Animations: {args.out_prefix}_modal_mode_*_animation.gif")

if __name__ == "__main__":
    main()
