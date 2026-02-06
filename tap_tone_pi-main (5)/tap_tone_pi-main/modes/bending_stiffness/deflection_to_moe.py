#!/usr/bin/env python3
import argparse, math, csv, json, pathlib

def E_3point(F, L_mm, b_mm, h_mm, d_mm):
    L=L_mm/1000; b=b_mm/1000; h=h_mm/1000; d=d_mm/1000
    I=b*h**3/12.0
    return (F*L**3)/(48.0*I*d)  # Pa

def E_4point(F, L_mm, b_mm, h_mm, d_mm, a_mm=None):
    L=L_mm/1000; a=(a_mm/1000 if a_mm else L/3); b=b_mm/1000; h=h_mm/1000; d=d_mm/1000
    I=b*h**3/12.0
    return (F*a*(3*L**2-4*a**2))/(24.0*I*d)  # Pa

def calc(method, span, width, thickness, force, deflection, density=None, inner_span=None):
    E = E_3point(force, span, width, thickness, deflection) if method=='3point' else \
        E_4point(force, span, width, thickness, deflection, inner_span)
    out = {'artifact_type':'bending_test','E_GPa': E/1e9}
    if density is not None:
        rho = density*1000.0  # g/cm3 -> kg/m3
        c = (E/rho)**0.5
        out.update({'specific_modulus_GPa_per_gcm3': (E/1e9)/density,'c_m_s': c,'radiation_ratio': c/rho})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--method', choices=['3point','4point'], default='3point')
    ap.add_argument('--span', type=float); ap.add_argument('--width', type=float)
    ap.add_argument('--thickness', type=float); ap.add_argument('--force', type=float)
    ap.add_argument('--deflection', type=float); ap.add_argument('--density', type=float)
    ap.add_argument('--inner-span', type=float)
    ap.add_argument('--csv'); ap.add_argument('--out')
    a = ap.parse_args()

    if a.csv:
        rows=[]
        with open(a.csv, newline='', encoding='utf-8') as f:
            r=csv.DictReader(f)
            for row in r:
                res = calc(row.get('method','3point'), float(row['span_mm']), float(row['width_mm']),
                           float(row['thickness_mm']), float(row['force_N']), float(row['deflection_mm']),
                           float(row['density_g_cm3']) if row.get('density_g_cm3') else None,
                           float(row['inner_span_mm']) if row.get('inner_span_mm') else None)
                row.update(res); rows.append(row)
        out = a.out or 'moe_results.csv'
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', newline='', encoding='utf-8') as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(f'Wrote {out}')
        return

    res = calc(a.method, a.span, a.width, a.thickness, a.force, a.deflection, a.density, a.inner_span)
    out = a.out or 'bending_test.json'
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
    print(f'Wrote {out}')

if __name__=='__main__':
    main()
