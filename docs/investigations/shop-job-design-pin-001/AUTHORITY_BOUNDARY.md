# Authority boundary — design snapshot

`LtbDesignSnapshotV1` stores a copy of a design and the identities required to find it later. It does not decide that the design may be built.

## Ownership

| Concern | Owner |
|---|---|
| Commercial and production job | CNC-Production-Shop `job_id` |
| Mutable design workspace | LTB `project_id` |
| Immutable design snapshot | This package |
| Official estimate and quote revision | CNC-Production-Shop |
| CAM package assembly and review | CAM Creation Studio |
| Physical evidence vocabulary | Physical Engineering Mesh |
| Manufacturing authorization | Readiness, CAM, and a person. Not this snapshot. |

## Not this snapshot

The record does not verify the CNC job. `verification_status` cannot be set to anything but `UNVERIFIED_EXTERNAL_REFERENCE`. Creating a snapshot does not call CNC-Production-Shop.

The record does not approve evidence, readiness, CAM, or manufacturing. Those words are not fields of the snapshot types. A project blob may still contain `manufacturing_state.status`, including `cam_approved`, because that value is part of the copied design state. The snapshot does not read it and does not treat it as permission.

Artifact and generator references carry identifiers and digests. A digest proves bytes, not approval.

The package imports the standard library and itself. It does not import routers, the project service, CAM generators, G-code writers, readiness mutators, physical-policy activation, or an HTTP client. Capture does not execute a generator and does not open a socket.

Successful checks of `fixtures/cnc_consumer_conformance.json` prove the synthetic snapshot bytes. They do not prove the design is correct or that anyone may manufacture it.
