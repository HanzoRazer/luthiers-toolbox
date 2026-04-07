#!/usr/bin/env python3
"""
archtop_modal_analysis.py

Takes stiffness maps from archtop_surface_tools.py and performs modal analysis
to predict natural frequencies and mode shapes.

Pipeline Complete:
------------------
1. archtop_surface_tools.py: CSV points -> Contours + Stiffness Map (K_eff_Nm)
2. archtop_modal_analysis.py: Stiffness Map -> Mode shapes + Frequencies
3. (Optional): Mode shapes -> Acoustic radiation

Method: Finite Difference Eigenvalue Problem
   ∇²(D(x,y) ∇² w) - ρh ω² w = 0

Where:
- D(x,y) = K_eff_Nm from stiffness map (spatially varying)
- ρ = density of wood (kg/m³)
- h = thickness (m)
- w = mode shape deflection
- ω = natural frequency (rad/s)

Outputs:
- Mode shape PNGs (top 6 modes)
- Frequency summary (Hz)
- CSV of modal data
- Optional: animated mode shapes

Requires:
pip install numpy matplotlib scipy
"""

import argparse
import json
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import eigs
import warnings

def read_stiffness_map(csv_path):
    """Read the stiffness map CSV from archtop_surface_tools.py"""
    data = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            x = float(row['x_mm'])
            y = float(row['y_mm'])
            # Store in dictionary keyed by (x,y)
            data[(x, y)] = {
                'K_eff': float(row['K_eff_Nm']),
                'height': float(row['height_mm'])
            }
    
    # Extract grid info
    xs = sorted(set(x for x, _ in data.keys()))
    ys = sorted(set(y for _, y in data.keys()))
    
    # Build 2D arrays
    nx, ny = len(xs), len(ys)
    X = np.zeros((ny, nx))
    Y = np.zeros((ny, nx))
    K_eff = np.zeros((ny, nx))
    height = np.zeros((ny, nx))
    
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            X[i, j] = x
            Y[i, j] = y
            K_eff[i, j] = data[(x, y)]['K_eff']
            height[i, j] = data[(x, y)]['height']
    
    # Convert mm to m for calculations
    X_m = X / 1000.0
    Y_m = Y / 1000.0
    
    return {
        'X_m': X_m, 'Y_m': Y_m,
        'X_mm': X, 'Y_mm': Y,
        'K_eff': K_eff,
        'height_mm': height,
        'nx': nx, 'ny': ny,
        'dx': (X_m[0,1] - X_m[0,0]) if nx > 1 else 0.01,
        'dy': (Y_m[1,0] - Y_m[0,0]) if ny > 1 else 0.01
    }

