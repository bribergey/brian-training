# Personalized Nutrition Product Specification

Status: research and architecture baseline for review
Branch: `codex/personalized-nutrition-engine`
Started: 2026-07-25

## Product promise

The Macros experience should answer four questions without pretending to know more than the data supports:

1. What is my target today, and why?
2. What have I logged so far?
3. What is probably remaining, and how certain is that estimate?
4. What is the most useful next action?

The system must separate facts, estimates, and coaching.

## Product boundaries

Canonical:

- profile and goal phase,
- calibrated maintenance estimate,
- versioned daily target,
- structured food facts and their provenance,
- deterministic consumed and remaining arithmetic,
- explicit user corrections and approvals.

Advisory:

- AI-extracted food candidates,
- uncertain portion estimates,
- meal suggestions,
- target explanations,
- trend summaries,
- proposed calibration changes.

The advisory layer cannot silently change canonical data.

## System design

```text
Profile + measurements + goal phase
                    |
Training schedule and completed sessions
                    v
       Deterministic target engine
        policy version + engine version
                    |
         Immutable day-plan revision
                    |
       +------------+-------------+
       |                          |
       v                          v
Structured food facts       Macros dashboard
provenance + revisions      target / logged /
       |                    remaining / confidence
       +------------+-------------+
                    v
            Optional AI coach
       explain / clarify / suggest
```

The target engine should be a pure function. Given the same versioned policy and the same input snapshot, it must always return the same result and checksum. It performs no model call, database read, random operation, or implicit clock lookup.

Conceptual contract:

```text
calculateNutritionTargets(policy, profileSnapshot, dayContext)
  -> target ranges
  -> reason codes
  -> applied / ignored / stale / missing inputs
  -> policy version
  -> engine version
  -> input hash
  -> confidence
```

## Macros tab

The Macros tab is the primary product, not a chat transcript.

### Top section

- Date navigation shared with Daily Log.
- Day type such as “Normal resistance day” or “Rest / light day.”
- Planned workout and training time where available.
- A short deterministic explanation such as “Carbohydrate is higher because Day C is scheduled.”
- Completeness badge: target ready, target provisional, missing current weight, or needs calibration.

### Progress section

Cards or bars for:

- energy,
- protein,
- carbohydrate,
- fat.

Each shows:

- target band,
- confirmed amount,
- estimated amount,
- remaining range,
- visual uncertainty.

Secondary indicators can include:

- fiber,
- hydration when enough data exists,
- protein feeding opportunities,
- selected micronutrients only when the underlying food detail supports them.

The UI must say “minimum logged so far” when food logging is incomplete. Missing food is not zero intake.

### Food timeline

Reuse the Daily Log's food-entry identity, time, description, and photos. Add analysis status:

- `confirmed`
- `estimated`
- `needs_clarification`
- `stale`
- `excluded`

Low-confidence items should ask a small, useful question:

- “About how much olive oil?”
- “Was that handful of walnuts closer to 30 g or 60 g?”
- “How many grams per scoop on this protein label?”
- “Was the restaurant rice about one cup or two?”

The goal is not to force weighing every meal. It is to clarify the few foods that dominate uncertainty.

### Next-action section

Before chat exists, deterministic suggestions can already be useful:

- protein below pace: suggest a known protein serving,
- carbohydrate low before training: suggest a tolerated carb option,
- fat already near the upper target: prefer leaner next options,
- fiber low late in the day: suggest fruit, legumes, or vegetables,
- logging incomplete: ask whether Brian is done logging food.

Suggestions should use ranges and Brian's accepted food history.

### Weekly calibration

Show:

- current goal phase,
- observed seven-day weight trend,
- desired rate band,
- number of complete weight and food days,
- training completion,
- current maintenance estimate and confidence,
- proposed adjustment and reasons.

No change is applied until Brian approves it.

### Calculation drawer

Expose:

- policy and engine versions,
- input date and freshness,
- body weight used,
- day classification,
- applied modifiers,
- ignored or missing signals,
- target revision history.

This makes the system explainable without requiring AI.

## Optional Coach tab

This can follow the first dashboard. The initial release already uses AI for food estimation; the optional Coach is a conversational explanation and planning layer, not the calculation engine.

Good coach tasks:

- explain why today's target differs,
- propose a meal that fits the remaining target range,
- ask clarifying questions about a meal,
- summarize weekly patterns,
- compare training and rest days,
- propose an allowlisted correction or calibration review.

The coach receives a server-built, allowlisted facts object. It does not query arbitrary tables and cannot write directly.

Every response should return:

