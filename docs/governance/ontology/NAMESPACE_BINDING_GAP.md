# Namespace→Domain Binding Gap — DEFERRED

**Status:** NAMED — binding authorship deferred to a governance increment
**Layer:** ontology / authority topology
**Raised by:** `scripts/governance/check_namespace_authority_drift.py` (advisory v1)
**Date:** 2026-08-16

---

## The gap, in one paragraph

`docs/governance/ontology/authority_chain_registry.json` declares **domains** and
**domain ownership**. It does not declare which **code namespace** belongs to
which domain. There is no `namespace_bindings` key, and nothing else in the
authority topology supplies that mapping. So for any given code namespace, the
topology cannot currently answer "who owns this?" — not because the answer is
contested, but because it was never written down.

This is a **missing layer**, not a defect in any tool that reports it.

---

## What it means for the drift detector

The namespace/authority drift detector consumes the authority topology to
adjudicate whether a candidate change drifts from declared authority. With no
binding layer, it returns `INSUFFICIENT_EVIDENCE` for essentially every code
namespace.

**That verdict is correct output, not a bug.** It is the detector reporting the
state of the topology accurately. `INSUFFICIENT_EVIDENCE` is deliberately:

- **not** a flagged verdict — a namespace is never suspect merely for being unbound;
- **advisory** severity — it describes a governance gap, not a code problem;
- **exit 0** — v1 is advisory throughout.

---

## The rule this note exists to protect

> **The detector MAY CONSUME authority. It MAY NOT CREATE authority.**

A future maintainer will, in good faith, look at a wall of
`INSUFFICIENT_EVIDENCE` and want to make the tool "more useful" by inferring the
binding — matching the namespace against a domain name, matching it against a
declared owner, or sniffing the module path. **Do not.**

Inference would be authority synthesis. The detector would begin manufacturing
the very ownership facts it exists to check candidate changes against, and every
downstream verdict would inherit an ownership claim that no governance record
ever made. A wrong `DECLARED_EXTENSION` is far more damaging than an honest
`INSUFFICIENT_EVIDENCE`, because it silently blesses drift.

The temptation is real and specific. Production declares both a `geometry` and a
`topology` domain, so namespaces like `body_outline` and `retopo` look bindable
to any human or heuristic. They are not bound, and until governance says
otherwise the honest verdict is that we do not know.

This rule is enforced executably. `tests/governance/test_namespace_authority_drift.py`
contains an **anti-inference guard**: a bait topology whose domain names and owner
names collide head-on with the probed namespace names, asserting that none of
them resolves. Four heuristics — exact domain-name match, fuzzy substring match,
owner-name match, and path sniffing — were each injected during development and
each was caught by that guard. If you add inference, those tests fail. That is
their purpose.

---

## Closing the gap — a separate governance action

Authoring bindings is **not** a detector change. It is a governance act, because
it declares ownership facts that carry authority. It belongs in its own
increment, with whatever ratification the authority model requires.

Shape, when it happens:

```jsonc
// docs/governance/ontology/authority_chain_registry.json
"namespace_bindings": {
  "<code_namespace>": { "domain": "<declared domain>", "concept": "<declared owner>" }
}
```

The detector already reads this key if present (`AuthorityTopology.namespace_bindings`)
and honours a binding only when its `domain` is a real declared domain. **No
detector change is required to consume bindings once they exist.**

### Expected consequences when bindings land

- Bound namespaces stop returning `INSUFFICIENT_EVIDENCE` and start returning
  substantive verdicts — `DECLARED_EXTENSION`, `DUPLICATE_AUTHORITY`, and so on.
  The engine already proves every one of those against a synthetic bound topology.
- Several dogfood tests assert the *current* factual condition and will
  legitimately need updating. They are written to say so in their docstrings —
  notably `test_real_registry_has_no_namespace_binding_layer`,
  `test_retopo_dogfood_reflects_binding_gap`, and
  `test_boe_control_not_flagged_by_age`. Changing them is expected; changing the
  anti-inference guard is not.
- Only then is it reasonable to consider promoting selected verdicts from
  advisory to blocking. Doing that before real bindings exist would gate on a
  topology that cannot answer the question.

---

## What this note is not

It is not a sprint plan, a binding proposal, or a schema change. It records a
known, deliberate gap and the reason the obvious shortcut is forbidden, so that
the boundary survives the next maintainer who does not have this context.
