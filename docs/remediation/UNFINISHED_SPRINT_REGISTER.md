# BR-001 — Unfinished Sprint Register

> Work previously authorized by a valid Dev Order / sprint but only **partially implemented**. Kept
> distinct from generic technical debt (charter §4). Each entry links to its
> [adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md) record. Populated in Commit 3.

## Record schema

```text
Originating program            (Dev Order / sprint id)
Original objective
Authoritative handoff          (doc path)
Relevant commits or PRs
Implemented scope
Missing scope
Current architectural validity (still valid / partially / invalid)
Tests currently present
Completion recommendation      (complete / narrow-and-complete)
Supersession recommendation    (supersede / retire — with reason)
Blocking decisions             (owner rulings needed)
Adjudication ledger ID         BR-NNN
```

## Register

> Populated in Commit 3 from Dev Order / handoff / branch discovery. An item is `UNFINISHED_SPRINT_WORK`
> only when it was **authorized** (a valid Dev Order exists) but not completed — never a never-approved
> capability (that is `ENHANCEMENT`) and never merely wrong behavior (that is `CONFIRMED_DEFECT`).

_(No entries yet — populated in Commit 3.)_
