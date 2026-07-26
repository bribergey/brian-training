-- Versioned nutrition targets, AI audit metadata, and user-owned recurring
-- food memory. Production and staging stay physically separate.

begin;

alter table training.user_profile
  add column if not exists carbohydrate_preference text
    check (carbohydrate_preference in ('Balanced', 'Lower carbohydrate'));
alter table training.user_profile
  add column if not exists added_sugar_preference text
    check (added_sugar_preference in ('No preference', 'No / low added sugar'));
alter table training.user_profile_staging
  add column if not exists carbohydrate_preference text
    check (carbohydrate_preference in ('Balanced', 'Lower carbohydrate'));
alter table training.user_profile_staging
  add column if not exists added_sugar_preference text
    check (added_sugar_preference in ('No preference', 'No / low added sugar'));

-- This staging-only profile update records the preference Brian explicitly
-- supplied for this test branch. Production data is not changed.
update training.user_profile_staging
set carbohydrate_preference = 'Lower carbohydrate',
    added_sugar_preference = 'No / low added sugar'
where user_id = 'brian';

create or replace view public.user_profile as
select
  id, name, dob, height_cm, training_days_per_week, preferred_days,
  training_window_start, training_window_end, goals, injuries,
  experience_level, equipment, created_at, updated_at, nutrition_notes,
  diet_type, fasting_window, gender, nutrition_goal, activity_level,
  macro_targets, macro_targets_history, user_id, carbohydrate_preference,
  added_sugar_preference
from training.user_profile;

create or replace view public.user_profile_staging as
select
  id, name, dob, height_cm, training_days_per_week, preferred_days,
  training_window_start, training_window_end, goals, injuries,
  experience_level, equipment, created_at, updated_at, nutrition_notes,
  diet_type, fasting_window, gender, nutrition_goal, activity_level,
  macro_targets, macro_targets_history, user_id, carbohydrate_preference,
  added_sugar_preference
from training.user_profile_staging;

alter view public.user_profile set (security_invoker = true);
alter view public.user_profile_staging set (security_invoker = true);

create table training.nutrition_day_targets (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  target_date date not null,
  day_type text not null check (day_type in ('training', 'rest')),
  status text not null default 'provisional'
    check (status in ('provisional', 'calibrated', 'manual')),
  engine_version text not null,
  input_hash text not null,
  input_snapshot jsonb not null default '{}'::jsonb
    check (jsonb_typeof(input_snapshot) = 'object'),
  reason_codes text[] not null default '{}'::text[],
  energy_kcal integer not null check (energy_kcal between 800 and 6000),
  protein_g numeric(6,1) not null check (protein_g between 0 and 500),
  carbs_g numeric(6,1) not null check (carbs_g between 0 and 1000),
  fat_g numeric(6,1) not null check (fat_g between 0 and 500),
  fiber_g numeric(6,1) check (fiber_g between 0 and 150),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint nutrition_day_targets_user_date_key unique (user_id, target_date),
  constraint nutrition_day_targets_energy_reconciles check (
    abs(energy_kcal - ((protein_g * 4) + (carbs_g * 4) + (fat_g * 9))) <= 25
  )
);

create table training.nutrition_day_targets_staging (
  like training.nutrition_day_targets including defaults including constraints including indexes
);

create table training.nutrition_food_memory (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  canonical_key text not null,
  canonical_name text not null,
  aliases text[] not null default '{}'::text[],
  serving_description text,
  latest_raw_description text,
  energy_kcal numeric(8,1) not null check (energy_kcal between 0 and 10000),
  protein_g numeric(7,1) not null check (protein_g between 0 and 1000),
  carbs_g numeric(7,1) not null check (carbs_g between 0 and 2000),
  fat_g numeric(7,1) not null check (fat_g between 0 and 1000),
  fiber_g numeric(7,1) check (fiber_g between 0 and 500),
  assumptions jsonb not null default '[]'::jsonb
    check (jsonb_typeof(assumptions) = 'array'),
  confidence numeric(4,3) not null default 0.5
    check (confidence between 0 and 1),
  source text not null default 'ai_estimate'
    check (source in ('ai_estimate', 'user_corrected', 'product_label', 'database_match')),
  provider text,
  model text,
  prompt_version text,
  times_used integer not null default 1 check (times_used > 0),
  user_confirmed boolean not null default false,
  last_used_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint nutrition_food_memory_user_key unique (user_id, canonical_key)
);

create table training.nutrition_food_memory_staging (
  like training.nutrition_food_memory including defaults including constraints including indexes
);

