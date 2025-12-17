docs/SawLab/Saw_Path_Planner_2_1_Upgrade_Plan.md

Saw Path Planner 2.1 Upgrade Plan

Scope: Trim cuts · Advanced yield · Multi-board planning
Subsystem: Saw Lab 2.0 → saw_lab/path_planner.py

1. Current State (Planner 2.0)

File: saw_lab/path_planner.py
Core pieces:

SawCutOperation – conceptual cut (CROSSCUT only so far).

SawCutPlan – operations list + kerf loss + utilization + feasibility.

_compute_basic_yield() – sums piece lengths + kerf, checks against a single stock_length_mm.

_build_naive_cut_sequence() – simple left-to-right crosscuts on one board.

plan_saw_cuts_for_board() – single-board, single cut list, naive order.

Limitations:

No explicit trim at board ends.

No concept of minimum scrap length.

Only one board at a time; no multi-board strategy (e.g. we have 3 boards of length L).

Only one simple strategy (left-to-right, no reordering).

2.1 keeps the same API shape but adds real production behaviors.

2. Goals for Path Planner 2.1

Trim Cuts (End Allowances)

Support configurable trim at both board ends:

leading_trim_mm

trailing_trim_mm

Reflect trim cuts as explicit operations (cut_type="TRIM").

Include trim kerf in the yield math and scrap.

Advanced Yield (Scrap + Strategies)

Respect minimum scrap length (don’t leave tiny unusable tails).

Support basic ordering strategies:

AS_GIVEN – current behavior.

LONGEST_FIRST – place long pieces first to avoid stranded leftovers.

Improved feasibility / warnings:

“Pieces + trim + kerf exceed stock.”

“Cannot satisfy minimum scrap requirement.”

Multi-Board Planning

Handle multiple boards with the same cut list:

e.g. stock_boards = [2400, 2400, 2400] or [2400, 1200].

Decide:

which pieces go on which board,

in what order,

how many boards required.

Provide per-board plans plus aggregate metrics.

3. Data Model Extensions
3.1 New config / inputs

Add a small planner config model in path_planner.py (or saw_lab/config.py):

class SawPlannerConfig(BaseModel):
    leading_trim_mm: float = 0.0
    trailing_trim_mm: float = 0.0
    min_scrap_length_mm: float = 20.0

    # Cut ordering strategy
    ordering_strategy: Literal["AS_GIVEN", "LONGEST_FIRST"] = "AS_GIVEN"


In the short term, this can be built inside plan_saw_cuts_for_board() from SawLabConfig or hardcoded defaults. Later it can be passed in from RMOS / user presets.

3.2 Multi-board types

Add a new model for multi-board planning:

class SawBoardPlan(BaseModel):
    board_index: int
    stock_length_mm: float
    plan: SawCutPlan


class MultiBoardCutPlan(BaseModel):
    boards: list[SawBoardPlan]
    total_stock_length_mm: float
    total_piece_length_mm: float
    total_kerf_loss_mm: float
    total_scrap_length_mm: float
    average_utilization: float
    is_feasible: bool
    warnings: list[str] = []

4. Implementation Steps (2.1)
4.1 Step 1 – Trim Cuts for Single Board

Target: plan_saw_cuts_for_board() + _compute_basic_yield() + _build_naive_cut_sequence()

Changes:

Yield calculation:

Currently:

required = total_pieces + total_kerf


New:

required = (
    total_pieces
    + total_kerf
    + planner_cfg.leading_trim_mm
    + planner_cfg.trailing_trim_mm
)


Scrap:

scrap = stock_length_mm - required


Trim operations:

At the beginning of _build_naive_cut_sequence():

ops = []
seq = 0
offset = 0.0

if planner_cfg.leading_trim_mm > 0:
    ops.append(
        SawCutOperation(
            op_id="TRIM_LEAD",
            sequence_index=seq,
            cut_type="TRIM",
            start_offset_mm=0.0,
            cut_length_mm=planner_cfg.leading_trim_mm,
            kerf_mm=kerf_mm,
            description=f"Leading trim cut of {planner_cfg.leading_trim_mm:.1f} mm.",
        )
    )
    seq += 1
    offset += planner_cfg.leading_trim_mm + kerf_mm


After laying out all pieces, consider trailing trim as conceptual; it doesn’t need an operation unless you want a final cut at the end.

Warnings:

If board is only barely usable after trims, attach a warning:

if scrap < planner_cfg.min_scrap_length_mm:
    plan.warnings.append(
        f"Scrap ({scrap:.1f} mm) is smaller than the configured minimum usable scrap "
        f"({planner_cfg.min_scrap_length_mm:.1f} mm)."
    )

4.2 Step 2 – Advanced Yield (min scrap + ordering)

A. Ordering Strategy

Modify the desired_piece_lengths_mm sequence before calling _build_naive_cut_sequence():

pieces = list(desired_piece_lengths_mm or [])

if planner_cfg.ordering_strategy == "LONGEST_FIRST":
    pieces.sort(reverse=True)
elif planner_cfg.ordering_strategy == "AS_GIVEN":
    pass


B. Min scrap feasibility

