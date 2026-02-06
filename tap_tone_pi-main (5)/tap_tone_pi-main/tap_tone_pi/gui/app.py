#!/usr/bin/env python3
"""
tap_tone_pi — Minimal GUI (Tkinter), measurement-only.

Migration: Canonical location is now tap_tone_pi.gui.app
           (previously gui/app.py)

Bug Fix: The binding bug in group() has been fixed. Form values are now
         captured at callback time, not at widget construction time.

Phase 6 Enhancements:
- Direct Python imports (no subprocess for core analysis)
- Matplotlib inline spectrum visualization

Runs:
- Tap-tone (live / offline WAV)
- Bending stiffness → MOE (single / batch)
- Provenance hash
- Load cell capture (serial) → load_series.json
- Dial indicator capture (serial) → displacement_series.json
- Emit manifest.json

No advisory or design logic. Facts only.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from typing import TYPE_CHECKING

# Resolve project root
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
DATA = ROOT / "data"

# Optional matplotlib for spectrum visualization
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Direct imports from tap_tone_pi (Phase 6 enhancement)
try:
    from tap_tone_pi.core.analysis import analyze_tap, AnalysisResult, Peak
    from tap_tone_pi.io.wav import read_wav_mono
    HAS_DIRECT_ANALYSIS = True
except ImportError:
    HAS_DIRECT_ANALYSIS = False


class SpectrumViewer(tk.Toplevel):
    """Matplotlib spectrum viewer window (Phase 6 enhancement)."""
    
    def __init__(self, parent: tk.Tk, result: "AnalysisResult", title: str = "Spectrum") -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("800x500")
        
        if not HAS_MATPLOTLIB:
            tk.Label(self, text="matplotlib not installed").pack(pady=20)
            return
        
        # Create figure
        fig = Figure(figsize=(8, 4.5), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot spectrum
        freq = result.spectrum_freq_hz
        mag = result.spectrum_mag
        ax.semilogy(freq, mag + 1e-10, 'b-', linewidth=0.5, alpha=0.7)
        
        # Mark peaks
        for peak in result.peaks:
            ax.axvline(peak.freq_hz, color='r', linestyle='--', alpha=0.5, linewidth=0.8)
            ax.annotate(
                f"{peak.freq_hz:.1f} Hz",
                xy=(peak.freq_hz, peak.magnitude),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                color='red'
            )
        
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (log scale)")
        ax.set_xlim(20, 2000)
        ax.set_title(f"Dominant: {result.dominant_hz:.1f} Hz | Confidence: {result.confidence:.2f}")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Info panel
        info_frame = tk.Frame(self)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = f"Peaks: {len(result.peaks)} | RMS: {result.rms:.4f} | Clipped: {result.clipped}"
        tk.Label(info_frame, text=info_text, font=("Courier", 10)).pack(side=tk.LEFT)
        
        tk.Button(info_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)


def run(cmd: str) -> None:
    """Execute a shell command and show result dialog."""
    try:
        print("> " + cmd)
        subprocess.check_call(shlex.split(cmd))
        messagebox.showinfo("Done", f"Ran:\n{cmd}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Command failed ({e.returncode}):\n{cmd}")


def default_run_id() -> str:
    """Generate a default run ID from current timestamp."""
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


class App(tk.Tk):
    """Main GUI application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("tap_tone_pi — Measurement GUI (v2.0.0)")
        self.geometry("640x520")
        self.run_id = tk.StringVar(value=default_run_id())

        frm = tk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        # Run ID
        rrow = tk.Frame(frm)
        rrow.pack(fill="x", pady=4)
        tk.Label(rrow, text="Run ID (folder under out/)").pack(side="left")
        tk.Entry(rrow, textvariable=self.run_id, width=20).pack(side="left", padx=6)

        # --- Tap-tone live
        self.tap_live_vars = group(frm, "Tap-tone (live)", [
            ("Duration (s)", "4"),
            ("Sample rate", "44100")
        ], self.do_tap_live)

        # --- Tap-tone offline
        self.wav_path = tk.StringVar(value=str((DATA / "sample_tap.wav").as_posix()))
        group_file(frm, "Tap-tone (offline WAV)", self.wav_path, self.do_tap_offline)

        # --- MOE single (with entry vars for live capture)
        self.moe_vars: dict[str, tk.StringVar] = {}
        group_with_binds(frm, "Bending → MOE (single)", [
            ("method", "Method (3point/4point)", "3point"),
            ("span", "Span mm", "400"),
            ("width", "Width mm", "20"),
            ("thickness", "Thickness mm", "3.0"),
            ("force", "Force N", "5.0"),
            ("deflection", "Deflection mm", "0.62"),
            ("density", "Density g/cm^3 (optional)", ""),
        ], self.moe_vars, self.do_moe_single)

        # --- MOE batch
        self.csv_path = tk.StringVar(value=str((ROOT / "data/deflection_runs.csv").as_posix()))
        group_file(frm, "Bending → MOE (batch CSV)", self.csv_path, self.do_moe_batch)

        # --- Provenance hash
        self.prov_path = tk.StringVar(value=str((ROOT / "data/grain_field.png").as_posix()))
        group_file(frm, "Provenance import (hash only)", self.prov_path, self.do_provenance)

        # --- Load cell capture
        self.load_cfg = tk.StringVar(
            value=str((ROOT / "config/devices/loadcell_example.json").as_posix())
        )
        group_file(frm, "Load cell capture (serial) → load_series.json", self.load_cfg, self.do_loadcell)

        # --- Dial indicator capture
        self.dial_port = tk.StringVar(value="COM3" if os.name == "nt" else "/dev/ttyUSB0")
        group_entry(frm, "Dial indicator serial port", self.dial_port, self.do_dial)

        # --- Manifest
        tk.Button(
            frm,
            text="Emit manifest.json (hash everything in out/<RunID>)",
            command=self.do_manifest,
            width=50
        ).pack(pady=6)

        # --- Chladni Wizard
        tk.Button(
            frm,
            text="Chladni Wizard (WAV → peaks → images → run + manifest)",
            command=self.do_chladni_wizard,
            width=50
        ).pack(pady=4)

    def outdir(self) -> pathlib.Path:
        """Get or create the output directory for current run."""
        p = OUT / self.run_id.get().strip()
        p.mkdir(parents=True, exist_ok=True)
        return p

    # --- Callbacks ---

    def do_tap_live(self, entry_vars: list[tk.StringVar]) -> None:
        """Run live tap-tone capture."""
        outdir = self.outdir()
        dur = entry_vars[0].get()
        sr = entry_vars[1].get()
        cmd = (
            f"python modes/tap_tone/tap_fft_logger.py "
            f"--outfile {outdir/'tap_tone.json'} "
            f"--plot {outdir/'spectrum.png'} "
            f"--duration {dur} --sr {sr} --labels A0 T11 B11"
        )
        run(cmd)

    def do_tap_offline(self, path_var: tk.StringVar) -> None:
        """Run offline tap-tone analysis on a WAV file.
        
        Phase 6 Enhancement: Uses direct Python imports when available,
        with inline matplotlib spectrum visualization.
        """
        wav_path = pathlib.Path(path_var.get())
        outdir = self.outdir()
        
        if HAS_DIRECT_ANALYSIS and HAS_MATPLOTLIB:
            # Direct analysis with spectrum viewer (Phase 6)
            try:
                audio, sr = read_wav_mono(wav_path)
                result = analyze_tap(audio, sr)
                
                # Save JSON result
                out_json = outdir / "tap_tone_offline.json"
                result_dict = {
                    "dominant_hz": result.dominant_hz,
                    "peaks": [{"freq_hz": p.freq_hz, "magnitude": p.magnitude} for p in result.peaks],
                    "clipped": result.clipped,
                    "rms": result.rms,
                    "confidence": result.confidence,
                    "source_wav": str(wav_path),
                }
                with open(out_json, "w") as f:
                    json.dump(result_dict, f, indent=2)
                
                # Show spectrum viewer
                SpectrumViewer(self, result, title=f"Spectrum: {wav_path.name}")
                messagebox.showinfo("Done", f"Analysis saved to:\n{out_json}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Analysis failed: {e}")
        else:
            # Fallback to subprocess
            cmd = (
                f"python modes/tap_tone/offline_from_wav.py "
                f"--wav {path_var.get()} "
                f"--outfile {outdir/'tap_tone_offline.json'} --labels A0 T11 B11"
            )
            run(cmd)

    def do_moe_single(self, var_dict: dict[str, tk.StringVar]) -> None:
        """Calculate MOE from single measurement.
        
        BUG FIX: Now reads .get() at callback time, not construction time.
        """
        outdir = self.outdir()
        # Read current values from StringVars at callback time
        method = var_dict["method"].get()
        span = var_dict["span"].get()
        width = var_dict["width"].get()
        thickness = var_dict["thickness"].get()
        force = var_dict["force"].get()
        deflection = var_dict["deflection"].get()
        density = var_dict["density"].get()
        
        cmd = (
            f"python modes/bending_stiffness/deflection_to_moe.py "
            f"--method {method} --span {span} --width {width} "
            f"--thickness {thickness} --force {force} --deflection {deflection} "
            f"--out {outdir/'bending_test.json'}"
        )
        if density.strip():
            cmd += f" --density {density}"
        run(cmd)

    def do_moe_batch(self, path_var: tk.StringVar) -> None:
        """Calculate MOE from batch CSV."""
        outdir = self.outdir()
        cmd = (
            f"python modes/bending_stiffness/deflection_to_moe.py "
            f"--csv {path_var.get()} --out {outdir/'moe_results.csv'}"
        )
        run(cmd)

    def do_provenance(self, path_var: tk.StringVar) -> None:
        """Hash a file for provenance tracking."""
        outdir = self.outdir()
        cmd = (
            f"python modes/provenance_import/attach_grain_provenance.py "
            f"--file {path_var.get()} --out {outdir/'provenance.json'}"
        )
        run(cmd)

    def do_loadcell(self, cfg_var: tk.StringVar) -> None:
        """Capture load cell data via serial."""
        outdir = self.outdir()
        cmd = (
            f"python modes/acquisition/loadcell_serial.py "
            f"--config {cfg_var.get()} --out {outdir/'load_series.json'}"
        )
        run(cmd)

    def do_dial(self, port_var: tk.StringVar) -> None:
        """Capture dial indicator data via serial."""
        outdir = self.outdir()
        cmd = (
            f"python modes/acquisition/dial_indicator_serial.py "
            f"--port {port_var.get()} --out {outdir/'displacement_series.json'}"
        )
        run(cmd)

    def do_manifest(self) -> None:
        """Emit manifest.json for all artifacts in run directory."""
        outdir = self.outdir()
        artifacts = []
        for p in sorted(outdir.glob("*")):
            if p.suffix.lower() in {".json", ".csv", ".png", ".wav"}:
                artifacts += ["--artifact", p.as_posix()]
        rig = ["--rig", "operator=Shop"]
        cmd = [
            "python", "modes/_shared/emit_manifest.py",
            "--out", (outdir / "manifest.json").as_posix(),
            *artifacts, *rig
        ]
        run(" ".join(shlex.quote(c) for c in cmd))

    def do_chladni_wizard(self) -> None:
        """
        Chladni pattern analysis wizard:
        1) Ask for a sweep/stepped-tone WAV
        2) Run peaks_from_wav.py → peaks.json
        3) Multi-select Chladni images (F####.png/JPG filenames embed Hz)
        4) Ask Plate ID + (optional) Temp/RH
        5) Run index_patterns.py → chladni_run.json
        6) Emit manifest.json for the Chladni set
        """
        try:
            run_dir = self.outdir() / "chladni"
            run_dir.mkdir(parents=True, exist_ok=True)

            # 1) Pick WAV
            wav_path = filedialog.askopenfilename(
                title="Select Chladni sweep WAV",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
            )
            if not wav_path:
                return

            peaks_json = run_dir / "peaks.json"

            # 2) Run peaks_from_wav.py
            cmd_peaks = [
                sys.executable, "-m", "tap_tone_pi.chladni.peaks_from_wav",
                "--wav", wav_path,
                "--out", peaks_json.as_posix(),
                "--min-hz", "50", "--max-hz", "2000", "--prominence", "0.02"
            ]
            subprocess.check_call(cmd_peaks, cwd=str(ROOT))

            # 3) Pick images (multi-select)
            img_paths = filedialog.askopenfilenames(
                title="Select Chladni pattern images (name like F0148.png)",
                filetypes=[
                    ("Images", "*.png;*.jpg;*.jpeg;*.PNG;*.JPG;*.JPEG"),
                    ("All files", "*.*")
                ]
            )
            if not img_paths:
                messagebox.showwarning(
                    "No images selected",
                    "Peaks were extracted, but no images were chosen."
                )
                return

            # 4) Plate ID + Env
            default_plate = f"{self.run_id.get()}_PLATE"
            plate_id = simpledialog.askstring(
                "Plate ID", "Enter plate ID:", initialvalue=default_plate
            ) or default_plate
            
            try:
                temp_str = simpledialog.askstring(
                    "Temperature (C)", "Enter temperature C (optional):", initialvalue=""
                )
                temp_c = float(temp_str) if temp_str else None
            except (TypeError, ValueError):
                temp_c = None
            
            try:
                rh_str = simpledialog.askstring(
                    "RH (%)", "Enter relative humidity % (optional):", initialvalue=""
                )
                rh = float(rh_str) if rh_str else None
            except (TypeError, ValueError):
                rh = None

            chladni_run_json = run_dir / "chladni_run.json"

            # 5) Run index_patterns.py
            cmd_idx = [
                sys.executable, "-m", "tap_tone_pi.chladni.index_patterns",
                "--peaks-json", peaks_json.as_posix(),
                "--plate-id", plate_id,
                "--out", chladni_run_json.as_posix(),
                "--images",
            ]
            cmd_idx += [pathlib.Path(p).as_posix() for p in img_paths]
            if temp_c is not None:
                cmd_idx += ["--tempC", str(temp_c)]
            if rh is not None:
                cmd_idx += ["--rh", str(rh)]

            subprocess.check_call(cmd_idx, cwd=str(ROOT))

            # 6) Emit manifest
            manifest_json = run_dir / "manifest.json"
            art_args = [
                "--artifact", peaks_json.as_posix(),
                "--artifact", chladni_run_json.as_posix(),
                "--artifact", pathlib.Path(wav_path).as_posix(),
            ]
            for p in img_paths:
                art_args += ["--artifact", pathlib.Path(p).as_posix()]

            rig_kvs = ["--rig", f"plate_id={plate_id}"]
            notes = ["--notes", f"Chladni v1 wizard (run={self.outdir().name})"]

            cmd_manifest = [
                sys.executable, "modes/_shared/emit_manifest.py",
                "--out", manifest_json.as_posix(),
                *art_args, *rig_kvs, *notes
            ]
            subprocess.check_call(cmd_manifest, cwd=str(ROOT))

            messagebox.showinfo(
                "Chladni v1",
                f"Peaks: {peaks_json}\nRun: {chladni_run_json}\nManifest: {manifest_json}"
            )

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Chladni wizard failed", f"Step failed with exit code {e.returncode}")
        except Exception as ex:
            messagebox.showerror("Chladni wizard error", str(ex))


