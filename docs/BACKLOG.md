# Production Shop — Implementation Backlog

Items here are fully analyzed and scoped. Each one has a source, a
specific file path, and enough context to implement without re-researching.
Nothing here was invented in a planning meeting — every item came from
reading actual code.

---


## TEST-001 — Fix 33 pre-existing test failures

**Status:** Known, not investigated
**Priority:** Medium
**Effort:** Unknown until investigated

33 tests consistently fail in pytest runs.
They are pre-existing and unrelated to recent work.

**First step:** Run pytest with -v and capture
the failing test names:
```bash
pytest services/api/tests/ -v 2>&1 | grep "FAILED" | head -40
```

**Then:** Triage into:
- Genuinely broken (fix)
- Skipped intentionally (add skip marker)
- Environment-dependent (document)

Do not fix them now — just document in BACKLOG.

---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.