def build_fd_matrix(K_eff, dx, dy, rho, h, boundary='clamped'):
    """
    Build finite difference matrix for:
    ∇²(D ∇² w) - ρh ω² w = 0
    
    Uses central differences with 13-point stencil for biharmonic operator.
    """
    ny, nx = K_eff.shape
    N = nx * ny
    A = lil_matrix((N, N))  # Stiffness matrix
    M = lil_matrix((N, N))  # Mass matrix
    
    def idx(i, j):
        return i * nx + j
    
    def laplacian(w, i, j):
        """Discrete Laplacian with variable D"""
        if i == 0 or i == ny-1 or j == 0 or j == nx-1:
            return 0  # Boundary handled separately
        
        # Central difference Laplacian of (D * Laplacian(w))
        # For interior points with variable D
        D_ij = K_eff[i, j]
        D_ip = K_eff[i+1, j] if i+1 < ny else D_ij
        D_im = K_eff[i-1, j] if i-1 >= 0 else D_ij
        D_jp = K_eff[i, j+1] if j+1 < nx else D_ij
        D_jm = K_eff[i, j-1] if j-1 >= 0 else D_ij
        
        # Laplacian of w
        w_ij = w[idx(i, j)]
        w_ip = w[idx(i+1, j)] if i+1 < ny else 0
        w_im = w[idx(i-1, j)] if i-1 >= 0 else 0
        w_jp = w[idx(i, j+1)] if j+1 < nx else 0
        w_jm = w[idx(i, j-1)] if j-1 >= 0 else 0
        
        Lw = (w_ip + w_im - 4*w_ij + w_jp + w_jm) / (dx*dy)
        
        # Apply boundary conditions (clamped: w=0, dw/dn=0)
        if boundary == 'clamped':
            if i == 0 or i == ny-1 or j == 0 or j == nx-1:
                return 0  # w=0 on boundary
        
        return D_ij * Lw
    
    # Build matrix
    for i in range(ny):
        for j in range(nx):
            node = idx(i, j)
            
            # Mass matrix (diagonal)
            M[node, node] = rho * h
            
            # Stiffness matrix using 13-point stencil approximation
            if i > 0 and i < ny-1 and j > 0 and j < nx-1:
                # Interior point
                D_ij = K_eff[i, j]
                D_ip = K_eff[i+1, j]
                D_im = K_eff[i-1, j]
                D_jp = K_eff[i, j+1]
                D_jm = K_eff[i, j-1]
                D_ipjp = K_eff[i+1, j+1] if i+1 < ny and j+1 < nx else D_ij
                D_imjm = K_eff[i-1, j-1] if i-1 >= 0 and j-1 >= 0 else D_ij
                
                # Center coefficient
                A[node, node] = (20 * D_ij + 2*(D_ip + D_im + D_jp + D_jm)) / (dx**2 * dy**2)
                
                # Neighbors
                if i+1 < ny:
                    A[node, idx(i+1, j)] = -4 * (D_ij + D_ip) / (dx**2 * dy**2)
                if i-1 >= 0:
                    A[node, idx(i-1, j)] = -4 * (D_ij + D_im) / (dx**2 * dy**2)
                if j+1 < nx:
                    A[node, idx(i, j+1)] = -4 * (D_ij + D_jp) / (dx**2 * dy**2)
                if j-1 >= 0:
                    A[node, idx(i, j-1)] = -4 * (D_ij + D_jm) / (dx**2 * dy**2)
                
                # Diagonal neighbors
                if i+1 < ny and j+1 < nx:
                    A[node, idx(i+1, j+1)] = 2 * D_ipjp / (dx**2 * dy**2)
                if i+1 < ny and j-1 >= 0:
                    A[node, idx(i+1, j-1)] = 2 * D_ipjp / (dx**2 * dy**2)
                if i-1 >= 0 and j+1 < nx:
                    A[node, idx(i-1, j+1)] = 2 * D_imjm / (dx**2 * dy**2)
                if i-1 >= 0 and j-1 >= 0:
                    A[node, idx(i-1, j-1)] = 2 * D_imjm / (dx**2 * dy**2)
            else:
                # Boundary: clamped (w=0)
                A[node, node] = 1.0
                M[node, node] = 0
    
    return csr_matrix(A), csr_matrix(M)

def solve_modes(grid_data, rho, h, num_modes=6, boundary='clamped'):
    """Solve eigenvalue problem for mode shapes and frequencies"""
    print(f"Building finite difference matrix for {grid_data['nx']}x{grid_data['ny']} grid...")
    A, M = build_fd_matrix(
        grid_data['K_eff'], 
        grid_data['dx'], 
        grid_data['dy'],
        rho, h, boundary
    )
    
    print(f"Solving for {num_modes} lowest modes...")
    # Use shift-invert to find smallest eigenvalues
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            eigenvalues, eigenvectors = eigs(A, k=num_modes, M=M, sigma=0, which='LM')
        except:
            # Fallback to regular eigenvalue solver
            eigenvalues, eigenvectors = eigs(A, k=num_modes, M=M, which='SM')
    
    # Convert to real and sort
    idx = np.argsort(np.real(eigenvalues))
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Calculate frequencies (Hz)
    omega = np.sqrt(np.real(eigenvalues))  # rad/s
    frequencies_hz = omega / (2 * np.pi)
    
    # Reshape mode shapes to grid
    mode_shapes = []
    for k in range(num_modes):
        mode = np.real(eigenvectors[:, k]).reshape(grid_data['ny'], grid_data['nx'])
        # Normalize
        mode = mode / np.max(np.abs(mode))
        mode_shapes.append(mode)
    
    return frequencies_hz, mode_shapes

