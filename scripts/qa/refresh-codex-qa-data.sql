-- Refresh the isolated Codex QA account from Brian's production data.
--
-- Run this entire file as one request through the Supabase SQL connector.
-- It is intentionally DML-only and transactional: Brian's rows are read as
-- source data, while only rows owned by `codex_qa` are deleted or inserted.
--
-- Production data is used as the source for both target environments so
-- staging exercises the app against the same realistic shapes as production.
-- Food-photo references and reusable-food IDs are removed from copied Daily
-- Logs. This prevents QA actions from ever targeting Brian's storage objects
-- or food-memory rows. The reusable foods themselves are copied with new IDs.

begin;

do $$
declare
  production_mapping_count integer;
  staging_mapping_count integer;
  brian_mapping_count integer;
begin
  select count(*) into production_mapping_count
  from training.app_users
  where user_id = 'codex_qa'
    and email = 'dev@lostplate.com'
    and is_active;

  select count(*) into staging_mapping_count
  from training.app_users_staging
  where user_id = 'codex_qa'
    and email = 'dev@lostplate.com'
    and is_active;

  select count(*) into brian_mapping_count
  from training.app_users
  where user_id = 'brian'
    and is_active;

  if production_mapping_count <> 1 then
    raise exception 'Expected one active codex_qa production mapping; found %',
      production_mapping_count;
  end if;

  if staging_mapping_count <> 1 then
    raise exception 'Expected one active codex_qa staging mapping; found %',
      staging_mapping_count;
  end if;

  if brian_mapping_count <> 1 then
    raise exception 'Expected one active Brian production mapping; found %',
      brian_mapping_count;
  end if;
end
$$;

create temporary table qa_brian_source_counts (
  table_name text primary key,
  row_count bigint not null
) on commit drop;

insert into qa_brian_source_counts (table_name, row_count)
values
  ('sessions', (select count(*) from training.sessions where user_id = 'brian')),
  ('program', (select count(*) from training.program where user_id = 'brian')),
  ('monthly_program', (select count(*) from training.monthly_program where user_id = 'brian')),
  ('user_profile', (select count(*) from training.user_profile where user_id = 'brian')),
  ('user_measurements', (select count(*) from training.user_measurements where user_id = 'brian')),
  ('daily_logs', (select count(*) from training.daily_logs where user_id = 'brian')),
  ('nutrition_day_targets', (select count(*) from training.nutrition_day_targets where user_id = 'brian')),
  ('nutrition_food_memory', (select count(*) from training.nutrition_food_memory where user_id = 'brian')),
  ('nutrition_ai_runs', (select count(*) from training.nutrition_ai_runs where user_id = 'brian'));

-- Delete only the dedicated QA account's existing fixture rows.
delete from training.nutrition_ai_runs_staging where user_id = 'codex_qa';
delete from training.nutrition_food_memory_staging where user_id = 'codex_qa';
delete from training.nutrition_day_targets_staging where user_id = 'codex_qa';
delete from training.daily_logs_staging where user_id = 'codex_qa';
delete from training.user_measurements_staging where user_id = 'codex_qa';
delete from training.user_profile_staging where user_id = 'codex_qa';
delete from training.sessions_staging where user_id = 'codex_qa';
delete from training.monthly_program_staging where user_id = 'codex_qa';
delete from training.program_staging where user_id = 'codex_qa';

delete from training.nutrition_ai_runs where user_id = 'codex_qa';
delete from training.nutrition_food_memory where user_id = 'codex_qa';
delete from training.nutrition_day_targets where user_id = 'codex_qa';
delete from training.daily_logs where user_id = 'codex_qa';
delete from training.user_measurements where user_id = 'codex_qa';
delete from training.user_profile where user_id = 'codex_qa';
delete from training.sessions where user_id = 'codex_qa';
delete from training.monthly_program where user_id = 'codex_qa';
delete from training.program where user_id = 'codex_qa';

