"""
tap_tone_pi.bending — Static bending MOE/EI measurement.

Migrated from: modes/bending_rig/

Modules:
    merge_and_moe: Merge load/displacement streams → MOE calculation
    plot_f_vs_d: Force vs displacement visualization

Example:
    python -m tap_tone_pi.bending.merge_and_moe \\
        --load load_series.json --disp displacement_series.json \\
        --out-dir ./out/rig --method 3point --span 400 --width 20 --thickness 3.0
"""
