
# Pull Request Guide

1. Create a branch:
   ```bash
   git checkout -b feature/my-change
   ```
2. Run tests & smoke:
   ```bash
   pytest -q || echo "pytest not configured"
   python scripts/smoke_cam_essentials.py || echo "smoke optional"
   ```
3. If touching CAM posts/routers, include before/after snippets and sample output (SVG/NC).
4. Keep PRs focused (one topic). Add screenshots for UI changes.
5. Expect squash merges for small/medium contributions.