insert into training.sessions (
  id, created_at, date, day, notes, exercises, logged_at,
  program_session_key, skipped, workout_time, user_id
)
select
  gen_random_uuid(), created_at, date, day, notes, exercises, logged_at,
  program_session_key, skipped, workout_time, 'codex_qa'
from training.sessions
where user_id = 'brian';

insert into training.sessions_staging (
  id, created_at, date, day, notes, exercises, logged_at,
  program_session_key, skipped, workout_time, user_id
)
select
  gen_random_uuid(), created_at, date, day, notes, exercises, logged_at,
  program_session_key, skipped, workout_time, 'codex_qa'
from training.sessions
where user_id = 'brian';

insert into training.program (
  id, created_at, week, day, exercise, sets, reps, weight, notes, rest,
  order_index, scheduled_date, week_number, session_label, session_key,
  suggested_sets, coach_notes, superset_group, user_id
)
select
  gen_random_uuid(), created_at, week, day, exercise, sets, reps, weight,
  notes, rest, order_index, scheduled_date, week_number, session_label,
  session_key, suggested_sets, coach_notes, superset_group, 'codex_qa'
from training.program
where user_id = 'brian';

insert into training.program_staging (
  id, created_at, week, day, exercise, sets, reps, weight, notes, rest,
  order_index, scheduled_date, week_number, session_label, session_key,
  suggested_sets, coach_notes, superset_group, user_id
)
select
  gen_random_uuid(), created_at, week, day, exercise, sets, reps, weight,
  notes, rest, order_index, scheduled_date, week_number, session_label,
  session_key, suggested_sets, coach_notes, superset_group, 'codex_qa'
from training.program
where user_id = 'brian';

insert into training.monthly_program (
  id, created_at, month, month_label, status, day, order_index, exercise,
  sets, weight, internal_notes, week_type, superset_group, session_label,
  user_id
)
select
  gen_random_uuid(), created_at, month, month_label, status, day,
  order_index, exercise, sets, weight, internal_notes, week_type,
  superset_group, session_label, 'codex_qa'
from training.monthly_program
where user_id = 'brian';

insert into training.monthly_program_staging (
  id, created_at, month, month_label, status, day, order_index, exercise,
  sets, weight, internal_notes, week_type, superset_group, session_label,
  user_id
)
select
  gen_random_uuid(), created_at, month, month_label, status, day,
  order_index, exercise, sets, weight, internal_notes, week_type,
  superset_group, session_label, 'codex_qa'
from training.monthly_program
where user_id = 'brian';

insert into training.user_profile (
  id, name, dob, height_cm, training_days_per_week, preferred_days,
  training_window_start, training_window_end, goals, injuries,
  experience_level, equipment, created_at, updated_at, nutrition_notes,
  diet_type, fasting_window, gender, nutrition_goal, activity_level,
  macro_targets, macro_targets_history, user_id, carbohydrate_preference,
  added_sugar_preference
)
select
  gen_random_uuid(), 'Codex QA', dob, height_cm, training_days_per_week,
  preferred_days, training_window_start, training_window_end, goals,
  injuries, experience_level, equipment, created_at, updated_at,
  nutrition_notes, diet_type, fasting_window, gender, nutrition_goal,
  activity_level, macro_targets, macro_targets_history, 'codex_qa',
  carbohydrate_preference, added_sugar_preference
from training.user_profile
where user_id = 'brian';

insert into training.user_profile_staging (
  id, name, dob, height_cm, training_days_per_week, preferred_days,
  training_window_start, training_window_end, goals, injuries,
  experience_level, equipment, created_at, updated_at, nutrition_notes,
  diet_type, fasting_window, gender, nutrition_goal, activity_level,
  macro_targets, macro_targets_history, user_id, carbohydrate_preference,
  added_sugar_preference
)
select
  gen_random_uuid(), 'Codex QA', dob, height_cm, training_days_per_week,
  preferred_days, training_window_start, training_window_end, goals,
  injuries, experience_level, equipment, created_at, updated_at,
  nutrition_notes, diet_type, fasting_window, gender, nutrition_goal,
  activity_level, macro_targets, macro_targets_history, 'codex_qa',
  carbohydrate_preference, added_sugar_preference
