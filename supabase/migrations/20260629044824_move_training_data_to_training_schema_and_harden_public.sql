-- Move Brian Training data out of the shared/exposed public table namespace.
--
-- Goals:
-- - put live training tables and views in the dedicated training schema
-- - keep public compatibility views so cached/static clients do not break
-- - remove old public scratch/storage surfaces that are not used by the app
-- - remove the temporary options_trader exposed-schema shim
-- - explicitly grant only the app's needed Data API surface

begin;

create schema if not exists training;

-- Remove unused public surfaces before recreating compatibility views.
drop table if exists public.app_docs;

drop policy if exists "Anon upload exercise photos" on storage.objects;
drop policy if exists "Public read exercise photos" on storage.objects;
-- The exercise-photos bucket itself must be emptied/deleted through the
-- Storage API or dashboard; direct deletes from storage.objects are blocked by
-- Supabase to avoid orphaned files. Dropping the policies removes public
-- listing/upload access immediately.

-- Supabase's current guidance recommends revoking broad default privileges for
-- future objects, but this project role cannot change those owner-specific
-- defaults through the CLI/MCP execution path. Existing objects are explicitly
-- revoked/granted below; default privilege cleanup remains a dashboard/owner
-- follow-up.


-- The full views depend on base tables, so drop before moving base tables.
drop view if exists public.program_full;
drop view if exists public.program_staging_full;
drop view if exists public.monthly_program_full;
drop view if exists public.monthly_program_staging_full;

do $$
declare
  table_name text;
  table_names text[] := array[
    'app_users',
    'app_users_staging',
    'exercises',
    'monthly_program',
    'monthly_program_staging',
    'program',
    'program_staging',
    'sessions',
    'sessions_staging',
    'user_measurements',
    'user_measurements_staging',
    'user_profile',
    'user_profile_staging'
  ];
begin
  foreach table_name in array table_names loop
    if exists (
      select 1
      from pg_class c
      join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relname = table_name
        and c.relkind in ('r', 'p')
    ) then
      execute format('alter table public.%I set schema training', table_name);
    end if;
  end loop;
end $$;

-- RLS helper functions stay in public for existing policy/function OIDs, but
-- they now read/write the training schema explicitly.
create or replace function public.current_app_user_id()
returns text
language sql
stable
set search_path to 'training', 'public', 'pg_temp'
as $$
  select au.user_id
  from training.app_users au
  where au.auth_user_id = auth.uid()
    and au.is_active = true
  limit 1
$$;

create or replace function public.current_staging_app_user_id()
returns text
language sql
stable
set search_path to 'training', 'public', 'pg_temp'
as $$
  select au.user_id
  from training.app_users_staging au
  where au.auth_user_id = auth.uid()
    and au.is_active = true
  limit 1
$$;

create or replace function public.update_exercise_months_used()
returns trigger
language plpgsql
set search_path to 'training', 'public', 'pg_temp'
as $$
begin
  if TG_OP = 'INSERT' then
    update training.exercises
    set months_used = array_append(months_used, NEW.month)
    where name = NEW.exercise
      and not (months_used @> array[NEW.month]);
  elsif TG_OP = 'DELETE' then
    update training.exercises e
    set months_used = (
      select coalesce(array_agg(distinct mp.month order by mp.month), '{}')
      from training.monthly_program mp
      where mp.exercise = e.name
    )
    where name = OLD.exercise;
  end if;
  return coalesce(NEW, OLD);
end;
$$;

-- Native training views for new clients.
create or replace view training.program_full
with (security_invoker = true)
as
select
  p.id,
  p.created_at,
  p.week,
  p.week_number,
  p.day,
  p.session_label,
  p.scheduled_date,
  p.session_key,
  p.order_index,
  p.exercise,
  e.badge,
  e.unit,
  e.rep_type,
  e.description,
  p.sets,
  p.reps,
  p.rest,
  p.weight,
  p.suggested_sets,
  p.coach_notes,
  p.superset_group,
  p.user_id
from training.program p
left join training.exercises e on e.name = p.exercise;

create or replace view training.program_staging_full
with (security_invoker = true)
as
select
  p.id,
  p.created_at,
  p.week,
  p.week_number,
  p.day,
  p.session_label,
  p.scheduled_date,
  p.session_key,
  p.order_index,
  p.exercise,
  e.badge,
  e.unit,
  e.rep_type,
  e.description,
  p.sets,
  p.reps,
  p.rest,
  p.weight,
  p.suggested_sets,
  p.coach_notes,
  p.superset_group,
  p.user_id
