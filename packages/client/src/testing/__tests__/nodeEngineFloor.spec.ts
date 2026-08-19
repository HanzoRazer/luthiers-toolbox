// Node engine floor: one declaration, many consumers.
//
// packages/client/package.json "engines.node" is the source of truth. The four
// client Dockerfiles assert it by *reading* that field
// (scripts/check-node-engine.mjs), so they cannot drift. Everything else that
// pins a Node version — CI jobs, compose files, .env.example, .nvmrc — is plain
// configuration that nothing validates at runtime. This spec is what keeps
// those honest, and it is why the guard was worth centralizing rather than
// copying a fifth time.

import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { parseVersion, satisfies } from "../../../scripts/check-node-engine.mjs";

const CLIENT_ROOT = resolve(__dirname, "..", "..", "..");
const REPO_ROOT = resolve(CLIENT_ROOT, "..", "..");

const read = (rel: string, from = REPO_ROOT) =>
  readFileSync(resolve(from, rel), "utf8");

const DECLARED_FLOOR: string = JSON.parse(read("package.json", CLIENT_ROOT))
  .engines.node;

/**
 * A bare major such as "22" is not a version — `node:22-alpine` and
 * `setup-node: 22` both float to the newest 22.x. So the question this spec can
 * answer is "can this pin ever satisfy the floor", i.e. does the major line
 * intersect it. Whether the *resolved* runtime clears the floor is the
 * Dockerfile guard's job, which is precisely why that guard still exists after
 * being centralized.
 */
const probeVersion = (declared: string) =>
  declared.includes(".") ? declared : `${declared}.9999.9999`;

function expectSatisfiesFloor(version: string, where: string) {
  expect(
    satisfies(parseVersion(probeVersion(version)), DECLARED_FLOOR),
    `${where} pins Node ${version}, which cannot satisfy the declared floor ` +
      `"${DECLARED_FLOOR}" in packages/client/package.json`,
  ).toBe(true);
}

interface LockEntry {
  engines?: { node?: string };
  optional?: boolean;
}

/** The lowest version each declared lane admits, e.g. ">=22.12.0" -> "22.12.0". */
function laneStarts(range: string): string[] {
  return range
    .split("||")
    .map((clause) => /v?(\d+(?:\.\d+){0,2})/.exec(clause)?.[1])
    .filter((v): v is string => Boolean(v));
}

/**
 * Dependencies that require more Node than the declared floor admits.
 *
 * The floor exists to describe what the tree actually needs. If a dependency
 * demands more than we declare, the declaration is a fiction: the build clears
 * the guard and then runs on a runtime the dependency does not support.
 */
function dependenciesAboveTheFloor(): string[] {
  const lock = JSON.parse(read("package-lock.json", CLIENT_ROOT)) as {
    packages: Record<string, LockEntry>;
  };
  const starts = laneStarts(DECLARED_FLOOR);
  const offenders: string[] = [];

  for (const [path, meta] of Object.entries(lock.packages)) {
    const required = meta?.engines?.node;
    // Optional packages are skipped by npm when they do not apply.
    if (!required || meta?.optional) continue;

    // Only a single-lane ">=x" range expresses one unambiguous floor.
    const bound = /(?:^|\|\|)\s*>=\s*v?(\d+(?:\.\d+){0,2})\s*$/.exec(
      required.trim(),
    );
    if (!bound) continue;

    const weakest = starts.find(
      (start) => !satisfies(parseVersion(start), `>=${bound[1]}`),
    );
    if (weakest) {
      offenders.push(
        `${path.replace("node_modules/", "")} needs node ${required}, but the ` +
          `declared floor admits ${weakest}`,
      );
    }
  }
  return offenders;
}

const NODE_VERSION_SOURCES: Array<[string, () => string]> = [
  ["docker-compose.yml", () => read("docker-compose.yml")],
  ["docker-compose.production.yml", () => read("docker-compose.production.yml")],
  [".env.example", () => read(".env.example")],
  ["docker/client/Dockerfile", () => read("docker/client/Dockerfile")],
  [
    "docker/client/Dockerfile.production",
    () => read("docker/client/Dockerfile.production"),
  ],
  [
    "docker/client/Dockerfile.railway",
    () => read("docker/client/Dockerfile.railway"),
  ],
  ["packages/client/Dockerfile", () => read("Dockerfile", CLIENT_ROOT)],
  [
    ".github/workflows/containers.yml",
    () => read(".github/workflows/containers.yml"),
  ],
];

const CLIENT_DOCKERFILES = NODE_VERSION_SOURCES.filter(([name]) =>
  name.includes("Dockerfile"),
);

describe("client Node engine floor", () => {
  it("is declared in package.json", () => {
    expect(DECLARED_FLOOR).toBeTruthy();
  });

  it("is satisfied by every dependency that declares one", () => {
    const offenders = dependenciesAboveTheFloor();
    expect(offenders, offenders.join("\n")).toEqual([]);
  });

  it("is satisfied by .nvmrc", () => {
    expectSatisfiesFloor(read(".nvmrc", CLIENT_ROOT).trim(), ".nvmrc");
  });

  it("is satisfied by every NODE_VERSION default", () => {
    let seen = 0;
    for (const [name, load] of NODE_VERSION_SOURCES) {
      for (const m of load().matchAll(
        /NODE_VERSION(?:\s*[:=]\s*|\s*:\s*\$\{NODE_VERSION:-)\s*"?(\d+(?:\.\d+)*)"?/g,
      )) {
        seen += 1;
        expectSatisfiesFloor(m[1], name);
      }
    }
    expect(seen, "found no NODE_VERSION defaults to check").toBeGreaterThan(6);
  });

  it("is satisfied by every workflow node-version", () => {
    const dir = resolve(REPO_ROOT, ".github", "workflows");
    let seen = 0;
    for (const file of readdirSync(dir).filter((f) => f.endsWith(".yml"))) {
      const text = readFileSync(resolve(dir, file), "utf8");
      for (const m of text.matchAll(/node-version:\s*"?(\d+(?:\.\d+)*)"?/g)) {
        seen += 1;
        expectSatisfiesFloor(m[1], `.github/workflows/${file}`);
      }
    }
    expect(seen, "found no workflow node-version pins to check").toBeGreaterThan(
      0,
    );
  });

  it("is not restated by hand in any Dockerfile", () => {
    // The whole point of check-node-engine.mjs is that the range appears once.
    // A Dockerfile that spells out version numbers is a copy that can drift.
    for (const [name, load] of CLIENT_DOCKERFILES) {
      const text = load();
      expect(text, `${name} must invoke the shared engine check`).toContain(
        "check-node-engine.mjs",
      );
      expect(
        text.includes("process.versions.node"),
        `${name} restates the floor inline instead of reading package.json`,
      ).toBe(false);
    }
  });
});