- a concise answer,
- references to the canonical facts used,
- suggestions with confidence,
- allowlisted proposed actions,
- whether each action requires confirmation,
- a safety level and reason code.

Numeric cards are always rendered from the database, never copied from model prose.

## Food analysis

AI-assisted food estimation is part of the first usable release. The user can keep writing normal descriptions instead of entering every ingredient and measurement. The system returns an explicit estimate with assumptions and improves recurring foods from corrections.

```text
Description and optional photo
  -> item and portion candidates
  -> known-food or food-database match when available
  -> nutrient estimate from the best available evidence
  -> user review when confidence is low
  -> accepted nutrient fact revision
```

Use saved user-confirmed foods and product labels first, then USDA FoodData Central where practical. A model-only estimate is allowed when that is the only convenient option, but it remains visibly estimated. Preserve:

- FoodData Central ID,
- source data type,
- retrieval or publication date,
- selected portion and grams,
- nutrient values and units,
- derivation method,
- user acceptance state.

Provenance tiers:

- A: weighed amount or entered/scanned package label.
- B: accepted database match with known portion.
- C: database match with inferred portion.
- D: model-only estimate.

Confidence belongs to each item and nutrient, not just the whole meal.

The current `daily_logs.food_entries` JSON remains the source observation during migration. Do not destructively replace it. Normalize by stable entry ID plus a content hash. When a description, photo, or portion changes, mark prior analysis stale and create a revision.

The existing `user_profile.macro_targets` and `macro_targets_history` JSON should be treated as legacy import data. Current records contain calorie/macronutrient reconciliation errors and lack versioned formulas or provenance. Preserve them for audit, validate them during migration, and replace their authority with typed, versioned nutrition-plan and daily-target rows.

## Data model

Use mirrored staging and production tables, authenticated row-level security, and migration-backed schema history.

### `nutrition_policy_versions`

Immutable scientific and product policy:

- semantic version,
- status,
- parameters and caps,
- evidence references,
- checksum,
- effective dates.

### `nutrition_goal_phases`

- user,
- goal type,
- start and optional end,
- desired rate,
- manual overrides,
- policy version,
- approval metadata.

### `nutrition_day_plan_revisions`

- user and local date,
- revision and status,
- goal phase,
- linked planned session key,
- actual workout state,
- input snapshot and hash,
- policy and engine versions,
- typed energy/macronutrient/fiber/fluid targets,
- reason codes,
- confidence and freshness,
- lock state.

### `nutrition_food_entry_revisions`

- user and date,
- stable Daily Log food-entry ID,
- source text hash,
- time,
- raw description,
- photo references,
- revision and stale state.

### `nutrition_food_items`

- entry revision,
- parsed food and preparation,
- amount and unit,
- grams,
- source food identity,
- review state,
- confidence.

### `nutrition_food_item_nutrients`

- item revision,
- nutrient code,
- amount and unit,
- low and high range,
- provenance tier,
- derivation method.

### `nutrition_calibration_runs`

- user,
- measurement window,
- completeness metrics,
- observed trend,
- target trend,
- proposed adjustment,
- explanation codes,
- approval state,
- resulting policy revision.

### `nutrition_ai_runs`

- user and purpose,
- prompt, schema, and model versions,
- requested and returned provider/model,
- input/context checksum,
- output validation state,
- request generation ID,
- token, cost, and latency metadata,
- typed error,
- privacy and retention mode.

### `nutrition_food_memory`

- user-scoped canonical name and aliases,
- representative serving description,
- calorie, protein, carbohydrate, fat, and fiber estimate,
- source and assumptions,
- confidence and user-confirmed state,
- use count and timestamps.

Optional chat tables can be added later. Keep core macro and energy columns typed and queryable. JSON snapshots are for audit and replay, not the only source of truth.

Any aggregate view over user data must preserve caller-scoped row-level security.

Related schema hardening:

- Enforce one profile row per user.
- Add a user time zone for local-day target generation.
- Plan a safe conversion of session dates from text to a real date type.
- Add session duration and optional RPE/RIR if workload-sensitive fueling is expected.
- Decide whether more than one measurement per day is valid; if it is, store a measurement timestamp plus source and conditions.

## OpenRouter and server boundary

The existing app is static. It must never contain an OpenRouter secret.

Use authenticated Supabase Edge Functions:

- `nutrition-plan`: deterministic target generation only.
- `nutrition-analyze-food`: extraction and clarification.
- `nutrition-coach`: explanations and suggestions over server-assembled facts.

Production rules:

- Pin a concrete model version; do not use an auto-router or “latest” alias.
- Use strict JSON Schema with `additionalProperties: false`.
- Require providers that support every requested parameter.
- Allow only tested model/provider fallbacks.
- Deny provider data collection and require zero-data-retention-capable routing where available.
- Keep prompt/response logging and data-sharing discounts off for personal health data.
- Send a pseudonymous user identifier, never name, email, or date of birth.
- Separate staging and production keys.
- Apply model allowlists, spend caps, request limits, and timeouts.
- Store usage, returned model/provider, validation, and error metadata.
- Keep the deterministic dashboard available during AI outages.

Food descriptions, OCR, photo text, and user notes are untrusted input. Separate them from instructions, cap lengths, and test prompt injection.

## Evaluation and drift controls

### Deterministic engine

- Golden test vectors for every goal and day type.
- Identical inputs produce identical outputs and hashes.
- Output values are nonnegative and internally energy-consistent.
- Readiness modifiers never exceed policy caps.
- Missing or stale values reduce confidence rather than becoming zero.
- Revisions append; they do not overwrite history.

### Data and security

- Authenticated row-level security on every user table.
- Cross-user read and write denial tests.
- Idempotent retries and duplicate meal-analysis tests.
- Source hashes invalidate stale food analysis.
- Migration reconciliation counts between JSON observations and normalized entries.

### AI

Use a fixed benchmark set containing:

- weighed foods,
- labels and serving sizes,
- simple ingredients,
- mixed home-cooked meals,
- restaurant meals,
- drinks and alcohol,
- vague portions,
- photo-only entries,
- edited entries,
- malicious prompt-like text.

Track:

- schema-valid response rate,
- clarification recall,
- food-match accuracy,
- per-macro error and uncertainty coverage,
- user correction rate,
- stale-analysis detection,
- unsafe-answer rate,
- latency,
- cost per accepted meal.

Invalid schema, impossible units, internal calorie/macro inconsistency, or an out-of-policy claim fails closed to “Could not analyze—please review.” Never silently coerce it into a canonical total.

## Delivery sequence

### First testable loop

- Calculate a stable, versioned calorie and macro target from the current profile, latest measurement, goal, activity, lower-carbohydrate preference, and training/rest day type.
- Show calories, protein, carbohydrate, and fat consumed and remaining.
- Analyze ordinary Daily Log food descriptions through an authenticated server function.
- Store estimates, confidence, assumptions, and source metadata with each food entry.
- Let the user correct an estimate without re-entering a meal.
- Recognize and reuse recurring foods and meals while typing.
- Keep incomplete days explicitly incomplete; missing food is never counted as zero.

Exit: the user can log a normal day, see useful estimated progress immediately, correct it, and receive a better default the next time the food recurs.

### Calibration and outcome learning

- Use sufficient complete weight, food, activity, and training data.
- Generate bounded adjustment proposals.
- Require explicit approval.
- Analyze how food on day N relates to sleep, energy, stool, and other outcomes on day N+1 and over longer windows.
- Keep these outcome associations separate from the target calculation and label them as observational rather than causal.

Exit: the system can learn Brian's maintenance while preserving an auditable history.

### Optional Coach

- Add explanations, meal suggestions, clarifications, and weekly reviews.
- Show fact references and proposed actions.
- No arbitrary writes and no silent target changes.

Exit: coach usefulness and safety exceed the deterministic experience in evaluation and real staging use.

## Current product decisions

- The dashboard must show total calories as well as protein, carbohydrate, and fat.
- Targets are stable by day type and do not react to daily sleep, stress, soreness, stool, or energy scores.
- The preferred logging mode is quick AI estimation from ordinary text, with better amounts added when convenient.
- Recurring foods and meals should become reusable user-specific memory.
- The active fasting, lower-carbohydrate, and no/low-added-sugar preferences come from the current profile, not from hardcoded documentation.
- Historical outcome analysis links food on one day to recovery signals on following days; it does not rewrite the day's target.
- Hydration, micronutrients, and a conversational coach can follow after the core loop is useful.

## Technical references

- [USDA FoodData Central API](https://fdc.nal.usda.gov/api-guide/)
- [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Edge Function authentication](https://supabase.com/docs/guides/functions/auth)
- [Supabase Edge Function secrets](https://supabase.com/docs/guides/functions/secrets)
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter provider routing and data policy](https://openrouter.ai/docs/guides/routing/provider-selection)
- [OpenRouter data collection](https://openrouter.ai/docs/guides/privacy/data-collection)
- [OpenRouter model fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks)
- [OpenRouter guardrails](https://openrouter.ai/docs/guides/features/guardrails/overview)
