#!/usr/bin/env python3
import argparse, json, os, pathlib, hashlib, time

def sha256(p): 
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="e.g., grain_field.png or grain_vectors.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-tool", default="")
    ap.add_argument("--resolution", default="")
    ap.add_argument("--orientation_ref", default="")
    ap.add_argument("--confidence", type=float, default=None)
    a=ap.parse_args()

    data = {
      "artifact_type":"provenance",
      "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
      "file": os.fspath(a.file),
      "sha256": sha256(a.file),
      "size": os.path.getsize(a.file),
      "source_tool": a.source_tool,
      "resolution": a.resolution,
      "orientation_ref": a.orientation_ref,
      "confidence": a.confidence
    }
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
    print(f"Wrote {a.out}")

if __name__=="__main__":
    main()
