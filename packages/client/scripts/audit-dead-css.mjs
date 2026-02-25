#!/usr/bin/env node
/**
 * audit-dead-css.mjs
 *
 * Detects dead CSS selectors in Vue SFC <style scoped> blocks and CSS Module files.
 * Run: node scripts/audit-dead-css.mjs [--fail-on-dead] [--verbose]
 *
 * Exit code 1 when --fail-on-dead is set and dead selectors are found (CI gate).
 *
 * Approach:
 *   - For <style scoped> in .vue files: extracts class selectors from <style>,
 *     extracts class names from <template>, and diffs them.
 *   - For .module.css files: finds the importing .vue file, extracts styles.XXX
 *     references from <script> + <template>, and diffs against defined classes.
 *
 * Limitations:
 *   - Dynamic class bindings with computed strings may cause false positives.
 *     Mark such selectors with a `/* dynamic *​/` comment to exclude them.
 *   - Does not trace class usage across child components (scoped styles
 *     and CSS Modules are per-component by design).
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, extname } from "node:path";

const SRC = join(import.meta.dirname, "..", "src");

const failOnDead = process.argv.includes("--fail-on-dead");
const verbose = process.argv.includes("--verbose");

// ── Helpers ────────────────────────────────────────────────────────────────

/** Recursively collect files matching a predicate. */
function walk(dir, predicate, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      // Skip node_modules, dist, __tests__, coverage
      if (["node_modules", "dist", "__tests__", "coverage"].includes(entry)) continue;
      walk(full, predicate, out);
    } else if (predicate(full)) {
      out.push(full);
    }
  }
  return out;
}

/** Extract class selectors from a CSS string. Returns Set<string>. */
function extractCssClasses(css) {
  const classes = new Set();
  // Remove comments (but preserve `/* dynamic */` marker check)
  const dynamicMarked = new Set();
  const commentRe = /\/\*[\s\S]*?\*\//g;
  let match;
  while ((match = commentRe.exec(css)) !== null) {
    if (/dynamic/i.test(match[0])) {
      // Find the next selector after this comment
      const after = css.slice(match.index + match[0].length).match(/\.([a-zA-Z_][\w-]*)/);
      if (after) dynamicMarked.add(after[1]);
    }
  }

  const stripped = css.replace(commentRe, "");

  // Match class selectors: .className (possibly followed by :pseudo, [attr], etc.)
  const classRe = /\.([a-zA-Z_][\w-]*)/g;
  while ((match = classRe.exec(stripped)) !== null) {
    const cls = match[1];
    // Skip pseudo-elements/classes that look like class names
    if (!dynamicMarked.has(cls)) {
      classes.add(cls);
    }
  }
  return { classes, dynamicMarked };
}