from training.user_profile
where user_id = 'brian';

insert into training.user_measurements (
  id, logged_at, weight_kg, body_fat_pct, notes, created_at, user_id
)
select
  gen_random_uuid(), logged_at, weight_kg, body_fat_pct, notes,
  created_at, 'codex_qa'
from training.user_measurements
where user_id = 'brian';

insert into training.user_measurements_staging (
  id, logged_at, weight_kg, body_fat_pct, notes, created_at, user_id
)
select
  gen_random_uuid(), logged_at, weight_kg, body_fat_pct, notes,
  created_at, 'codex_qa'
from training.user_measurements
where user_id = 'brian';

create temporary table qa_daily_logs_source on commit drop as
select
  created_at, log_date, sleep_score, sleep_duration_minutes, energy,
  stress, mood, soreness, work_hours, stool_type, no_bowel_movement,
  had_alcohol, had_caffeine, took_magnesium, traveled, illness,
  first_calories_at, last_calories_at,
  coalesce((
    select jsonb_agg(
      (entry - 'memory_id' - 'memory_source_description')
        || jsonb_build_object('photos', '[]'::jsonb)
      order by ordinal
    )
    from jsonb_array_elements(source.food_entries)
      with ordinality as food(entry, ordinal)
  ), '[]'::jsonb) as food_entries,
  notes, coach_analysis, updated_at, took_electrolytes,
  had_protein_powder
from training.daily_logs source
where user_id = 'brian';

insert into training.daily_logs (
  id, user_id, log_date, sleep_score, sleep_duration_minutes, energy,
  stress, mood, soreness, work_hours, stool_type, no_bowel_movement,
  had_alcohol, had_caffeine, took_magnesium, traveled, illness,
  first_calories_at, last_calories_at, food_entries, notes, coach_analysis,
  created_at, updated_at, took_electrolytes, had_protein_powder
)
select
  gen_random_uuid(), 'codex_qa', log_date, sleep_score,
  sleep_duration_minutes, energy, stress, mood, soreness, work_hours,
  stool_type, no_bowel_movement, had_alcohol, had_caffeine,
  took_magnesium, traveled, illness, first_calories_at, last_calories_at,
  food_entries, notes, coach_analysis, created_at, updated_at,
  took_electrolytes, had_protein_powder
from qa_daily_logs_source;

insert into training.daily_logs_staging (
  id, user_id, log_date, sleep_score, sleep_duration_minutes, energy,
  stress, mood, soreness, work_hours, stool_type, no_bowel_movement,
  had_alcohol, had_caffeine, took_magnesium, traveled, illness,
  first_calories_at, last_calories_at, food_entries, notes, coach_analysis,
  created_at, updated_at, took_electrolytes, had_protein_powder
)
select
  gen_random_uuid(), 'codex_qa', log_date, sleep_score,
  sleep_duration_minutes, energy, stress, mood, soreness, work_hours,
  stool_type, no_bowel_movement, had_alcohol, had_caffeine,
  took_magnesium, traveled, illness, first_calories_at, last_calories_at,
  food_entries, notes, coach_analysis, created_at, updated_at,
  took_electrolytes, had_protein_powder
from qa_daily_logs_source;

insert into training.nutrition_day_targets (
  id, user_id, target_date, day_type, status, engine_version, input_hash,
  input_snapshot, reason_codes, energy_kcal, protein_g, carbs_g, fat_g,
  fiber_g, created_at, updated_at
)
select
  gen_random_uuid(), 'codex_qa', target_date, day_type, status,
  engine_version, input_hash, input_snapshot, reason_codes, energy_kcal,
  protein_g, carbs_g, fat_g, fiber_g, created_at, updated_at
from training.nutrition_day_targets
where user_id = 'brian';

