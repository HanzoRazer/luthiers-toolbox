# C2/C3 Authority Model Refinement

Status: Deferred by design

## Purpose

This record captures a deferred governance design question at the C2/C3 seam.

It does not change GAMS v1.
It does not reopen C2.
It does not alter implementation behavior.

## Current formulation

Operational role and authority state are independent dimensions.

This is the formulation currently used by GAMS v1.

## Candidate discussion formulation (non-adopted)

This candidate formulation is archived for future design discussion and must not
be cited as adopted governance; alternative formulations remain open.

Authority state is invariant under representation, serialization, routing,
storage location, namespace, and operational role.

Authority changes only through an explicitly governed promotion event.

## Reason for deferral

This question concerns the load-bearing anti-collision principle at the C2/C3
boundary.

It is deferred not because it is unimportant, but because it is highly important.
Changing this formulation requires a dedicated governance design discussion and
must not occur opportunistically during documentation cleanup or implementation
work.

## Evaluation criteria

A future discussion should determine whether the candidate refinement:

- preserves all guarantees of the current two-axis model
- improves precision without reducing explanatory value
- composes cleanly with C2, GAMS, the Format Flow Matrix, Canonical DXF Correctness, and future C3 enforcement
- clarifies authority transitions without deciding authoritative geometry origin

## Non-goals

This record does not:

- decide authoritative geometry origin
- promote vectorizer output
- promote IBG output
- alter DXF serializer behavior
- create schema enforcement
- add CI gates
- change code