Update _compute_basic_yield() to consider min_scrap_length_mm:

required = total_pieces + total_kerf + leading_trim + trailing_trim
scrap = stock_length_mm - required

if scrap < 0:
    feasible = False
elif scrap < min_scrap_length_mm:
    # Technically fits, but violates scrap policy.
    feasible = False
else:
    feasible = True


If infeasible due to scrap policy, provide a specific message:

if scrap < min_scrap_length_mm:
    warnings.append(
        f"Stock length leaves scrap ({scrap:.1f} mm) smaller than minimum scrap requirement "
        f"({min_scrap_length_mm:.1f} mm)."
    )

4.3 Step 3 – Multi-Board Planning

Add a new function:

def plan_saw_cuts_for_multiple_boards(
    stock_lengths_mm: list[float],
    desired_piece_lengths_mm: list[float],
    planner_cfg: SawPlannerConfig,
    kerf_mm: float,
) -> MultiBoardCutPlan:
    """
    Distribute desired pieces across multiple boards.

    Simple initial strategy:
        - Sort boards by length (descending).
        - For each board:
            - Try to place as many pieces as fit, respecting trim + kerf + min scrap.
            - Remove assigned pieces from the pending list.
        - If any pieces remain at the end, is_feasible = False.

    Future upgrades:
        - smarter packing / backtracking,
        - different strategies (e.g. shortest board first).
    """


Strategy 0 (baseline, greedy):

Sort stock_lengths_mm descending.

Maintain remaining_pieces list (optionally ordered by planner_cfg.ordering_strategy).

For each board:

Try to “take” a subset of remaining_pieces from the front until adding the next piece would violate yield (including trims + min scrap).

Call plan_saw_cuts_for_board() with that subset and current board length.

Store the resulting SawCutPlan into a new SawBoardPlan.

Remove assigned pieces from remaining_pieces.

At the end:

If remaining_pieces is empty → is_feasible = True

Otherwise → is_feasible = False + warning.

Aggregation in MultiBoardCutPlan:

Sum:

total_stock_length_mm – sum of board lengths.

total_piece_length_mm – sum of all SawCutPlan.total_piece_length_mm.

total_kerf_loss_mm – sum of all SawCutPlan.total_kerf_loss_mm.

total_scrap_length_mm – sum of all SawCutPlan.scrap_length_mm.

average_utilization – total_piece_length_mm / total_stock_length_mm.

Collect:

warnings from each board, plus:

“Not all pieces could be assigned to boards” if any remain.

5. API Contracts / Call Sites
5.1 RMOS / Saw Engine

Current:

saw_plan = plan_saw_cuts_for_board(cut_ctx, cfg)


2.1 additions:

Internally, plan_saw_cuts_for_board() will:

build SawPlannerConfig (trim, scrap, ordering),

call the new 2.1 logic.

Later, SawLabConfig can be extended to carry defaults:

default_trims_mm

min_scrap_length_mm

default_ordering_strategy

Multi-board call stays internal to Saw Lab at first.
When you’re ready, a future API might accept:

MultiBoardCutPlan plan_saw_cuts_for_stock_set(
    stock_boards_mm: list[float],
    desired_piece_lengths_mm: list[float],
    planner_cfg: SawPlannerConfig
)


but 2.1 can hide that behind the existing RMOS interfaces.

6. Testing Strategy (2.1)

Add new tests (or extend existing ones):

Trim behavior:

Given one board and one piece, verify:

trim allowances included in required length,

SawCutPlan has a leading trim operation when leading_trim_mm > 0.

Min scrap feasibility:

Case where pieces + kerf + trims fit the board but scrap < min_scrap_length_mm.

Expect is_feasible = False and a scrap-related warning.

Ordering strategies:

AS_GIVEN vs. LONGEST_FIRST produce different SawCutOperation sequences.

Use small cut lists like [100, 300, 200].

Multi-board:

Example:

boards: [1000, 1000]

pieces: [400, 400, 400]

Verify that all pieces are assigned and is_feasible = True.

Example where there isn’t enough total stock:

boards: [500, 500]

pieces: [400, 400, 400]

Expect is_feasible = False and a clear warning.

7. Rollout Plan

Phase A – Single Board Enhancements

Implement SawPlannerConfig.

Add trims, min scrap, ordering strategies.

Keep current API signatures.

Add tests for these behaviors.

Phase B – Multi-Board Planning

Implement MultiBoardCutPlan + SawBoardPlan.

Implement plan_saw_cuts_for_multiple_boards().

Add targeted tests.

Phase C – RMOS Exposure (Optional)

Decide if multi-board planning stays an internal Saw Lab concern or is exposed to:

RMOS API,

UI (e.g. “we need 2 boards of 2400mm”).

Phase D – Optimization / Strategy Experiments

Add more ordering strategies (e.g. “best fit first”).

Add toggles to select strategies via context or config.

TL;DR:
Path Planner 2.1 turns your skeleton into a production-grade saw planner with:

Trim cuts,

Enforced minimum scrap,

Basic ordering strategies,

Multi-board planning,

while preserving the same top-level RMOS → Saw Lab → Toolpath Builder flow.