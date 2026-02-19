/**
 * Composable for generating export code snippets (PowerShell, Python, Node, GitHub Actions).
 * Extracted from DesignFirstWorkflowPanel.vue
 */

// ==========================================================================
// String Escaping Utilities
// ==========================================================================

/** Escape single quotes for PowerShell single-quoted strings */
export function psEscape(s: string): string {
  return `'${String(s).replace(/'/g, "''")}'`
}

/** Escape for Python triple-quoted strings */
export function pyEscape(s: string): string {
  return String(s).replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"')
}

/** Escape for JS template literal (backticks) */
export function jsEscape(s: string): string {
  return String(s)
    .replace(/\\/g, '\\\\')
    .replace(new RegExp(String.fromCharCode(96), 'g'), '\\' + String.fromCharCode(96))
}

/** Escape single quotes for YAML single-quoted strings */
export function yamlEscapeSingleQuotes(s: string): string {
  return s.replace(/'/g, "''")
}

// ==========================================================================
// Filename Utilities
// ==========================================================================

/** Generate safe filename from session ID */
export function safeFilenameFromSession(sessionId: string): string {
  const cleaned = (sessionId || 'session')
    .trim()
    .slice(0, 32)
    .replace(/[^a-zA-Z0-9._-]+/g, '_')
  return `art_studio_export_intent_${cleaned}.json`
}

/**
 * Best-effort repo name detection for workflow header.
 * Priority: VITE_REPO_NAME env → BASE_URL → pathname heuristic → fallback.
 */
export function detectRepoNameForHeader(): string {
  try {
    const viteRepo =
      (import.meta as any)?.env?.VITE_REPO_NAME ||
      (import.meta as any)?.env?.REPO_NAME

    if (typeof viteRepo === 'string' && viteRepo.trim()) {
      return viteRepo.trim()
    }

    const baseUrl = (import.meta as any)?.env?.BASE_URL
    if (typeof baseUrl === 'string' && baseUrl !== '/' && baseUrl.trim()) {
      const m = baseUrl.match(/^\/([^/]+)\/?$/)
      if (m?.[1]) return m[1]
    }

    const path = window.location?.pathname || ''
    const parts = path.split('/').filter(Boolean)
    if (parts.length >= 1) {
      return parts[0]
    }
  } catch {
    // ignore
  }

  return 'UNKNOWN_REPO'
}

// ==========================================================================
// PowerShell Snippet
// ==========================================================================

export function buildExportPowerShellIwr(url: string, sessionId: string): string {
  const out = safeFilenameFromSession(sessionId)

  return [
    `$url = ${psEscape(url)}`,
    `$out = ${psEscape(out)}`,
    `Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing`,
    `Write-Host ("Saved: " + $out)`,
  ].join('\r\n')
}

// ==========================================================================
// Python Snippet
// ==========================================================================

export function buildExportPythonRequests(url: string, sessionId: string): string {
  const out = safeFilenameFromSession(sessionId)
  const u = pyEscape(url)

  return [
    '# Promotion intent export (Python requests)',
    'import sys',
    'import json',
    'import requests',
    '',
    `url = """${u}"""`,
    `out = r"""${out}"""`,
    '',
    "resp = requests.get(url, headers={'Accept': 'application/json'}, timeout=30)",
    'resp.raise_for_status()',
    '',
    '# Save raw body',
    "with open(out, 'wb') as f:",
    '    f.write(resp.content)',
    '',
    '# Optional: quick sanity parse',
    'try:',
    '    data = resp.json()',
    "    print('Downloaded intent:', data.get('intent_version'), 'session_id=', data.get('session_id'))",
    'except Exception as e:',
    "    print('Downloaded file saved, but JSON parse failed:', e, file=sys.stderr)",
    '',
    "print('Saved:', out)",
    '',
  ].join('\n')
}

// ==========================================================================
// Node.js Snippet
// ==========================================================================

export function buildExportNodeFetch(url: string, sessionId: string): string {
  const out = safeFilenameFromSession(sessionId)
  const u = jsEscape(url)

  return [
    '// Promotion intent export (Node fetch, Node 18+)',
    "import fs from 'node:fs';",
    '',
    "const url = '" + u + "';",
    'const out = ' + JSON.stringify(out) + ';',
    '',
    'const res = await fetch(url, {',
    "  method: 'GET',",
    "  headers: { 'Accept': 'application/json' },",
    '});',
    '',
    'if (!res.ok) {',
    "  const ct = res.headers.get('content-type') || '';",
    "  let body = '';",
    "  try { body = ct.includes('application/json') ? JSON.stringify(await res.json()) : await res.text(); } catch {}",
    "  throw new Error('HTTP ' + res.status + ' ' + res.statusText + ' :: ' + body);",
    '}',
    '',
    'const buf = Buffer.from(await res.arrayBuffer());',
    'fs.writeFileSync(out, buf);',
    '',
    '// Optional: sanity parse',
    'try {',
    "  const json = JSON.parse(buf.toString('utf8'));",
    "  console.log('Downloaded intent:', json.intent_version, 'session_id=', json.session_id);",
    '} catch (e) {',
    "  console.warn('Saved file but JSON parse failed:', e?.message || e);",
    '}',
    '',
    "console.log('Saved:', out);",
    '',
  ].join('\n')
}

// ==========================================================================
// GitHub Actions Step
// ==========================================================================

export function buildExportGitHubActionsStep(url: string, sessionId: string): string {
  const out = safeFilenameFromSession(sessionId)
  const safeUrl = yamlEscapeSingleQuotes(url)
  return [
    '- name: Download RMOS promotion-intent',
    '  run: |',
    `    curl -sSfL '${safeUrl}' -o ${out}`,
    '',
    '- name: Upload promotion-intent artifact',
    '  uses: actions/upload-artifact@v4',
    '  with:',
    '    name: promotion-intent',
    `    path: ${out}`,
  ].join('\n')
}

// ==========================================================================
// GitHub Actions Job
// ==========================================================================

export function buildExportGitHubActionsJob(url: string, sessionId: string): string {
  const safeOut = safeFilenameFromSession(sessionId)
  const u = yamlEscapeSingleQuotes(url)
  const out = yamlEscapeSingleQuotes(safeOut)

  return [
    'art-studio-export-intent:',
    '  name: Download Art Studio export intent',
    '  runs-on: ubuntu-latest',
    '  steps:',
    '    - name: Download export intent JSON',
    '      env:',
    '        TOOLBOX_API_TOKEN: ${{ secrets.TOOLBOX_API_TOKEN }}',
    '      run: |',
    '        set -euo pipefail',
    `        URL='${u}'`,
    `        OUT='${out}'`,
    '        HDR=()',
    '        if [ -n "${TOOLBOX_API_TOKEN:-}" ]; then',
    '          HDR+=(-H "Authorization: Bearer ${TOOLBOX_API_TOKEN}")',
    '        fi',
    '        curl -sSfL "${HDR[@]}" "$URL" -o "$OUT"',
    '        echo "Saved ${OUT}"',
    '    - name: Upload artifact',
    '      uses: actions/upload-artifact@v4',
    '      with:',
    '        name: art-studio-export-intent',
    `        path: ${out}`,
    '        retention-days: 7',
    '',
  ].join('\n')
}

// ==========================================================================
// GitHub Actions Workflow (Full .yml)
// ==========================================================================

export function buildExportGitHubActionsWorkflow(url: string, sessionId: string): string {
  const safeOut = safeFilenameFromSession(sessionId)
  const u = yamlEscapeSingleQuotes(url)
  const out = yamlEscapeSingleQuotes(safeOut)

  return [
    `name: Art Studio — Download + Validate Export Intent`,
    ``,
    `on:`,
    `  workflow_dispatch:`,
    `    inputs:`,
    `      export_url:`,
    `        description: 'Override export URL (optional)'`,
    `        required: false`,
    `        default: '${u}'`,
    `      out_file:`,
    `        description: 'Output filename (optional)'`,
    `        required: false`,
    `        default: '${out}'`,
    ``,
    `permissions:`,
    `  contents: read`,
    ``,
    `jobs:`,
    `  art-studio-export-intent:`,
    `    name: Download export intent`,
    `    runs-on: ubuntu-latest`,
    `    steps:`,
    `      - name: Download export intent JSON`,
    `        env:`,
    `          TOOLBOX_API_TOKEN: \${{ secrets.TOOLBOX_API_TOKEN }}`,
    `          EXPORT_URL: \${{ inputs.export_url }}`,
    `          OUT_FILE: \${{ inputs.out_file }}`,
    `        run: |`,
    `          set -euo pipefail`,
    `          URL="\${EXPORT_URL}"`,
    `          OUT="\${OUT_FILE}"`,
    `          HDR=()`,
    `          if [ -n "\${TOOLBOX_API_TOKEN:-}" ]; then`,
    `            HDR+=(-H "Authorization: Bearer \${TOOLBOX_API_TOKEN}")`,
    `          fi`,
    `          curl -L "\${HDR[@]}" "\${URL}" -o "\${OUT}"`,
    `          echo "Saved \${OUT}"`,
    `          ls -la`,
    ``,
    `      - name: Upload artifact`,
    `        uses: actions/upload-artifact@v4`,
    `        with:`,
    `          name: art-studio-export-intent`,
    `          path: \${{ inputs.out_file }}`,
    `          retention-days: 7`,
    ``,
    `  validate-export-intent:`,
    `    name: Validate PromotionIntentV1 (strict)`,
    `    runs-on: ubuntu-latest`,
    `    needs: [art-studio-export-intent]`,
    `    steps:`,
    `      - name: Download artifact`,
    `        uses: actions/download-artifact@v4`,
    `        with:`,
    `          name: art-studio-export-intent`,
    ``,
    `      - name: Strict schema validation`,
    `        env:`,
    `          OUT_FILE: \${{ inputs.out_file }}`,
    `        run: |`,
    `          set -euo pipefail`,
    `          python - <<'PY'`,
    `          import json, os, sys`,
    `          `,
    `          # Locate the file`,
    `          path = os.environ.get("OUT_FILE")`,
    `          if not path or not os.path.exists(path):`,
    `              candidates = [p for p in os.listdir(".") if p.lower().endswith(".json")]`,
    `              if len(candidates) == 1:`,
    `                  path = candidates[0]`,
    `              else:`,
    `                  raise SystemExit(f"Could not locate OUT_FILE. OUT_FILE={path!r}, candidates={candidates}")`,
    `          `,
    `          # Parse JSON`,
    `          with open(path, "r", encoding="utf-8") as f:`,
    `              data = json.load(f)`,
    `          `,
    `          if not isinstance(data, dict):`,
    `              raise SystemExit(f"PromotionIntentV1 must be an object, got {type(data).__name__}")`,
    `          `,
    `          # =================== STRICT CONTRACT VALIDATION ===================`,
    `          # Required top-level keys (PromotionIntentV1 contract)`,
    `          REQUIRED_TOP = [`,
    `              "intent_version", "session_id", "mode", "created_at",`,
    `              "design", "feasibility", "design_fingerprint",`,
    `              "feasibility_fingerprint", "fingerprint_algo",`,
    `          ]`,
    `          missing_top = [k for k in REQUIRED_TOP if k not in data]`,
    `          if missing_top:`,
    `              raise SystemExit(f"STRICT FAIL: Missing required top-level keys: {missing_top}")`,
    `          `,
    `          # intent_version must be "v1"`,
    `          if data.get("intent_version") != "v1":`,
    `              raise SystemExit(f"STRICT FAIL: intent_version must be 'v1', got {data.get('intent_version')!r}")`,
    `          `,
    `          # Required nested keys in design`,
    `          design = data.get("design")`,
    `          if not isinstance(design, dict):`,
    `              raise SystemExit(f"STRICT FAIL: 'design' must be an object, got {type(design).__name__}")`,
    `          REQUIRED_DESIGN = ["outer_diameter_mm", "inner_diameter_mm", "ring_params"]`,
    `          missing_design = [k for k in REQUIRED_DESIGN if k not in design]`,
    `          if missing_design:`,
    `              raise SystemExit(f"STRICT FAIL: Missing required design keys: {missing_design}")`,
    `          `,
    `          # Required nested keys in feasibility`,
    `          feas = data.get("feasibility")`,
    `          if not isinstance(feas, dict):`,
    `              raise SystemExit(f"STRICT FAIL: 'feasibility' must be an object, got {type(feas).__name__}")`,
    `          REQUIRED_FEAS = ["overall_score", "risk_bucket", "material_efficiency", "estimated_cut_time_min", "warnings"]`,
    `          missing_feas = [k for k in REQUIRED_FEAS if k not in feas]`,
    `          if missing_feas:`,
    `              raise SystemExit(f"STRICT FAIL: Missing required feasibility keys: {missing_feas}")`,
    `          `,
    `          # =================== VALIDATION PASSED ===================`,
    `          print(f"OK: PromotionIntentV1 strict validation passed for {path}")`,
    `          print(f"    intent_version={data['intent_version']}")`,
    `          print(f"    session_id={data['session_id']}")`,
    `          print(f"    mode={data['mode']}")`,
    `          print(f"    design_fingerprint={data['design_fingerprint'][:16]}...")`,
    `          print(f"    feasibility.risk_bucket={feas['risk_bucket']}")`,
    `          PY`,
    ``,
  ].join('\n')
}

// ==========================================================================
// Repo-Ready Workflow Bundle
// ==========================================================================

export function buildRepoReadyWorkflowBundle(url: string, sessionId: string): string {
  const filename = 'art-studio-export-intent.yml'
  const repoName = detectRepoNameForHeader()
  const workflow = buildExportGitHubActionsWorkflow(url, sessionId)

  return [
    `# =====================================================================`,
    `# Art Studio — Promotion Intent Export Contract (Phase 32.0)`,
    `#`,
    `# Detected repo (best-effort): ${repoName}`,
    `# Recommended path: .github/workflows/${filename}`,
    `#`,
    `# Optional secret (only needed if your export URL requires auth):`,
    `#   TOOLBOX_API_TOKEN = <your API token>`,
    `#`,
    `# This workflow:`,
    `#   Job 1) Downloads PromotionIntentV1 JSON and uploads as artifact`,
    `#   Job 2) Downloads artifact and runs STRICT schema validation`,
    `#          (fails pipeline if required keys missing or intent_version != "v1")`,
    `# =====================================================================`,
    ``,
    workflow,
  ].join('\n')
}

// ==========================================================================
// cURL Snippet
// ==========================================================================

export function buildPromotionIntentCurl(baseUrl: string, sessionId: string): string {
  const url = `${baseUrl}/art/workflow/sessions/${encodeURIComponent(sessionId)}/promotion_intent`
  return [
    `curl -X POST "${url}"`,
    `  -H "Accept: application/json"`,
    `  -H "Content-Type: application/json"`,
  ].join(' \\\n')
}
