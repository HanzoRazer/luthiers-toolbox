# CAD Collab v9 — Unified Scaffold
Features: DXF import, datum snaps, multi-scale helper, bridge snap, versioned saves, realtime collab, DXF/SVG/G-code exports.
Run server:
  cd server && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && uvicorn app:app --reload --port 8000
Open client/index.html in a browser.
