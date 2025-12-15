#!/usr/bin/env python3
import re, argparse, html, csv
from pathlib import Path
COMMENT_PATTERNS=[(re.compile(r"\(.*?\)"),""),(re.compile(r";.*$"),""),(re.compile(r"%"),"")]
TOKEN_RE=re.compile(r"([A-Z])([+\-]?\d+(\.\d+)?)",re.I)
def strip_comments(s): 
    out=s
    for pat,repl in COMMENT_PATTERNS: out=pat.sub(repl,out)
    return out.strip()
def tokens_param_map(s):
    d={}
    for m in TOKEN_RE.finditer(s.replace(" ","")): d[m.group(1).upper()]=float(m.group(2))
    return d
def words_list(s):
    s=s.replace(" ",""); out=[]; i=0
    while i<len(s):
        if s[i].isalpha():
            j=i+1
            while j<len(s) and (s[j].isdigit() or s[j] in ".-+"): j+=1
            out.append(s[i:j].upper()); i=j
        else: i+=1
    return out
class ModalState:
    def __init__(self, flavor="generic"):
        self.units="mm"; self.distance="absolute"; self.feedmode="per_min"; self.plane="XY"
        self.wcs="G54"; self.feed=None; self.rpm=None; self.spindle="OFF"; self.tool=None
    def modes(self):
        unit="mm/min" if self.units=="mm" else "in/min"
        f=(f"Feed: {self.feed:g} {unit}; " if self.feed is not None else "")
        s=(f"Spindle: {self.spindle}" + (f" @ {self.rpm:g} RPM" if self.rpm is not None else ""))
        return f"Units: {self.units}; Dist: {self.distance}; Plane: {self.plane}; {f}{s}; WCS: {self.wcs}"
def fmt_xyz(p): 
    return " ".join([f"{k}{p[k]:g}" for k in ("X","Y","Z") if k in p]) or "(no XYZ)"
def explain_line(line, st: ModalState):
    raw=line.rstrip("\n"); ln=strip_comments(raw)
    if not ln: return raw,"(comment/blank)",st.modes()
    words=words_list(ln); params=tokens_param_map(ln)
    g=[w.split('.')[0] for w in words if w.startswith('G')]; m=[w for w in words if w.startswith('M')]
    acts=[]
    for gc in g:
        if gc in ("G20","G70"): st.units="inch"; acts.append("Units → inches (G20).")
        elif gc in ("G21","G71"): st.units="mm"; acts.append("Units → millimeters (G21).")
        elif gc=="G90": st.distance="absolute"; acts.append("Absolute (G90).")
        elif gc=="G91": st.distance="incremental"; acts.append("Incremental (G91).")
        elif gc=="G94": st.feedmode="per_min"; acts.append("Feed per minute (G94).")
        elif gc=="G95": st.feedmode="per_rev"; acts.append("Feed per rev (G95).")
        elif gc=="G17": st.plane="XY"; acts.append("Plane XY (G17).")
        elif gc=="G18": st.plane="XZ"; acts.append("Plane XZ (G18).")
        elif gc=="G19": st.plane="YZ"; acts.append("Plane YZ (G19).")
        elif gc in ("G54","G55","G56","G57","G58","G59"): st.wcs=gc; acts.append(f"WCS {gc}.")
    for mc in m:
        if mc in ("M3","M03"): st.spindle="CW"; st.rpm=params.get("S",st.rpm); acts.append(f"Spindle CW (M3){(' @ '+str(int(st.rpm))+' RPM') if st.rpm else ''}.")
        elif mc in ("M4","M04"): st.spindle="CCW"; st.rpm=params.get("S",st.rpm); acts.append(f"Spindle CCW (M4){(' @ '+str(int(st.rpm))+' RPM') if st.rpm else ''}.")
        elif mc in ("M5","M05"): st.spindle="OFF"; acts.append("Spindle OFF (M5).")
        elif mc in ("M2","M30"): acts.append("Program end (M2/M30).")
    if "F" in params: st.feed=params["F"]; unit="mm/min" if st.units=="mm" else "in/min"; acts.append(f"Feed set F{st.feed:g} {unit}.")
    if "S" in params and not any(mm in m for mm in ("M3","M4","M03","M04")): st.rpm=params["S"]; acts.append(f"RPM set S{st.rpm:g}.")
    motion=None
    for gc in g:
        if gc in ("G0","G00","G1","G01","G2","G02","G3","G03"): motion=gc
    xyz={k:params[k] for k in ("X","Y","Z") if k in params}; ijk={k:params[k] for k in ("I","J","K") if k in params}; r=params.get("R")
    if motion in ("G0","G00"): acts.append(f"Rapid → {fmt_xyz(xyz)}.")
    elif motion in ("G1","G01"): unit='mm/min' if st.units=='mm' else 'in/min'; f=(f' at F{st.feed:g} {unit}' if st.feed else ''); acts.append(f"Linear → {fmt_xyz(xyz)}{f}.")
    elif motion in ("G2","G02","G3","G03"):
        cw='clockwise' if motion in ("G2","G02") else 'counter-clockwise'
        if r is not None: acts.append(f"Arc {cw} → {fmt_xyz(xyz)} R{r:g} in {st.plane}.")
        else:
            centers=' '.join([f"{k}{v:g}" for k,v in ijk.items()]) if ijk else 'no IJK'
            acts.append(f"Arc {cw} → {fmt_xyz(xyz)} using {centers} in {st.plane}.")
    return raw, (" ".join(acts) or "No op recognized."), st.modes()

