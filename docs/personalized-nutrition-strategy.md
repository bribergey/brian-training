# Personalized Nutrition Strategy

Status: research baseline for review
Branch: `codex/personalized-nutrition-engine`
Started: 2026-07-25

This document defines the scientific strategy for Brian's nutrition system. It is a coaching and product specification, not a diagnosis or a substitute for care from a physician or credentialed sports dietitian.

## Executive decision

The system should use a stable, versioned nutrition prescription with a small number of controlled adjustments:

1. Estimate energy needs, then calibrate them from observed intake and multiweek body-weight trends.
2. Keep protein nearly constant every day.
3. Keep dietary fat within a health-supporting band.
4. Change carbohydrate and total energy primarily according to the goal phase and planned or completed training demand.
5. Use sleep, energy, soreness, stress, illness, stool, hunger, and performance as monitoring signals. Do not convert a single subjective rating into a pseudo-precise macro change.
6. Use deterministic rules for targets and arithmetic. AI may interpret food, explain a target, and suggest meals, but it does not own the prescription.

The target engine must be useful without AI. This is the central safeguard against model drift.

## Brian-specific starting context

Read-only production checks on 2026-07-25 found:

- Male, age 46, height 180 cm.
- Last recorded measurement: 75 kg and 16% body fat, dated 2026-04-01. It is too old to treat as a current calibration point.
- Current profile goal: lean bulk. The broader profile also lists strength, muscle gain, fat loss, recomposition, endurance, and general health, so the primary goal and acceptable rate of gain still need explicit confirmation.
- High activity outside the gym, with four preferred lifting days per week.
- Recent training is consistent and high volume: 15 normal resistance sessions in the last 28 days, generally about 23–28 logged work sets, plus a few small extra sessions.
- Current eating preference is primarily plant-based but flexible, with gluten-free and lectin-free preferences.
- Current eating window is approximately noon–7 p.m.; the training window begins as early as 10 a.m.
- Fifteen Daily Logs cover 2026-07-11 through 2026-07-25. Food was recorded on 12 days, with 32 entries total.
- The profile already contains unvalidated `macro_targets` and `macro_targets_history` JSON. The current stored values are 2,500 kcal, 149 g protein, 289 g carbohydrate, and 83 g fat for training days; 2,275 kcal, 149 g protein, 207 g carbohydrate, and 83 g fat for rest days. The training macros reconcile to about 2,499 kcal, but the rest macros reconcile to about 2,171 kcal—a 104 kcal mismatch. At least one history record also fails calorie/macro reconciliation. These values have no durable formula, evidence, input snapshot, or engine version and must not become the new system's source of truth.

The food log is useful coaching context but not yet sufficient for accurate macro totals. Many entries use intentionally convenient descriptions such as “handful,” “bowl,” “a lot,” restaurant dishes, oil, tahini, or mixed meals. Those are normal ways to log a life, but they create large calorie and fat uncertainty unless portions are clarified.

### Patterns worth testing, not declaring as facts

- Most logged days contain two meals plus an occasional shake. That may make a lean-gain calorie target and evenly distributed protein harder to reach inside a seven-hour window.
- Several days concentrate a large amount of protein in a two- or three-scoop shake. Splitting that across another feeding may improve distribution without changing total protein.
- Nuts, olive oil, tahini, bacon, restaurant stir-fries, and mixed dishes can make fat and calories vary substantially even when the visible meal volume looks similar.
- Carbohydrate intake appears variable and is often concentrated later in the day. Morning training may therefore be fasted or lightly fueled.
- The logs include useful whole-food anchors—legumes, sweet potato, rice, eggs, tuna, vegetables, fruit, yogurt, and mixed animal foods—but quantities and brands are not yet precise enough to assess protein, fiber, or micronutrient adequacy reliably.

These observations should guide clarification prompts and dashboard design. They should not be turned into definitive nutrient claims until the food entries have structured portions and provenance.

## Provisional prescription

These are evidence-grounded starting ranges, not final daily targets. Energy and carbohydrate targets remain provisional until current weight and a calibration window exist.

### Energy

Athlete-oriented resting-energy equations place Brian's estimated resting requirement at roughly 1,800–1,900 kcal/day using the stale April measurement. Equations can be wrong by hundreds of calories for an individual, and an activity multiplier adds more uncertainty.

The app should therefore:

- Show an initial maintenance range, not false precision.
- Collect at least 14–28 days of reasonably complete intake, morning weight, training, and activity data.
- Use the seven-day average of morning weight rather than individual weigh-ins.
- Adjust maintenance no more often than weekly, and preferably after two complete weeks.
- Never “eat back” wearable exercise calories one for one.

For a lean-gain phase, start conservatively—approximately 5% above calibrated maintenance—and aim for roughly 0.1–0.25% body weight gain per week for a trained recreational lifter. At 75 kg that would be about 0.08–0.19 kg per week. If waist or fat gain rises without useful strength or training progress, reduce the surplus. If weight and performance do not move despite good adherence, increase it modestly.

### Protein

