#!/usr/bin/env python3
"""
tap_tone_pi — Minimal GUI (Tkinter), measurement-only.

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
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess, shlex, pathlib, datetime, os, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
DATA = ROOT / "data"

def run(cmd: str):
    try:
        print("> " + cmd)
        subprocess.check_call(shlex.split(cmd))
        messagebox.showinfo("Done", f"Ran:\n{cmd}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Command failed ({e.returncode}):\n{cmd}")

def default_run_id():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tap_tone_pi — Measurement GUI")
        self.geometry("640x520")
        self.run_id = tk.StringVar(value=default_run_id())

        frm = tk.Frame(self); frm.pack(fill="both", expand=True, padx=10, pady=10)

        # Run ID
        rrow = tk.Frame(frm); rrow.pack(fill="x", pady=4)
        tk.Label(rrow, text="Run ID (folder under out/)").pack(side="left")
        tk.Entry(rrow, textvariable=self.run_id, width=20).pack(side="left", padx=6)

        # --- Tap-tone live
        group(frm, "Tap-tone (live)", [
            ("Duration (s)", "4"), ("Sample rate", "44100")
        ], self.do_tap_live)

        # --- Tap-tone offline
        self.wav_path = tk.StringVar(value=str((DATA/"sample_tap.wav").as_posix()))
        group_file(frm, "Tap-tone (offline WAV)", self.wav_path, self.do_tap_offline)

        # --- MOE single
        self.single_vals = {
            "method":"3point", "span":"400", "width":"20",
            "thickness":"3.0", "force":"5.0", "deflection":"0.62", "density":""
        }
        group(frm, "Bending → MOE (single)", [
            ("Method (3point/4point)", self.single_vals["method"]),
            ("Span mm", self.single_vals["span"]),
            ("Width mm", self.single_vals["width"]),
            ("Thickness mm", self.single_vals["thickness"]),
            ("Force N", self.single_vals["force"]),
            ("Deflection mm", self.single_vals["deflection"]),
            ("Density g/cm^3 (optional)", self.single_vals["density"]),
        ], self.do_moe_single, binds=self.single_vals)

        # --- MOE batch
        self.csv_path = tk.StringVar(value=str((ROOT/"data/deflection_runs.csv").as_posix()))
        group_file(frm, "Bending → MOE (batch CSV)", self.csv_path, self.do_moe_batch)

        # --- Provenance hash
        self.prov_path = tk.StringVar(value=str((ROOT/"data/grain_field.png").as_posix()))
        group_file(frm, "Provenance import (hash only)", self.prov_path, self.do_provenance)

        # --- Load cell capture
        self.load_cfg = tk.StringVar(value=str((ROOT/"config/devices/loadcell_example.json").as_posix()))
        group_file(frm, "Load cell capture (serial) → load_series.json", self.load_cfg, self.do_loadcell)

        # --- Dial indicator capture
        self.dial_port = tk.StringVar(value="COM3" if os.name=="nt" else "/dev/ttyUSB0")
        group_entry(frm, "Dial indicator serial port", self.dial_port, self.do_dial)

        # --- Manifest
        tk.Button(frm, text="Emit manifest.json (hash everything in out/<RunID>)", command=self.do_manifest, width=50).pack(pady=6)

        # --- Chladni Wizard
        tk.Button(
            frm,
            text="Chladni Wizard (WAV → peaks → images → run + manifest)",
            command=self.do_chladni_wizard,
            width=50
        ).pack(pady=4)

    def outdir(self) -> pathlib.Path:
        p = OUT / self.run_id.get().strip()
        p.mkdir(parents=True, exist_ok=True)
        return p

    # callbacks
    def do_tap_live(self, vals):
        outdir = self.outdir()
        dur, sr = vals[0].get(), vals[1].get()
        cmd = f"python modes/tap_tone/tap_fft_logger.py --outfile {outdir/'tap_tone.json'} --plot {outdir/'spectrum.png'} --duration {dur} --sr {sr} --labels A0 T11 B11"
        run(cmd)

    def do_tap_offline(self, path_var):
        outdir = self.outdir()
        cmd = f"python modes/tap_tone/offline_from_wav.py --wav {path_var.get()} --outfile {outdir/'tap_tone_offline.json'} --labels A0 T11 B11"
        run(cmd)

    def do_moe_single(self, binds):
        outdir = self.outdir()
        b = binds
        cmd = f"python modes/bending_stiffness/deflection_to_moe.py --method {b['method']} --span {b['span']} --width {b['width']} --thickness {b['thickness']} --force {b['force']} --deflection {b['deflection']} --out {outdir/'bending_test.json'}"
        if b['density'].strip():
            cmd += f" --density {b['density']}"
        run(cmd)

    def do_moe_batch(self, path_var):
        outdir = self.outdir()
        cmd = f"python modes/bending_stiffness/deflection_to_moe.py --csv {path_var.get()} --out {outdir/'moe_results.csv'}"
        run(cmd)

    def do_provenance(self, path_var):
        outdir = self.outdir()
        cmd = f"python modes/provenance_import/attach_grain_provenance.py --file {path_var.get()} --out {outdir/'provenance.json'}"
        run(cmd)

    def do_loadcell(self, cfg_var):
        outdir = self.outdir()
        cmd = f"python modes/acquisition/loadcell_serial.py --config {cfg_var.get()} --out {outdir/'load_series.json'}"
        run(cmd)

    def do_dial(self, port_var):
        outdir = self.outdir()
        cmd = f"python modes/acquisition/dial_indicator_serial.py --port {port_var.get()} --out {outdir/'displacement_series.json'}"
        run(cmd)

    def do_manifest(self):
        outdir = self.outdir()
        # include all JSON/CSV/PNG/WAV in the run folder
        artifacts = []
        for p in sorted(outdir.glob("*")):
            if p.suffix.lower() in {".json",".csv",".png",".wav"}:
                artifacts += ["--artifact", p.as_posix()]
        rig = ["--rig", "operator=Shop"]
        cmd = ["python","modes/_shared/emit_manifest.py","--out", (outdir/"manifest.json").as_posix(), *artifacts, *rig]
        run(" ".join(shlex.quote(c) for c in cmd))

    def do_chladni_wizard(self):
        """
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
                sys.executable, "modes/chladni/peaks_from_wav.py",
                "--wav", wav_path,
                "--out", peaks_json.as_posix(),
                "--min-hz", "50", "--max-hz", "2000", "--prominence", "0.02"
            ]
            subprocess.check_call(cmd_peaks, cwd=str(ROOT))

            # 3) Pick images (multi-select)
            img_paths = filedialog.askopenfilenames(
                title="Select Chladni pattern images (name like F0148.png)",
                filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.PNG;*.JPG;*.JPEG"), ("All files", "*.*")]
            )
            if not img_paths:
                messagebox.showwarning("No images selected", "Peaks were extracted, but no images were chosen.")
                return

            # 4) Plate ID + Env
            default_plate = f"{self.run_id.get()}_PLATE"
            plate_id = simpledialog.askstring("Plate ID", "Enter plate ID:", initialvalue=default_plate) or default_plate
            try:
                temp_str = simpledialog.askstring("Temperature (C)", "Enter temperature C (optional):", initialvalue="")
                temp_c = float(temp_str) if temp_str else None
            except (TypeError, ValueError):
                temp_c = None
            try:
                rh_str = simpledialog.askstring("RH (%)", "Enter relative humidity % (optional):", initialvalue="")
                rh = float(rh_str) if rh_str else None
            except (TypeError, ValueError):
                rh = None

            chladni_run_json = run_dir / "chladni_run.json"

            # 5) Run index_patterns.py
            cmd_idx = [
                sys.executable, "modes/chladni/index_patterns.py",
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

            # 6) Emit manifest (lists wav, peaks, run json, and all images)
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

            # Done!
            messagebox.showinfo(
                "Chladni v1",
                f"Peaks: {peaks_json}\nRun: {chladni_run_json}\nManifest: {manifest_json}"
            )

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Chladni wizard failed", f"Step failed with exit code {e.returncode}")
        except Exception as ex:
            messagebox.showerror("Chladni wizard error", str(ex))

def group(parent, title, fields, callback, binds=None):
    f = tk.LabelFrame(parent, text=title); f.pack(fill="x", pady=4)
    entries = []
    for label, default in fields:
        row = tk.Frame(f); row.pack(fill="x")
        tk.Label(row, text=label, width=28, anchor="w").pack(side="left")
        var = None
        if isinstance(default, str):
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var, width=16).pack(side="left")
        else:
            var = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=var, width=16).pack(side="left")
        entries.append(var)
        if binds and isinstance(binds, dict):
            # map by normalized key name if present
            key = label.split()[0].lower()
            for k in list(binds.keys()):
                if k.startswith(key):
                    binds[k] = var.get()
    tk.Button(f, text="Run", command=lambda: callback(entries if not binds else binds)).pack(pady=3)

def group_file(parent, title, path_var, callback):
    f = tk.LabelFrame(parent, text=title); f.pack(fill="x", pady=4)
    row = tk.Frame(f); row.pack(fill="x")
    tk.Entry(row, textvariable=path_var, width=48).pack(side="left")
    tk.Button(row, text="Browse", command=lambda: path_var.set(filedialog.askopenfilename() or path_var.get())).pack(side="left", padx=6)
    tk.Button(f, text="Run", command=lambda: callback(path_var)).pack(pady=3)

def group_entry(parent, title, var, callback):
    f = tk.LabelFrame(parent, text=title); f.pack(fill="x", pady=4)
    row = tk.Frame(f); row.pack(fill="x")
    tk.Entry(row, textvariable=var, width=32).pack(side="left")
    tk.Button(f, text="Run", command=lambda: callback(var)).pack(pady=3)

if __name__ == "__main__":
    App().mainloop()
