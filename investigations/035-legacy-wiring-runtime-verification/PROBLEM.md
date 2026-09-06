# PROBLEM — FALSE INTEGRATION / EXECUTION-PATH DIVERGENCE

## Failure class

```text
FALSE INTEGRATION / EXECUTION-PATH DIVERGENCE
```

An intended implementation exists and may pass isolated tests, but the real
application path does not traverse it, causing the system to execute a
different, obsolete, placeholder, fallback, or otherwise unintended path.

The observable user or manufacturing effect is often reported as:

```text
"the technology does not work"
```

when the real condition may be:

```text
"the intended implementation is not what production executes"
```

## Three separate propositions

These must not be collapsed:

```text
1. CODE EXISTS
   An implementation, module, or documented capability is present in the tree.

2. TESTS PASS
   Isolated or direct-import tests exercise that implementation (or a fixture
   that looks like it).

3. RUNTIME EXECUTES THE INTENDED IMPLEMENTATION
   The current production entrypoint dereferences and calls that
   implementation, producing the intended terminal effect, consumed by the
   intended downstream consumer.
```

A true (1) and (2) with a false (3) is false integration.

## Distinctions that are not automatically defects

- A **fallback** is not automatically D3. An expected fail-closed guard may be
  correct behavior.
- A **duplicate route** is not automatically D2. Parallel implementations may
  be intentional; runtime must show which handler actually fires.
- A **spy on the source module** that reports zero calls is not proof of
  non-execution. Callers may have bound the symbol earlier. Spy location must
  be the dereference point.
- Current Toolbox Vectorizer is a **control**, not this failure class's seed.

## Governing question (per specimen)

> When the real current production entrypoint is exercised, does execution
> reach the implementation that is supposed to provide the capability?

For every specimen distinguish:

```text
ENTRYPOINT
EXPECTED IMPLEMENTATION
ACTUAL IMPLEMENTATION
TERMINAL EFFECT
DOWNSTREAM CONSUMER
TEST PATH
```