- Working range for maintenance or lean gain: 1.8–2.0 g/kg/day.
- At 75 kg: approximately 135–150 g/day.
- Keep the daily target stable across rest and training days.
- Use three or four meaningful feedings where practical, commonly about 0.4–0.55 g/kg per feeding for a muscle-gain pattern.
- At 75 kg: approximately 30–40 g per feeding.
- Total daily protein matters more than perfect timing.
- For a predominantly plant-based pattern, favor the upper end and use protein-complete or complementary foods such as soy, tofu/tempeh, legumes, and soy or blended pea/rice isolates. A flexible diet can also use eggs, dairy, fish, and meat according to preference.

If the goal changes to a calorie deficit, the target would usually move toward roughly 1.8–2.4 g/kg/day, with the higher end reserved for leaner people or more aggressive deficits.

### Carbohydrate

Carbohydrate is the main daily adjustment:

- General resistance-training starting range: about 3–5 g/kg/day.
- At 75 kg: approximately 225–375 g/day before reconciling with the calibrated energy target.
- Rest or light day: lower end of the personal range.
- Normal resistance day: middle of the personal range.
- High-volume legs/full-body, conditioning, long session, or two-a-day: upper end.

For ordinary fed lifting sessions under about 60–75 minutes, intra-workout carbohydrate is usually unnecessary. Higher-volume, fasted, glycogen-depleted, long, or twice-daily training is more likely to benefit from additional carbohydrate.

For training in the morning:

- Best lean-gain option: move training into the eating window or allow a small pre-training feeding.
- A practical pre-training option is a tolerable protein serving plus roughly 15–30 g carbohydrate.
- A normal mixed meal with protein and carbohydrate one to four hours before training is sufficient when scheduling allows.

The fasting window is an adherence preference, not a metabolic requirement. If it makes energy, protein distribution, performance, or recovery worse, the nutrition strategy should win.

### Fat

- Use approximately 20–35% of energy, commonly 25–30% for the working target.
- Do not routinely prescribe below 20% of energy.
- Emphasize unsaturated sources.
- Keep enough room in the energy budget for training carbohydrate.

Because oil, nuts, tahini, and restaurant cooking are frequent in the current logs, the product should prioritize portion clarification for these foods. A one-line “handful” or “olive oil” estimate can meaningfully change the day's calorie and fat total.

### Fiber and food quality

- Use a target band rather than a pass/fail number.
- A useful starting target is about 30–40 g/day, consistent with approximately 14 g per 1,000 kcal and the adult male adequate intake.
- Increase gradually and pair with adequate fluid.
- Spread plant foods across vegetables, fruit, legumes, whole grains or tolerated starches, nuts, and seeds.
- Reduce fiber and fat immediately before a demanding session if they cause gastrointestinal discomfort; preserve overall daily or weekly diet quality.

### Hydration

- The adult male total-water adequate intake is approximately 3.7 L/day, including water contained in food. It is not a mandatory plain-water target.
- Short indoor lifting sessions usually need water and normal meals, not automatic electrolyte products.
- For prolonged or hot sessions, measure personal sweat rate from pre/post body weight, fluid consumed, urine, and session duration.
- Avoid both meaningful dehydration and drinking enough to gain body mass during exercise.
- Sodium replacement should respond to measured or strongly suspected sweat losses, heat, session length, and medical context—not a universal number.

### Micronutrients and supplements

Use age- and sex-specific Dietary Reference Intakes. Do not invent “athlete RDAs.”

For a primarily plant-based but flexible pattern, periodically assess:

- vitamin B12,
- vitamin D,
- calcium,
- iron/ferritin when risk or symptoms justify it,
- iodine,
- zinc,
- omega-3 intake,
- potassium and overall produce variety.

Do not recommend high-dose iron, vitamin D, calcium, zinc, or magnesium from symptoms alone.

Creatine monohydrate is the strongest default performance supplement for this training pattern:

- 3–5 g/day is a standard maintenance dose.
- Loading is optional.
- Product, dose, and actual frequency should become structured profile data.

Caffeine can help performance, but sleep sensitivity and timing matter. It should not become an automatic recommendation, especially when energy and sleep are already low.

## Dynamic target policy

The app should assign each day a versioned type:

- `rest_light`
- `resistance_normal`
- `resistance_high`
- `conditioning_endurance`
- `mixed_or_double`
- `recovery_illness`

The training schedule provides the initial type. Completed training may create a new revision.

Rules:

- Protein remains stable.
- Fat remains stable or changes only modestly.
- Carbohydrate carries most training-day variation.
- Total energy varies modestly across the week while preserving the goal-phase weekly average.
- A moved or skipped workout creates a new day-plan revision. It does not erase the original plan.
- A day plan should lock once food logging is in use unless Brian explicitly asks to recalculate after a workout change.

Daily Log signals have bounded authority:

- One poor sleep, energy, stress, or soreness score changes coaching emphasis, not the target arithmetic.
- Persistent multi-day patterns may generate a proposed calibration or recovery review.
- Illness should suspend aggressive deficits and prompt recovery guidance.
- Stool data can support hydration or gastrointestinal context; it does not directly change macros.
- Low energy can indicate underfueling. The app must not respond automatically by lowering carbohydrates or calories.