# --- Helper functions for building form groups ---

def group(
    parent: tk.Widget,
    title: str,
    fields: list[tuple[str, str]],
    callback
) -> list[tk.StringVar]:
    """
    Create a labeled frame with entry fields and a Run button.
    
    Returns the list of StringVars so they can be read at callback time.
    The callback receives this list and should call .get() on each var.
    """
    f = tk.LabelFrame(parent, text=title)
    f.pack(fill="x", pady=4)
    
    entry_vars: list[tk.StringVar] = []
    for label, default in fields:
        row = tk.Frame(f)
        row.pack(fill="x")
        tk.Label(row, text=label, width=28, anchor="w").pack(side="left")
        var = tk.StringVar(value=default)
        tk.Entry(row, textvariable=var, width=16).pack(side="left")
        entry_vars.append(var)
    
    # Pass the list of vars to callback - caller reads .get() at call time
    tk.Button(f, text="Run", command=lambda: callback(entry_vars)).pack(pady=3)
    return entry_vars


def group_with_binds(
    parent: tk.Widget,
    title: str,
    fields: list[tuple[str, str, str]],  # (key, label, default)
    var_dict: dict[str, tk.StringVar],
    callback
) -> None:
    """
    Create a labeled frame with named entry fields.
    
    BUG FIX: Stores StringVar objects in var_dict, not their values.
    The callback receives var_dict and should call var.get() at call time.
    
    Args:
        fields: List of (key, label, default) tuples
        var_dict: Dictionary to populate with key -> StringVar mappings
        callback: Function to call with var_dict on Run button click
    """
    f = tk.LabelFrame(parent, text=title)
    f.pack(fill="x", pady=4)
    
    for key, label, default in fields:
        row = tk.Frame(f)
        row.pack(fill="x")
        tk.Label(row, text=label, width=28, anchor="w").pack(side="left")
        var = tk.StringVar(value=default)
        tk.Entry(row, textvariable=var, width=16).pack(side="left")
        # Store the StringVar, not its current value
        var_dict[key] = var
    
    tk.Button(f, text="Run", command=lambda: callback(var_dict)).pack(pady=3)


def group_file(
    parent: tk.Widget,
    title: str,
    path_var: tk.StringVar,
    callback
) -> None:
    """Create a labeled frame with file path entry and browse button."""
    f = tk.LabelFrame(parent, text=title)
    f.pack(fill="x", pady=4)
    
    row = tk.Frame(f)
    row.pack(fill="x")
    tk.Entry(row, textvariable=path_var, width=48).pack(side="left")
    tk.Button(
        row,
        text="Browse",
        command=lambda: path_var.set(filedialog.askopenfilename() or path_var.get())
    ).pack(side="left", padx=6)
    
    tk.Button(f, text="Run", command=lambda: callback(path_var)).pack(pady=3)


def group_entry(
    parent: tk.Widget,
    title: str,
    var: tk.StringVar,
    callback
) -> None:
    """Create a labeled frame with a single entry field."""
    f = tk.LabelFrame(parent, text=title)
    f.pack(fill="x", pady=4)
    
    row = tk.Frame(f)
    row.pack(fill="x")
    tk.Entry(row, textvariable=var, width=32).pack(side="left")
    
    tk.Button(f, text="Run", command=lambda: callback(var)).pack(pady=3)


if __name__ == "__main__":
    App().mainloop()
