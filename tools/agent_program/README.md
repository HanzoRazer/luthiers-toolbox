# `tools/agent_program/`

Read-only analysis of the Agent Program incident ledger.

## What it is for

`analyze_incidents.py` loads
`docs/governance/agents/agent_program_incidents_002a.json`, validates its shape,
and reports the inputs a human uses to decide whether a second agent authority
boundary is justified.

**It does not make that decision, and it cannot act.** It has no subprocess, no
network, no Git or `gh` invocation, and no write path — enforced by tests in
`tests/agent_program/test_incident_analysis.py`.

## Usage

```bash
# summary of the committed ledger (--ledger defaults to it)
python -m tools.agent_program.analyze_incidents

# or point at another ledger
python -m tools.agent_program.analyze_incidents --ledger path/to/ledger.json
```

Output reports `schema_version`, `review_order`, `terminal_decision`, the incident
count, `recurrence_counts`, `uncovered_recurring_families`,
`necessity_test_can_pass`, and `authority_contract_required`.

Validation is not a separate mode: `render_summary()` validates first and raises
`IncidentLedgerError` listing every schema error, so a malformed ledger fails the
run rather than producing a partial summary. There is no flag that reports
"valid" and stops — validity is only ever observed as *the summary rendered at
all*.

## The two rules worth knowing before reading output

Both are deliberately strict, and both bias **toward** finding a new agent
necessary. Neither can manufacture a "not justified" conclusion by hiding
evidence.

**`recurrence_eligible()`** — an incident counts toward recurrence only with
`independent_incident: true`, at least one `evidence_refs` entry, and a non-empty
`underlying_incident_id`. A real failure that was never durably evidenced counts
zero. Output will therefore look sparser than lived experience, by design.

**`uncovered_recurring_families()`** — a family is covered only when *one whole
control* covers *every* recurrence-eligible member (all YES on Grounding, or all
YES on deterministic sufficiency). A family whose members are covered by
*different* controls stays **uncovered**, because neither control handles it
alone. `UNKNOWN` and `PARTIAL` are never promoted to `YES`.

Both rules are pinned by tests so they cannot drift silently.

## Functions that are not decision inputs

`summarize_control_coverage()` returns raw per-field tallies. It does not group by
family, does not filter to recurrence-eligible incidents, and does not distinguish
`UNKNOWN` from `PARTIAL`. It is a diagnostic aid for eyeballing ledger shape, and
is deliberately not called by `render_summary()` or
`agent_002_necessity_inputs()`. Do not read a mostly-`YES` tally as coverage.

## If you extend this

The tests forbid `subprocess`, `gh pr`, `git commit` and similar strings in this
package. That check is intentionally blunt: the guarantee being protected is that
this tool cannot act on the repository, and a blunt check is harder to defeat
accidentally than a clever one. If a legitimate change trips it, the right move is
to question whether the tool is still read-only — not to loosen the check.