## Calibration policy

The engine should propose, not silently apply, a maintenance change.

Minimum inputs:

- At least three morning weights per week for 14 days, with more frequent entries preferred and a completeness threshold.
- A seven-day rolling average or robust trend estimate.
- Food-log completeness status for each day.
- Planned and completed training classification.
- A simple activity measure such as steps or a stable outside-gym activity class.
- Goal phase and desired rate.

Calibration review:

1. Compare observed weight trend with the goal-rate band.
2. Check food-log completeness and uncertainty.
3. Check training completion, performance, hunger, energy, and recovery trends.
4. Propose a small energy change with an explanation.
5. Require explicit approval.
6. Create a new target-policy revision; never rewrite prior targets.

## Safety limits

The app may flag patterns but should not diagnose Relative Energy Deficiency in Sport, nutrient deficiency, or an eating disorder.

Escalate to a sports dietitian or clinician for persistent or concerning patterns such as:

- unintended or rapid weight loss,
- persistent fatigue, dizziness, cold intolerance, or performance decline,
- recurrent illness or injury,
- low libido or other hormonal symptoms,
- persistent gastrointestinal pain, vomiting, diarrhea, constipation, or blood in stool,
- suspected anemia or deficiency,
- food fear, bingeing, purging, compulsive exercise, or obsessive tracking,
- kidney, liver, cardiovascular, endocrine, or metabolic disease,
- aggressive cutting, repeated fasting, or high-dose supplement use despite poor recovery.

## Inputs still required

Before final targets are activated:

- Current morning body weight and a new waist measurement.
- At least 14 days of morning weight entries.
- Explicit primary goal for the next phase and acceptable rate of gain or loss.
- Typical session duration and effort/RPE; current set count alone is not an energy-expenditure measure.
- A fallback rule for days beyond the scheduled-program horizon. The current program only extends through 2026-07-26, so “unknown” must remain distinct from “rest.”
- Typical daily steps or another stable activity measure.
- Protein-powder brand and nutrition label.
- Current supplement list with dose and timing.
- Relevant diagnoses, medications, food allergies/intolerances, and clinician-ordered labs Brian wants considered.
- Usual caffeine and alcohol amount/timing.
- Whether the fasting window is flexible on morning training days.
- Representative pre/post training weights for hot, long, or unusually sweaty sessions if hydration periodization is desired.

## Evidence quality

Strongest:

- adequate energy availability,
- sufficient total protein,
- higher carbohydrate availability as training duration and intensity rise,
- health-supporting fat and fiber,
- individualized hydration,
- correcting confirmed micronutrient shortfalls,
- creatine and context-appropriate caffeine.

Moderate:

- even protein distribution,
- higher carbohydrate on unusually high-volume lifting days,
- conservative surplus for hypertrophy,
- pre-sleep protein,
- time-restricted eating as an adherence option.

Uncertain or highly individual:

- the exact surplus that maximizes muscle gain,
- an exact carbohydrate formula for each resistance workout,
- macro changes calculated from sleep, soreness, stress, stool, or subjective energy,
- photo-only calorie estimates without portion confirmation,
- generic sodium prescriptions,
- most supplements marketed for soreness, hormones, inflammation, or sleep.

## Primary references

- [IOC 2023 consensus statement on Relative Energy Deficiency in Sport](https://bjsm.bmj.com/content/57/17/1073)
- [Academy, ACSM, and Dietitians of Canada: Nutrition and Athletic Performance](https://pubmed.ncbi.nlm.nih.gov/26920240/)
- [ISSN position stand: protein and exercise](https://link.springer.com/article/10.1186/s12970-017-0177-8)
- [Morton et al. protein supplementation meta-analysis](https://pubmed.ncbi.nlm.nih.gov/28698222/)
- [Helms et al. protein during caloric restriction](https://pubmed.ncbi.nlm.nih.gov/24092765/)
- [Carbohydrate and resistance-training performance systematic review](https://pubmed.ncbi.nlm.nih.gov/35215506/)
- [Energy surplus trial in resistance-trained adults](https://sportsmedicine-open.springeropen.com/articles/10.1186/s40798-023-00651-y)
- [Accuracy of athlete resting metabolic rate equations](https://pubmed.ncbi.nlm.nih.gov/37632665/)
- [NATA fluid-replacement position statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC5634236/)
- [ISSN nutrient-timing position stand](https://link.springer.com/article/10.1186/s12970-017-0189-4)
- [IOC dietary supplement consensus](https://bjsm.bmj.com/content/52/7/439)
- [Australian Institute of Sport supplement framework](https://www.ausport.gov.au/ais/nutrition/supplements/about-the-ais-sports-supplement-framework)
- [USDA Dietary Reference Intake calculator](https://www.nal.usda.gov/human-nutrition-and-food-safety/dri-calculator)
- [2025–2030 Dietary Guidelines for Americans](https://odphp.health.gov/our-work/nutrition-physical-activity/dietary-guidelines/current-dietary-guidelines)
