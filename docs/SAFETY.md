# Operator Safety — The Production Shop

## What RMOS Does

The RMOS (Risk Management and Operations System) evaluates every job before it reaches the machine.

- **GREEN:** All checks pass — job may proceed
- **YELLOW:** Warnings present — operator must acknowledge before proceeding
- **RED:** Hard failure — job is blocked; parameters must be changed

RMOS does NOT replace machine guarding, operator training, or safe CNC practices. It is a pre-cut validation layer, not a safety interlock.

## G-code Path Safety

Every G-code-emitting endpoint in this system passes through one of:

- RMOS feasibility gate (neck, body, rosette ops)
- Preflight gate with BCamMachineSpec limits (Z ceiling 101.6mm, safe Z 10mm enforced)
- Explicit operator acknowledgment (YELLOW gate)

The CAM Workspace wizard requires GREEN or acknowledged YELLOW before enabling download.

## BCAM 2030A Specific

- **Safe Z:** 10mm (clearance height between moves)
- **Z travel:** 101.6mm (4 inches) hard ceiling
- **Tool changes:** M1 optional stop — machine pauses, operator changes tool, presses cycle start
- **Tool length compensation:** G43 applied after every tool change

## What the System Does Not Do

- Does not replace physical machine guarding
- Does not verify workholding or fixture security
- Does not detect tool breakage during a run
- Does not substitute for operator CNC training
- Does not guarantee chip-free or burn-free cuts (feed/speed recommendations are starting points)

## Probe Cycles

G38.2 probing cycles are used for channel depth verification. If the probe does not trigger within the expected travel, the program stops with an alarm. Verify probe wiring and calibration before use.

## Saw Lab

Saw Lab operations include kickback risk assessment (LOW/MEDIUM/HIGH). HIGH kickback risk blocks the operation. MEDIUM requires acknowledgment. Always use appropriate push sticks and blade guards regardless of risk rating.

## Emergency Stop

Know the location of your machine's E-stop before starting any program. The system cannot stop a running program — only the machine operator can.