insert into training.nutrition_day_targets_staging (
  id, user_id, target_date, day_type, status, engine_version, input_hash,
  input_snapshot, reason_codes, energy_kcal, protein_g, carbs_g, fat_g,
  fiber_g, created_at, updated_at
)
select
  gen_random_uuid(), 'codex_qa', target_date, day_type, status,
  engine_version, input_hash, input_snapshot, reason_codes, energy_kcal,
  protein_g, carbs_g, fat_g, fiber_g, created_at, updated_at
from training.nutrition_day_targets
where user_id = 'brian';

insert into training.nutrition_food_memory (
  id, user_id, canonical_key, canonical_name, aliases,
  serving_description, latest_raw_description, energy_kcal, protein_g,
  carbs_g, fat_g, fiber_g, assumptions, confidence, source, provider,
  model, prompt_version, times_used, user_confirmed, last_used_at,
  created_at, updated_at, description_patterns, portion_notes,
  correction_count, display_name, needs_reestimate
)
select
  gen_random_uuid(), 'codex_qa', canonical_key, canonical_name, aliases,
  serving_description, latest_raw_description, energy_kcal, protein_g,
  carbs_g, fat_g, fiber_g, assumptions, confidence, source, provider,
  model, prompt_version, times_used, user_confirmed, last_used_at,
  created_at, updated_at, description_patterns, portion_notes,
  correction_count, display_name, needs_reestimate
from training.nutrition_food_memory
where user_id = 'brian';

insert into training.nutrition_food_memory_staging (
  id, user_id, canonical_key, canonical_name, aliases,
  serving_description, latest_raw_description, energy_kcal, protein_g,
  carbs_g, fat_g, fiber_g, assumptions, confidence, source, provider,
  model, prompt_version, times_used, user_confirmed, last_used_at,
  created_at, updated_at, description_patterns, portion_notes,
  correction_count, display_name, needs_reestimate
)
select
  gen_random_uuid(), 'codex_qa', canonical_key, canonical_name, aliases,
  serving_description, latest_raw_description, energy_kcal, protein_g,
  carbs_g, fat_g, fiber_g, assumptions, confidence, source, provider,
  model, prompt_version, times_used, user_confirmed, last_used_at,
  created_at, updated_at, description_patterns, portion_notes,
  correction_count, display_name, needs_reestimate
from training.nutrition_food_memory
where user_id = 'brian';

insert into training.nutrition_ai_runs (
  id, user_id, log_date, purpose, entry_ids, provider, model,
  prompt_version, status, input_hash, output_hash, latency_ms, error_code,
  created_at, prompt_tokens, completion_tokens, total_tokens, cost_usd,
  image_count, generation_id
)
select
  gen_random_uuid(), 'codex_qa', log_date, purpose, entry_ids, provider,
  model, prompt_version, status, input_hash, output_hash, latency_ms,
  error_code, created_at, prompt_tokens, completion_tokens, total_tokens,
  cost_usd, image_count, generation_id
from training.nutrition_ai_runs
where user_id = 'brian';

insert into training.nutrition_ai_runs_staging (
  id, user_id, log_date, purpose, entry_ids, provider, model,
  prompt_version, status, input_hash, output_hash, latency_ms, error_code,
  created_at, prompt_tokens, completion_tokens, total_tokens, cost_usd,
  image_count, generation_id
)
select
  gen_random_uuid(), 'codex_qa', log_date, purpose, entry_ids, provider,
  model, prompt_version, status, input_hash, output_hash, latency_ms,
  error_code, created_at, prompt_tokens, completion_tokens, total_tokens,
  cost_usd, image_count, generation_id
from training.nutrition_ai_runs
where user_id = 'brian';

-- Abort the transaction if any Brian source row count changed unexpectedly.
do $$
declare
  changed_table text;
