# Proposal tools and data contract

All calls use the service's pinned environment and user. Never supply SQL or a
user_id. Staging uses the synthetic codex_qa account; production uses Brian.
Read the live exercise catalog for exact names and units. New shared exercises
require a separate PM-reviewed addition; never invent catalog names.

prepare_program_proposal arguments:

- kind: week, month, or adjustment
- summary: concise progress analysis, decisions and useful advice
- start_date: exact YYYY-MM-DD for a new week (date/timezone confirmed with Brian)
- block_name: descriptive name for a new monthly blueprint
- rows: complete exercise objects as below

The service assigns UUIDs, month/week/internal identifiers, user_id and dates.
Do not invent these values. It also binds the proposal to its source snapshot.

## New weekly rows

Every row needs day, order_index (warm-up is 0), exercise, session_label (day focus,
not Upper A or Month/Week), superset_group (string or null), sets, reps (text),
weight (numeric), rest (text), suggested_sets, coach_notes, evidence, scheme.

Each suggested_sets entry has exactly:

```json
{"set":1,"reps":"5","weight":40,"rest":"2:00"}
```

There must be exactly sets entries, numbered consecutively. Each preset reps value must be a single positive numeric string, such as "5"
or "30"; the app uses numeric fields and ranges like "5–8" would render blank.
For time/distance use the catalog rep_type unit (sec, min or km), without a unit
suffix in the numeric field. Put target ranges and fallback choices in notes. Use 0 for bodyweight, the catalog's unit for other weights (e.g. per-hand
dumbbells). Row weight summarizes the highest working-set weight. coach_notes and
row reps must explain any differing top/back-off or ramp set targets. The service
derives the stored row reps/rest summaries from the exact per-set presets. Rest per
set is M:SS. Evidence must name the actual dated prior sets, or explicitly state
that no direct prior non-deload evidence exists and name what you used instead.

scheme must match the monthly contract: straight (same working weights),
top_backoff (heavier first set, equal lighter back-off weights), ramp (increasing
weights), bodyweight. Warm-up may use scheme warmup, null sets/reps/weight/rest
and null suggested_sets, with a specific routine in coach_notes.

## Monthly blueprint rows

For every exercise supply both normal and deload rows. Each row needs week_type,
day, order_index, exercise, session_label, superset_group, sets, reps, weight,
rest, suggested_sets, and contract. The contract contains strings for:

```json
{"scheme":"straight","reps":"5–8","effort":"exercise-specific target",
 "progression":"what earns the next increase","fallback":"what to do on a miss",
 "rationale":"why this exercise and structure; warm-ups contain the actual routine"}
```

The monthly table lacks reps and per-set columns. The service saves the complete
versioned contract and reference suggested_sets into internal_notes. It computes
the next month number, archives only the prior current month and inserts both
templates in one transaction. Deload mirrors all slots and supersets. Monthly
reference loads are starting proposals, not permanent weekly loads.

Legacy templates do not have reviewed contracts. Prepare a new monthly blueprint
before generating a new week from them. Read the old approved normal block for
structure and current logs for starting loads; don't copy the hiking template.

## Mid-week adjustments

Read exact rows with get_program_rows. Supply each complete replacement row with
its existing id and all weekly fields, scheme, evidence and change_reason.
Adjustments may change load/reps/sets/rest/notes, not move dates/exercise slots or
edit logged/skipped workouts. New structure changes must be explained explicitly.
Changing the exercise catalog or replacing exercise slots goes to the PM.

## What the tools do not do

prepare_program_proposal does not write workouts. It returns validation errors or
a proposal id. Fix validation errors before presenting a plan. The service sends
the full exact plan and approval control. Only authenticated Brian can approve;
approvals expire, superseded drafts cannot be applied, stale data requires a fresh
proposal, and the database must match the requested rows before success is sent.
