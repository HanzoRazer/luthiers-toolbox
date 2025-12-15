1️⃣ Branch Strategy

The plan mentions creating feature/client-migration, but you're currently on feature/rmos-2-0-skeleton.

Answer: 1 → B

B) Create a new branch feature/client-migration off the current branch

Reasoning:

feature/rmos-2-0-skeleton already contains the RMOS 2.0 + CAM + calculators spine work.

The client migration depends on that direction, so we want to keep it as the base.

A dedicated feature/client-migration branch keeps this big UI merge isolated and easy to review/revert if needed.

So:

git checkout feature/rmos-2-0-skeleton
git checkout -b feature/client-migration

2️⃣ Duplicate File Resolution (55 files)

For the 55 files that exist in both locations…

Answer: 2 → B (with a bias rule)

B) Do a diff comparison and keep whichever has more features

Operational rule for GitHub:

Default assumption: packages/client/src is the canonical, “new” home.

For a duplicate:

Compare client/src/... vs packages/client/src/....

If packages/client version is clearly newer/more integrated → keep it, but pull in any missing behavior from the legacy version when feasible.

If the legacy client/src version has clearly more UI/logic → keep legacy as the body, but place it into packages/client/src and add a // TODO: merged from legacy client note for human follow-up.

Never silently delete a duplicate; always keep at least one version in packages/client/src.

So answer B, but with: “prefer packages/client version unless the legacy one obviously has more functionality.”

3️⃣ Router Wiring

Should I add routes now or later?

Answer: 3 → B

B) Just migrate the files and leave router wiring for a follow-up task

Reasoning:

Phase 1–4 should be about file rescue and structure, not UX decisions.

Once components exist under packages/client/src, we can wire routes in a focused “Router wiring” step (still within the same branch, but later commit).

That also avoids broken routes while things are half-migrated.

So for now: copy views/components in, but leave router/index.ts unchanged until a dedicated routing pass.

4️⃣ API Endpoint Binding (Phase 6)

Are /api/ai-cam/... and friends live?

Right now, the design for those endpoints exists (we’ve specced them in the backend waves), but they may not be fully implemented in the current repo state. To avoid wiring to something that doesn’t exist yet:

Answer: 4 → B

B) Add placeholder/TODO comments for future wiring

Instructions for GitHub:

Migrate GCodeExplainer.vue, WiringWorkbench.vue, etc., into packages/client.

Keep existing dummy/local behavior if they already have it.

Where API calls should live, insert:

// TODO: wire to /api/ai-cam/explain-gcode once backend is in place
// TODO: wire to /api/calculators/wiring/... for real physics


No hard dependency on endpoints until we confirm backend routes exist and are stable.

5️⃣ Test Suite

Compare system has .spec.ts tests – what to do?

Answer: 5 → B

B) Just migrate tests but defer running them

Nuanced version that matches the plan in the doc :

Tests should be copied into the monorepo test tree so we don’t lose them.

It’s OK if they don’t pass immediately; don’t treat failing tests as a blocker for this migration PR.

If the agent wants to run tests, that’s fine – but failures should be documented as TODOs, not “stop execution.”

So: migrate tests alongside the components, but don’t stop the work if they’re currently red.

6️⃣ Execution Mode

Execute all phases at once or in chunks?

Answer: 6 → B

B) Execute phase-by-phase with checkpoints for your approval

This matches the “incremental with commits after each phase” approach described in the doc.

Practical instructions:

Phase 0 → commit

Phase 1–2 (Toolbox calculators) → commit

Phase 3 (Compare) → commit

…and so on

At each phase, it’s easy for you to glance at the diff and say “yes, keep going.”

TL;DR Answer Block for GitHub

You can paste this directly back into Copilot / the GitHub agent:

1. Branch Strategy: B – Create feature/client-migration off feature/rmos-2-0-skeleton.

2. Duplicate Files: B – Do a diff; prefer packages/client version unless legacy clearly has more features, then merge logic and keep one version under packages/client/src.

3. Router Wiring: B – Migrate files now, wire routes in a later step.

4. API Binding: B – Add TODO placeholder comments; don’t wire to /api/ai-cam until backend endpoints are confirmed.

5. Tests: B – Migrate tests, but don’t block on them passing yet.

6. Execution Mode: B – Execute phase-by-phase with commits and checkpoints.