begin
  select snapshot.table_name into changed_table
  from qa_brian_source_counts snapshot
  join (
    values
      ('sessions', (select count(*) from training.sessions where user_id = 'brian')),
      ('program', (select count(*) from training.program where user_id = 'brian')),
      ('monthly_program', (select count(*) from training.monthly_program where user_id = 'brian')),
      ('user_profile', (select count(*) from training.user_profile where user_id = 'brian')),
      ('user_measurements', (select count(*) from training.user_measurements where user_id = 'brian')),
      ('daily_logs', (select count(*) from training.daily_logs where user_id = 'brian')),
      ('nutrition_day_targets', (select count(*) from training.nutrition_day_targets where user_id = 'brian')),
      ('nutrition_food_memory', (select count(*) from training.nutrition_food_memory where user_id = 'brian')),
      ('nutrition_ai_runs', (select count(*) from training.nutrition_ai_runs where user_id = 'brian'))
  ) as current_counts(table_name, row_count)
    on current_counts.table_name = snapshot.table_name
  where current_counts.row_count <> snapshot.row_count
  limit 1;

  if changed_table is not null then
    raise exception 'Brian source count changed during QA refresh: %',
      changed_table;
  end if;
end
$$;

commit;

-- The result is a concise verification report. Production and staging QA
-- counts should equal Brian's production counts for every listed data type.
with expected as (
  select 'sessions' data_type, count(*) expected_count
  from training.sessions where user_id = 'brian'
  union all select 'program', count(*) from training.program where user_id = 'brian'
  union all select 'monthly_program', count(*) from training.monthly_program where user_id = 'brian'
  union all select 'user_profile', count(*) from training.user_profile where user_id = 'brian'
  union all select 'user_measurements', count(*) from training.user_measurements where user_id = 'brian'
  union all select 'daily_logs', count(*) from training.daily_logs where user_id = 'brian'
  union all select 'nutrition_day_targets', count(*) from training.nutrition_day_targets where user_id = 'brian'
  union all select 'nutrition_food_memory', count(*) from training.nutrition_food_memory where user_id = 'brian'
  union all select 'nutrition_ai_runs', count(*) from training.nutrition_ai_runs where user_id = 'brian'
),
actual as (
  select 'production' environment, 'sessions' data_type, count(*) actual_count
  from training.sessions where user_id = 'codex_qa'
  union all select 'production', 'program', count(*) from training.program where user_id = 'codex_qa'
  union all select 'production', 'monthly_program', count(*) from training.monthly_program where user_id = 'codex_qa'
  union all select 'production', 'user_profile', count(*) from training.user_profile where user_id = 'codex_qa'
  union all select 'production', 'user_measurements', count(*) from training.user_measurements where user_id = 'codex_qa'
  union all select 'production', 'daily_logs', count(*) from training.daily_logs where user_id = 'codex_qa'
  union all select 'production', 'nutrition_day_targets', count(*) from training.nutrition_day_targets where user_id = 'codex_qa'
  union all select 'production', 'nutrition_food_memory', count(*) from training.nutrition_food_memory where user_id = 'codex_qa'
  union all select 'production', 'nutrition_ai_runs', count(*) from training.nutrition_ai_runs where user_id = 'codex_qa'
  union all select 'staging', 'sessions', count(*) from training.sessions_staging where user_id = 'codex_qa'
  union all select 'staging', 'program', count(*) from training.program_staging where user_id = 'codex_qa'
  union all select 'staging', 'monthly_program', count(*) from training.monthly_program_staging where user_id = 'codex_qa'
  union all select 'staging', 'user_profile', count(*) from training.user_profile_staging where user_id = 'codex_qa'
  union all select 'staging', 'user_measurements', count(*) from training.user_measurements_staging where user_id = 'codex_qa'
  union all select 'staging', 'daily_logs', count(*) from training.daily_logs_staging where user_id = 'codex_qa'
  union all select 'staging', 'nutrition_day_targets', count(*) from training.nutrition_day_targets_staging where user_id = 'codex_qa'
  union all select 'staging', 'nutrition_food_memory', count(*) from training.nutrition_food_memory_staging where user_id = 'codex_qa'
  union all select 'staging', 'nutrition_ai_runs', count(*) from training.nutrition_ai_runs_staging where user_id = 'codex_qa'
)
select
  actual.environment,
  actual.data_type,
  expected.expected_count,
  actual.actual_count,
  actual.actual_count = expected.expected_count as matches
from actual
join expected using (data_type)
order by actual.environment, actual.data_type;