from training.program_staging p
left join training.exercises e on e.name = p.exercise;

create or replace view training.monthly_program_full
with (security_invoker = true)
as
select
  mp.id,
  mp.created_at,
  mp.month,
  mp.month_label,
  mp.status,
  mp.week_type,
  mp.day,
  mp.order_index,
  mp.exercise,
  e.badge,
  e.unit,
  e.rep_type,
  e.description,
  mp.superset_group,
  mp.weight,
  mp.sets,
  mp.session_label,
  mp.user_id
from training.monthly_program mp
left join training.exercises e on e.name = mp.exercise;

create or replace view training.monthly_program_staging_full
with (security_invoker = true)
as
select
  mp.id,
  mp.created_at,
  mp.month,
  mp.month_label,
  mp.status,
  mp.week_type,
  mp.day,
  mp.order_index,
  mp.exercise,
  e.badge,
  e.unit,
  e.rep_type,
  e.description,
  mp.superset_group,
  mp.weight,
  mp.sets,
  mp.session_label,
  mp.user_id
from training.monthly_program_staging mp
left join training.exercises e on e.name = mp.exercise;

-- Public compatibility views for cached clients and older coach instructions.
create or replace view public.app_users
with (security_invoker = true)
as select * from training.app_users;

create or replace view public.app_users_staging
with (security_invoker = true)
as select * from training.app_users_staging;

create or replace view public.exercises
with (security_invoker = true)
as select * from training.exercises;

create or replace view public.monthly_program
with (security_invoker = true)
as select * from training.monthly_program;

create or replace view public.monthly_program_staging
with (security_invoker = true)
as select * from training.monthly_program_staging;

create or replace view public.program
with (security_invoker = true)
as select * from training.program;

create or replace view public.program_staging
with (security_invoker = true)
as select * from training.program_staging;

create or replace view public.sessions
with (security_invoker = true)
as select * from training.sessions;

create or replace view public.sessions_staging
with (security_invoker = true)
as select * from training.sessions_staging;

create or replace view public.user_measurements
with (security_invoker = true)
as select * from training.user_measurements;

create or replace view public.user_measurements_staging
with (security_invoker = true)
as select * from training.user_measurements_staging;

create or replace view public.user_profile
with (security_invoker = true)
as select * from training.user_profile;

create or replace view public.user_profile_staging
with (security_invoker = true)
as select * from training.user_profile_staging;

create or replace view public.program_full
with (security_invoker = true)
as select * from training.program_full;

create or replace view public.program_staging_full
with (security_invoker = true)
as select * from training.program_staging_full;

create or replace view public.monthly_program_full
with (security_invoker = true)
as select * from training.monthly_program_full;

create or replace view public.monthly_program_staging_full
with (security_invoker = true)
as select * from training.monthly_program_staging_full;

-- Explicit grants for the training schema and compatibility views.
revoke create on schema public from public, anon, authenticated;
revoke all on schema training from public, anon, authenticated;
grant usage on schema training to anon, authenticated;

revoke all on all tables in schema training from anon, authenticated;
revoke all on all tables in schema public from anon, authenticated;

grant select on table training.app_users to authenticated;
grant select on table training.app_users_staging to authenticated;
grant select on table public.app_users to authenticated;
grant select on table public.app_users_staging to authenticated;

grant select on table training.exercises to anon, authenticated;
grant select on table public.exercises to anon, authenticated;

grant select, insert, update, delete on table
  training.program,
  training.program_staging,
  training.monthly_program,
  training.monthly_program_staging,
  training.sessions,
  training.sessions_staging,
  training.user_profile,
  training.user_profile_staging,
  training.user_measurements,
  training.user_measurements_staging
to authenticated;

grant select, insert, update, delete on table
  public.program,
  public.program_staging,
  public.monthly_program,
  public.monthly_program_staging,
  public.sessions,
  public.sessions_staging,
  public.user_profile,
  public.user_profile_staging,
  public.user_measurements,
  public.user_measurements_staging
to authenticated;

grant select on table
  training.program_full,
  training.program_staging_full,
  training.monthly_program_full,
  training.monthly_program_staging_full,
  public.program_full,
  public.program_staging_full,
  public.monthly_program_full,
  public.monthly_program_staging_full
to authenticated;

-- Expose only the schemas needed by the app. This removes options_trader from
-- PostgREST/Data API exposure and enables direct training-schema requests.
alter role authenticator set pgrst.db_schemas = 'public, training';
notify pgrst, 'reload config';
notify pgrst, 'reload schema';

drop schema if exists options_trader;

commit;