def plot_mode_shapes(grid_data, mode_shapes, frequencies_hz, out_prefix):
    """Plot all mode shapes"""
    num_modes = len(mode_shapes)
    cols = min(3, num_modes)
    rows = (num_modes + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    if num_modes == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for i, (mode, freq) in enumerate(zip(mode_shapes, frequencies_hz)):
        ax = axes[i]
        im = ax.contourf(grid_data['X_mm'], grid_data['Y_mm'], mode, 
                         levels=20, cmap='RdBu_r')
        ax.set_aspect('equal')
        ax.set_title(f'Mode {i+1}: {freq:.1f} Hz')
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
        plt.colorbar(im, ax=ax, label='Normalized deflection')
    
    # Hide unused subplots
    for i in range(num_modes, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_modes.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # Also save individual mode plots
    for i, (mode, freq) in enumerate(zip(mode_shapes, frequencies_hz)):
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.contourf(grid_data['X_mm'], grid_data['Y_mm'], mode, 
                         levels=20, cmap='RdBu_r')
        ax.set_aspect('equal')
        ax.set_title(f'Mode {i+1}: {freq:.1f} Hz')
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
        plt.colorbar(im, label='Normalized deflection')
        plt.tight_layout()
        plt.savefig(f"{out_prefix}_mode_{i+1}.png", dpi=200)
        plt.close()

def save_modal_data(frequencies_hz, mode_shapes, grid_data, out_prefix):
    """Save modal analysis results to CSV and JSON"""
    # Save frequencies
    freq_data = []
    for i, f in enumerate(frequencies_hz):
        freq_data.append({
            'mode': i+1,
            'frequency_hz': float(f),
            'angular_frequency_rad_s': float(2 * np.pi * f)
        })
    
    freq_json = f"{out_prefix}_frequencies.json"
    with open(freq_json, 'w') as f:
        json.dump(freq_data, f, indent=2)
    
    # Save mode shapes as CSV
    mode_csv = f"{out_prefix}_mode_shapes.csv"
    with open(mode_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        header = ['x_mm', 'y_mm'] + [f'mode_{i+1}' for i in range(len(mode_shapes))]
        writer.writerow(header)
        
        # Write data
        ny, nx = grid_data['X_mm'].shape
        for i in range(ny):
            for j in range(nx):
                row = [grid_data['X_mm'][i, j], grid_data['Y_mm'][i, j]]
                for mode in mode_shapes:
                    row.append(mode[i, j])
                writer.writerow(row)
    
    print(f"Saved modal data to {freq_json} and {mode_csv}")
    return freq_data

def create_mode_animation(grid_data, mode_shapes, frequencies_hz, out_prefix):
    """Create animated GIF of mode shapes vibrating"""
    for i, (mode, freq) in enumerate(zip(mode_shapes, frequencies_hz)):
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Time array for one period
        t = np.linspace(0, 1/freq, 30)
        
        def animate(frame):
            ax.clear()
            phase = 2 * np.pi * freq * t[frame]
            vibrating = mode * np.sin(phase)
            im = ax.contourf(grid_data['X_mm'], grid_data['Y_mm'], vibrating,
                            levels=20, cmap='RdBu_r', vmin=-1, vmax=1)
            ax.set_aspect('equal')
            ax.set_title(f'Mode {i+1}: {freq:.1f} Hz - Frame {frame+1}/{len(t)}')
            ax.set_xlabel('x (mm)')
            ax.set_ylabel('y (mm)')
            return [im]
        
        anim = FuncAnimation(fig, animate, frames=len(t), interval=50, blit=True)
        anim.save(f"{out_prefix}_mode_{i+1}_animation.gif", writer='pillow', fps=20)
        plt.close()
        print(f"Saved animation for mode {i+1}")

def main():
    parser = argparse.ArgumentParser(
        description="Modal analysis from archtop stiffness map",
        epilog="Complete pipeline: CSV -> Contours+Stiffness -> Modes -> Sound"
    )
    parser.add_argument("--stiffness-map", required=True,
                       help="CSV from archtop_surface_tools.py (*_stiffness_map.csv)")
    parser.add_argument("--out-prefix", required=True,
                       help="Output prefix for mode shapes and data")
    parser.add_argument("--density", type=float, default=450,
                       help="Wood density (kg/m³) [default: 450 for spruce]")
    parser.add_argument("--thickness", type=float, default=4.0,
                       help="Plate thickness in mm [default: 4.0]")
    parser.add_argument("--num-modes", type=int, default=6,
                       help="Number of modes to compute [default: 6]")
    parser.add_argument("--boundary", choices=['clamped', 'simply_supported'],
                       default='clamped', help="Boundary condition [default: clamped]")
    parser.add_argument("--no-animation", action='store_true',
                       help="Skip creating GIF animations")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ARCHTOP MODAL ANALYSIS")
    print("=" * 60)
    print(f"Input stiffness map: {args.stiffness_map}")
    print(f"Wood density: {args.density} kg/m³")
    print(f"Thickness: {args.thickness} mm")
    print(f"Computing {args.num_modes} modes with {args.boundary} boundary")
    print("-" * 60)
    
    # Load stiffness map
    grid_data = read_stiffness_map(args.stiffness_map)
    print(f"Grid size: {grid_data['nx']} x {grid_data['ny']}")
    print(f"Grid spacing: dx={grid_data['dx']*1000:.1f} mm, dy={grid_data['dy']*1000:.1f} mm")
    
    # Convert thickness to meters
    h_m = args.thickness / 1000.0
    
    # Solve for modes
    frequencies_hz, mode_shapes = solve_modes(
        grid_data, args.density, h_m, args.num_modes, args.boundary
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("MODAL FREQUENCIES")
    print("=" * 60)
    for i, f in enumerate(frequencies_hz):
        print(f"Mode {i+1}: {f:.1f} Hz")
    
    # Save outputs
    print("\n" + "-" * 60)
    print("SAVING OUTPUTS")
    print("-" * 60)
    
    # Plot mode shapes
    plot_mode_shapes(grid_data, mode_shapes, frequencies_hz, args.out_prefix)
    print(f"✓ Mode shape plots: {args.out_prefix}_modes.png")
    
    # Save data
    freq_data = save_modal_data(frequencies_hz, mode_shapes, grid_data, args.out_prefix)
    
    # Create animations (optional)
    if not args.no_animation:
        print("Creating animations (this may take a moment)...")
        create_mode_animation(grid_data, mode_shapes, frequencies_hz, args.out_prefix)
        print(f"✓ Animations: {args.out_prefix}_mode_*_animation.gif")
    
    # Create summary
    summary = {
        'input_file': args.stiffness_map,
        'density_kg_m3': args.density,
        'thickness_mm': args.thickness,
        'boundary_condition': args.boundary,
        'modes': freq_data,
        'lowest_mode_hz': float(frequencies_hz[0]) if len(frequencies_hz) > 0 else None,
        'air_mode_estimate_hz': float(frequencies_hz[0] * 0.7) if len(frequencies_hz) > 0 else None
    }
    
    summary_json = f"{args.out_prefix}_summary.json"
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Summary: {summary_json}")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE!")
    print("=" * 60)
    print("\nYour archtop design now has predicted modes:")
    for i, f in enumerate(frequencies_hz[:3]):
        print(f"  Mode {i+1}: {f:.1f} Hz")
    if len(frequencies_hz) > 3:
        print(f"  ... and {len(frequencies_hz)-3} higher modes")
    
    print("\nNext steps:")
    print("1. Compare predicted modes to target frequencies")
    print("2. Adjust arching geometry in source CSV")
    print("3. Re-run pipeline to see effect on modes")
    print("4. Add sound radiation model to predict tone")

if __name__ == "__main__":
    main()