def write_txt(p, rows):
    out=[]
    for n,raw,expl,m in rows:
        out.append(f"N{n:04d}: {raw}"); out.append(f"       → {expl}"); 
        if expl != "(comment/blank)": out.append(f"       · {m}")
        out.append("")
    Path(p).write_text("\n".join(out), encoding="utf-8")

def write_md(p, rows, title):
    lines=[f"# G-code Explanation — {title}","","| Line | G-code | Explanation | Modes |","|---:|---|---|---|"]
    pipe_esc = "\\|"
    for n,raw,expl,m in rows:
        lines.append(f"| {n} | `{raw.replace('|', pipe_esc)}` | {expl.replace('|', pipe_esc)} | {m.replace('|', pipe_esc)} |")
    Path(p).write_text("\n".join(lines), encoding="utf-8")

def write_html(p, rows, title):
    esc=html.escape
    h=["<!doctype html><meta charset='utf-8'><title>G-code Explanation</title><style>body{font-family:Arial;margin:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:8px}th{background:#f5f5f5}tr:nth-child(even){background:#fafafa}</style>",
       f"<h2>G-code Explanation — {esc(title)}</h2><table><thead><tr><th>Line</th><th>G-code</th><th>Explanation</th><th>Modes</th></tr></thead><tbody>"]
    for n,raw,expl,m in rows:
        h.append(f"<tr><td>{n}</td><td><code>{esc(raw)}</code></td><td>{esc(expl)}</td><td>{esc(m)}</td></tr>")
    h.append("</tbody></table>"); Path(p).write_text("\n".join(h), encoding="utf-8")

def write_csv(p, rows):
    import csv
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["line","gcode","explanation","modes"])
        for n,raw,expl,m in rows: w.writerow([n,raw,expl,m])

def main():
    ap=argparse.ArgumentParser(description="Explain a G-code file (offline).")
    ap.add_argument("--in",dest="infile",required=True); ap.add_argument("--out",dest="outfile",default=None)
    ap.add_argument("--md",action="store_true"); ap.add_argument("--html",action="store_true"); ap.add_argument("--csv",action="store_true")
    args=ap.parse_args()
    pin=Path(args.infile); 
    rows=[]; st=ModalState()
    for i,ln in enumerate(pin.read_text(errors="ignore").splitlines(),1):
        raw,expl,m=explain_line(ln,st); rows.append((i,raw,expl,m))
    ptxt=Path(args.outfile) if args.outfile else pin.with_name(pin.stem+"_Explained.txt")
    write_txt(ptxt,rows); print(f"[OK] {ptxt}")
    if args.md: write_md(pin.with_name(pin.stem+"_Explained.md"),rows,pin.name)
    if args.html: write_html(pin.with_name(pin.stem+"_Explained.html"),rows,pin.name)
    if args.csv: write_csv(pin.with_name(pin.stem+"_Explained.csv"),rows)
if __name__=="__main__": main()
