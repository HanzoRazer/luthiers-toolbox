# Audit Sources (Local Junctions)

**Purpose:** Read-only cross-repo access for governance audits from `luthiers-toolbox`.

Junctions are **local-only** (not committed to git). Recreate after clone:

```powershell
$audit = "C:\Users\thepr\Downloads\luthiers-toolbox\docs\audit-sources"
New-Item -ItemType Directory -Force -Path $audit | Out-Null
@(
  @('tap_tone_pi', 'C:\Users\thepr\Downloads\tap_tone_pi'),
  @('CAM-Assist-Blueprint', 'C:\Users\thepr\Downloads\CAM-Assist-Blueprint'),
  @('vectorizer-sandbox', 'C:\Users\thepr\Downloads\vectorizer-sandbox')
) | ForEach-Object {
  $link = Join-Path $audit $_[0]
  if (Test-Path $link) { Remove-Item $link -Force -Recurse }
  New-Item -ItemType Junction -Path $link -Target $_[1] | Out-Null
}
```

See [`../handoffs/imports/MANIFEST.md`](../handoffs/imports/MANIFEST.md) for repo HEAD snapshots and handoff index.