/** Extract class names used in a Vue template string. */
function extractTemplateClasses(template) {
  const classes = new Set();
  const dynamicPrefixes = [];

  // Detect Vue <Transition name="xxx"> and auto-register its 6 class patterns
  const transRe = /<(?:Transition|transition)\s[^>]*name="([^"]+)"/g;
  let tMatch;
  while ((tMatch = transRe.exec(template)) !== null) {
    const name = tMatch[1];
    for (const suffix of [
      "-enter-active", "-leave-active",
      "-enter-from", "-leave-from",
      "-enter-to", "-leave-to",
    ]) {
      classes.add(name + suffix);
    }
  }

  // Static class="foo bar baz"
  const staticRe = /\bclass="([^"]*)"/g;
  let m;
  while ((m = staticRe.exec(template)) !== null) {
    for (const cls of m[1].split(/\s+/)) {
      if (cls) classes.add(cls);
    }
  }

  // Dynamic :class="{ active: ... }" or :class="[...]"
  const dynRe = /:class="([^"]*)"/g;
  while ((m = dynRe.exec(template)) !== null) {
    const expr = m[1];
    // Extract identifiers that look like class names from objects: { 'class-name': expr }
    const objRe = /['"]?([\w-]+)['"]?\s*:/g;
    let m2;
    while ((m2 = objRe.exec(expr)) !== null) {
      classes.add(m2[1]);
    }
    // Also pick up plain string class names in arrays: ['foo', 'bar']
    const arrRe = /['"]([a-zA-Z_][\w-]*)['"]/g;
    while ((m2 = arrRe.exec(expr)) !== null) {
      classes.add(m2[1]);
    }
    // Detect string-concatenated class patterns like `'risk-' + level`
    // and add all CSS classes matching that prefix as "potentially dynamic"
    const concatRe = /['"]([a-zA-Z_][\w-]*-)['"]\s*\+/g;
    while ((m2 = concatRe.exec(expr)) !== null) {
      dynamicPrefixes.push(m2[1]);
    }
    // Back-tick template literals: `risk-${level}`
    const tmplRe = /`([a-zA-Z_][\w-]*-)\$\{/g;
    while ((m2 = tmplRe.exec(expr)) !== null) {
      dynamicPrefixes.push(m2[1]);
    }
  }

  return { classes, dynamicPrefixes };
}

/** Extract styles.XXX references from a script/template string. */
function extractModuleClassRefs(content) {
  const classes = new Set();
  const re = /styles\.([a-zA-Z_]\w*)/g;
  let m;
  while ((m = re.exec(content)) !== null) {
    classes.add(m[1]);
  }
  // Also handle styles['xxx'] and styles["xxx"]
  const bracketRe = /styles\[['"]([a-zA-Z_][\w-]*)['"]\]/g;
  while ((m = bracketRe.exec(content)) !== null) {
    classes.add(m[1]);
  }
  return classes;
}

// ── Section extractors for .vue files ──────────────────────────────────────

function extractSection(content, tag) {
  // Handles <template>, <script ...>, <style ...>
  const openRe = new RegExp(`<${tag}(\\s[^>]*)?>`, "i");
  const closeRe = new RegExp(`</${tag}>`, "i");
  const openMatch = openRe.exec(content);
  if (!openMatch) return null;
  const start = openMatch.index + openMatch[0].length;
  const closeMatch = closeRe.exec(content.slice(start));
  if (!closeMatch) return null;
  return content.slice(start, start + closeMatch.index);
}

function extractStyleBlocks(content) {
  const blocks = [];
  const re = /<style(\s[^>]*)?>[\s\S]*?<\/style>/gi;
  let m;
  while ((m = re.exec(content)) !== null) {
    const attrs = m[1] || "";
    const isScoped = /\bscoped\b/.test(attrs);
    const isModule = /\bmodule\b/.test(attrs);
    const bodyStart = m[0].indexOf(">") + 1;
    const bodyEnd = m[0].lastIndexOf("</style>");
    const body = m[0].slice(bodyStart, bodyEnd);
    blocks.push({ body, isScoped, isModule, attrs });
  }
  return blocks;
}

// ── Audit logic ────────────────────────────────────────────────────────────

const findings = [];

// 1. Audit <style scoped> in .vue files
const vueFiles = walk(SRC, (f) => extname(f) === ".vue");

for (const file of vueFiles) {
  const content = readFileSync(file, "utf-8");
  const template = extractSection(content, "template") || "";
  const styleBlocks = extractStyleBlocks(content);

  for (const block of styleBlocks) {
    if (!block.isScoped) continue; // only audit scoped blocks (non-scoped are global)

    const { classes: cssClasses, dynamicMarked } = extractCssClasses(block.body);
    const { classes: templateClasses, dynamicPrefixes } = extractTemplateClasses(template);

    // Also check script for programmatic class usage
    const script = extractSection(content, "script") || "";
    const scriptClassRe = /['"]([a-zA-Z_][\w-]*)['"]/g;
    let sm;
    while ((sm = scriptClassRe.exec(script)) !== null) {
      templateClasses.add(sm[1]);
    }

    // Also scan script for dynamic prefix patterns
    const scriptConcatRe = /['"]([a-zA-Z_][\w-]*-)['"]\s*\+/g;
    while ((sm = scriptConcatRe.exec(script)) !== null) {
      dynamicPrefixes.push(sm[1]);
    }
    const scriptTmplRe = /`([a-zA-Z_][\w-]*-)\$\{/g;
    while ((sm = scriptTmplRe.exec(script)) !== null) {
      dynamicPrefixes.push(sm[1]);
    }

    const dead = [...cssClasses].filter(
      (cls) =>
        !templateClasses.has(cls) &&
        !dynamicMarked.has(cls) &&
        !dynamicPrefixes.some((p) => cls.startsWith(p))
    );

    if (dead.length > 0) {
      findings.push({
        file: relative(SRC, file),
        type: "scoped",
        dead,
        total: cssClasses.size,
      });
    }
  }
}

// 2. Audit .module.css files
const cssModuleFiles = walk(SRC, (f) => f.endsWith(".module.css"));

for (const cssFile of cssModuleFiles) {
  const css = readFileSync(cssFile, "utf-8");
  const { classes: cssClasses, dynamicMarked } = extractCssClasses(css);

  // Find the importing .vue file (search co-located files)
  const dir = join(cssFile, "..");
  const baseName = relative(dir, cssFile);

  let usedClasses = new Set();
  let importingFile = null;

  // Search all .vue files in the same directory
  for (const vf of vueFiles) {
    const vContent = readFileSync(vf, "utf-8");
    if (vContent.includes(baseName)) {
      importingFile = vf;
      usedClasses = extractModuleClassRefs(vContent);
      break;
    }
  }

  if (!importingFile) {
    if (verbose) {
      console.log(`  ⚠ No importer found for ${relative(SRC, cssFile)}`);
    }
    continue;
  }

  // Also pick up composes: targets (they reference other classes in the same module)
  const composesRe = /composes:\s*(\w+)/g;
  let cm;
  while ((cm = composesRe.exec(css)) !== null) {
    // If a class is referenced via composes, it's "used" within the module
    // But only if the composing class is itself used
    // For simplicity, don't count composes-only as "used"
  }

  const dead = [...cssClasses].filter(
    (cls) => !usedClasses.has(cls) && !dynamicMarked.has(cls)
  );

  if (dead.length > 0) {
    findings.push({
      file: relative(SRC, cssFile),
      type: "module",
      dead,
      total: cssClasses.size,
      importer: relative(SRC, importingFile),
    });
  }
}

// ── Report ─────────────────────────────────────────────────────────────────

const totalDead = findings.reduce((sum, f) => sum + f.dead.length, 0);
const totalAudited = vueFiles.length + cssModuleFiles.length;

console.log(`\n🔍 CSS Dead-Code Audit — ${totalAudited} files scanned\n`);

if (findings.length === 0) {
  console.log("✅ No dead CSS selectors detected.\n");
} else {
  console.log(`⚠  ${totalDead} potentially dead selector(s) in ${findings.length} file(s):\n`);

  for (const f of findings) {
    const label = f.type === "module"
      ? `[CSS Module] ${f.file} (imported by ${f.importer})`
      : `[scoped] ${f.file}`;
    console.log(`  ${label}`);
    console.log(`    Dead (${f.dead.length}/${f.total}): ${f.dead.join(", ")}`);
    console.log();
  }

  if (verbose) {
    console.log("Tip: Mark intentionally-dynamic selectors with /* dynamic */ to suppress.\n");
  }
}

if (failOnDead && totalDead > 0) {
  console.log("❌ --fail-on-dead: exiting with code 1\n");
  process.exit(1);
}