create table training.nutrition_ai_runs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  log_date date not null,
  purpose text not null default 'food_estimation',
  entry_ids text[] not null default '{}'::text[],
  provider text,
  model text,
  prompt_version text not null,
  status text not null check (status in ('succeeded', 'failed')),
  input_hash text,
  output_hash text,
  latency_ms integer check (latency_ms is null or latency_ms >= 0),
  error_code text,
  created_at timestamptz not null default timezone('utc', now())
);

create table training.nutrition_ai_runs_staging (
  like training.nutrition_ai_runs including defaults including constraints including indexes
);

alter table training.nutrition_day_targets enable row level security;
alter table training.nutrition_day_targets_staging enable row level security;
alter table training.nutrition_food_memory enable row level security;
alter table training.nutrition_food_memory_staging enable row level security;
alter table training.nutrition_ai_runs enable row level security;
alter table training.nutrition_ai_runs_staging enable row level security;

create policy nutrition_day_targets_own on training.nutrition_day_targets
for all to authenticated
using (user_id = (select public.current_app_user_id()))
with check (user_id = (select public.current_app_user_id()));

create policy nutrition_day_targets_staging_own on training.nutrition_day_targets_staging
for all to authenticated
using (user_id = (select public.current_staging_app_user_id()))
with check (user_id = (select public.current_staging_app_user_id()));

create policy nutrition_food_memory_own on training.nutrition_food_memory
for all to authenticated
using (user_id = (select public.current_app_user_id()))
with check (user_id = (select public.current_app_user_id()));

create policy nutrition_food_memory_staging_own on training.nutrition_food_memory_staging
for all to authenticated
using (user_id = (select public.current_staging_app_user_id()))
with check (user_id = (select public.current_staging_app_user_id()));

create policy nutrition_ai_runs_select_own on training.nutrition_ai_runs
for select to authenticated
using (user_id = (select public.current_app_user_id()));

create policy nutrition_ai_runs_staging_select_own on training.nutrition_ai_runs_staging
for select to authenticated
using (user_id = (select public.current_staging_app_user_id()));

create trigger touch_updated_at_nutrition_day_targets
before update on training.nutrition_day_targets
for each row execute function public.phase3_touch_updated_at();

create trigger touch_updated_at_nutrition_day_targets_staging
before update on training.nutrition_day_targets_staging
for each row execute function public.phase3_touch_updated_at();

create trigger touch_updated_at_nutrition_food_memory
before update on training.nutrition_food_memory
for each row execute function public.phase3_touch_updated_at();

create trigger touch_updated_at_nutrition_food_memory_staging
before update on training.nutrition_food_memory_staging
for each row execute function public.phase3_touch_updated_at();

revoke all on table training.nutrition_day_targets from anon;
revoke all on table training.nutrition_day_targets_staging from anon;
revoke all on table training.nutrition_food_memory from anon;
revoke all on table training.nutrition_food_memory_staging from anon;
revoke all on table training.nutrition_ai_runs from anon;
revoke all on table training.nutrition_ai_runs_staging from anon;

grant select, insert, update, delete on table training.nutrition_day_targets to authenticated;
grant select, insert, update, delete on table training.nutrition_day_targets_staging to authenticated;
grant select, insert, update, delete on table training.nutrition_food_memory to authenticated;
grant select, insert, update, delete on table training.nutrition_food_memory_staging to authenticated;
grant select on table training.nutrition_ai_runs to authenticated;
grant select on table training.nutrition_ai_runs_staging to authenticated;

grant all privileges on table training.nutrition_day_targets to service_role;
grant all privileges on table training.nutrition_day_targets_staging to service_role;
grant all privileges on table training.nutrition_food_memory to service_role;
grant all privileges on table training.nutrition_food_memory_staging to service_role;
grant all privileges on table training.nutrition_ai_runs to service_role;
grant all privileges on table training.nutrition_ai_runs_staging to service_role;

comment on table training.nutrition_day_targets is
  'Production versioned daily calorie and macro target snapshots.';
comment on table training.nutrition_day_targets_staging is
  'Staging-only versioned daily calorie and macro target snapshots.';
comment on table training.nutrition_food_memory is
  'Production user-owned recurring foods and meals with reusable nutrient estimates.';
comment on table training.nutrition_food_memory_staging is
  'Staging-only user-owned recurring foods and meals with reusable nutrient estimates.';
comment on table training.nutrition_ai_runs is
  'Production metadata-only audit log for nutrition model calls; raw prompts and responses are not stored.';
comment on table training.nutrition_ai_runs_staging is
  'Staging-only metadata audit log for nutrition model calls; raw prompts and responses are not stored.';

commit;
