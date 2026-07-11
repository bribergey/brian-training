-- Add separate production and staging Daily Log storage.
--
-- This migration intentionally creates no seed/copy operation. Staging Daily
-- Log rows remain in daily_logs_staging and never move into daily_logs.

begin;

create table training.daily_logs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  log_date date not null default current_date,
  sleep_score smallint,
  sleep_duration_minutes smallint,
  energy smallint,
  stress smallint,
  mood smallint,
  soreness smallint,
  work_hours numeric(4,1),
  stool_type smallint,
  no_bowel_movement boolean not null default false,
  had_alcohol boolean not null default false,
  had_caffeine boolean not null default false,
  took_magnesium boolean not null default false,
  traveled boolean not null default false,
  illness boolean not null default false,
  first_calories_at time without time zone,
  last_calories_at time without time zone,
  food_entries jsonb not null default '[]'::jsonb,
  notes text,
  coach_analysis jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint daily_logs_user_date_key unique (user_id, log_date),
  constraint daily_logs_sleep_score_check check (sleep_score between 0 and 100),
  constraint daily_logs_sleep_duration_check check (sleep_duration_minutes between 0 and 1440),
  constraint daily_logs_energy_check check (energy between 1 and 5),
  constraint daily_logs_stress_check check (stress between 1 and 5),
  constraint daily_logs_mood_check check (mood between 1 and 5),
  constraint daily_logs_soreness_check check (soreness between 1 and 5),
  constraint daily_logs_work_hours_check check (work_hours between 0 and 24),
  constraint daily_logs_stool_type_check check (stool_type between 1 and 7),
  constraint daily_logs_stool_choice_check check (not (no_bowel_movement and stool_type is not null)),
  constraint daily_logs_food_entries_array_check check (jsonb_typeof(food_entries) = 'array'),
  constraint daily_logs_coach_analysis_object_check check (jsonb_typeof(coach_analysis) = 'object')
);

create table training.daily_logs_staging (
  like training.daily_logs including defaults including constraints including indexes
);

alter table training.daily_logs enable row level security;
alter table training.daily_logs_staging enable row level security;

create policy daily_logs_select_own
on training.daily_logs
for select
to authenticated
using (user_id = (select public.current_app_user_id()));

create policy daily_logs_insert_own
on training.daily_logs
for insert
to authenticated
with check (user_id = (select public.current_app_user_id()));

create policy daily_logs_update_own
on training.daily_logs
for update
to authenticated
using (user_id = (select public.current_app_user_id()))
with check (user_id = (select public.current_app_user_id()));

create policy daily_logs_delete_own
on training.daily_logs
for delete
to authenticated
using (user_id = (select public.current_app_user_id()));

create policy daily_logs_staging_select_own
on training.daily_logs_staging
for select
to authenticated
using (user_id = (select public.current_staging_app_user_id()));

create policy daily_logs_staging_insert_own
on training.daily_logs_staging
for insert
to authenticated
with check (user_id = (select public.current_staging_app_user_id()));

create policy daily_logs_staging_update_own
on training.daily_logs_staging
for update
to authenticated
using (user_id = (select public.current_staging_app_user_id()))
with check (user_id = (select public.current_staging_app_user_id()));

create policy daily_logs_staging_delete_own
on training.daily_logs_staging
for delete
to authenticated
using (user_id = (select public.current_staging_app_user_id()));

create trigger touch_updated_at_daily_logs
before update on training.daily_logs
for each row
execute function public.phase3_touch_updated_at();

create trigger touch_updated_at_daily_logs_staging
before update on training.daily_logs_staging
for each row
execute function public.phase3_touch_updated_at();

revoke all on table training.daily_logs from anon;
revoke all on table training.daily_logs_staging from anon;

grant select, insert, update, delete on table training.daily_logs to authenticated;
grant select, insert, update, delete on table training.daily_logs_staging to authenticated;
grant all privileges on table training.daily_logs to service_role;
grant all privileges on table training.daily_logs_staging to service_role;

comment on table training.daily_logs is
  'Production user-owned Daily Log records. One row per app user and local calendar date.';
comment on table training.daily_logs_staging is
  'Staging-only user-owned Daily Log records. Rows are never promoted or copied to production.';
comment on column training.daily_logs.food_entries is
  'User-entered JSON array of {id, time, description} food or drink entries.';
comment on column training.daily_logs.coach_analysis is
  'Coach-derived structured analysis kept separate from user-entered fields.';

commit;
