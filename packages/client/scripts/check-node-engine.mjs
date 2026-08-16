#!/usr/bin/env node
/**
 * Assert the running Node satisfies the client's declared engine floor.
 *
 * The floor lives in exactly one place: the "engines.node" field of
 * packages/client/package.json. This script READS that field rather than
 * restating it, so the four client Dockerfiles cannot drift from the manifest
 * (or from each other) the next time the floor moves.
 *
 * Run it after package.json is available in the image and before `npm ci`, so a
 * wrong base image fails with this message instead of an opaque Vite/ESM error
 * several minutes later.
 *
 * Why this rather than npm's own `engine-strict=true`: that setting makes npm
 * refuse to install when ANY package in the tree declares an unmet engines
 * range, including transitive dev dependencies whose ranges are stale or
 * narrower than reality. This tree already carries such a case (an optional
 * @napi-rs binary asking for ^22.20 || ^24.12 || >=25), so engine-strict would
 * fail installs that are in fact fine. This guard checks only the floor the
 * client itself declares, which is the constraint we actually mean.
 *
 * Usage:  node scripts/check-node-engine.mjs [path/to/package.json]
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
export const DEFAULT_MANIFEST = resolve(HERE, "..", "package.json");

/** [major, minor, patch] from "20.19.4" / "v20.19.4" / "22". Missing parts are 0. */
export function parseVersion(text) {
  const cleaned = String(text).trim().replace(/^v/, "");
  const parts = cleaned.split(".", 3).map((n) => Number.parseInt(n, 10));
  if (parts.length === 0 || Number.isNaN(parts[0])) {
    throw new Error(`Cannot parse version ${JSON.stringify(String(text))}`);
  }
  return [parts[0], parts[1] || 0, parts[2] || 0];
}

export function compare(a, b) {
  for (let i = 0; i < 3; i += 1) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return 0;
}

/**
 * Does `version` satisfy one comparator clause?
 *
 * Deliberately supports only the forms this repo uses — `>=x.y.z`, `>x.y.z`,
 * `^x.y.z` and a bare `x.y.z`. Anything else throws rather than being guessed
 * at, because a silently mis-parsed range is worse than no check at all.
 */
export function satisfiesClause(version, clause) {
  const text = clause.trim();
  if (text === "*") return true;

  const match = /^(>=|>|\^)?\s*v?(\d+(?:\.\d+){0,2})$/.exec(text);
  if (!match) {
    throw new Error(
      `Unsupported semver clause ${JSON.stringify(clause)} in engines.node. ` +
        "Extend scripts/check-node-engine.mjs to handle it - do not weaken the check."
    );
  }
  const [, operator, raw] = match;
  const bound = parseVersion(raw);

  if (operator === undefined) return compare(version, bound) === 0; // exact pin
  if (operator === ">=") return compare(version, bound) >= 0;
  if (operator === ">") return compare(version, bound) > 0;
  return satisfiesCaret(version, bound);
}

/**
 * npm's caret: "compatible with", i.e. no change to the leftmost non-zero part.
 *
 *   ^1.2.3 -> >=1.2.3 <2.0.0
 *   ^0.2.3 -> >=0.2.3 <0.3.0
 *   ^0.0.3 -> >=0.0.3 <0.0.4
 *
 * A 0-major is unreachable for a Node engine range, but this helper is exported
 * and unit-tested, so it implements the rule rather than the convenient
 * approximation "same major". Treating ^0.2.3 as "any 0.x" would accept 0.9.0.
 */
export function satisfiesCaret(version, bound) {
  if (compare(version, bound) < 0) return false;
  const [bMajor, bMinor] = bound;
  if (bMajor !== 0) return version[0] === bMajor;
  if (bMinor !== 0) return version[0] === 0 && version[1] === bMinor;
  return version[0] === 0 && version[1] === 0 && version[2] === bound[2];
}

export function satisfies(version, range) {
  return range
    .split("||")
    .some((clause) => satisfiesClause(version, clause));
}

/** Fallback used only when package.json has no engines.node (diagnostic / bootstrap). */
export const FALLBACK_FLOOR = ">=22.12.0";

export function readDeclaredFloor(manifestPath = DEFAULT_MANIFEST) {
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const range = manifest?.engines?.node;
  if (!range) {
    console.warn(
      `WARN: ${manifestPath} has no "engines.node"; using FALLBACK_FLOOR=${FALLBACK_FLOOR}.`
    );
    return FALLBACK_FLOOR;
  }
  return range;
}

function main(argv) {
  const manifestPath = resolve(argv[2] ?? DEFAULT_MANIFEST);
  let range;
  try {
    range = readDeclaredFloor(manifestPath);
  } catch (err) {
    console.error(`FATAL: ${err.message}`);
    return 1;
  }

  const running = process.versions.node;
  if (!satisfies(parseVersion(running), range)) {
    console.error(
      `FATAL: Node ${running} does not satisfy the client engine floor "${range}" ` +
        `(declared in ${manifestPath}).`
    );
    return 1;
  }
  console.log(`Node ${running} satisfies the client engine floor "${range}".`);
  return 0;
}

// Only act as a CLI when executed directly; importable as a library otherwise.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv));
}
