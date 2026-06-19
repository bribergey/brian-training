drop policy if exists prod_legacy_anon_program_select_brian on public.program;
drop policy if exists prod_legacy_anon_monthly_program_select_brian on public.monthly_program;
drop policy if exists prod_legacy_anon_sessions_select_brian on public.sessions;
drop policy if exists prod_legacy_anon_sessions_insert_brian on public.sessions;
drop policy if exists prod_legacy_anon_sessions_update_brian on public.sessions;
drop policy if exists prod_legacy_anon_user_profile_select_brian on public.user_profile;
drop policy if exists prod_legacy_anon_user_profile_insert_brian on public.user_profile;
drop policy if exists prod_legacy_anon_user_profile_update_brian on public.user_profile;
drop policy if exists prod_legacy_anon_user_measurements_select_brian on public.user_measurements;
drop policy if exists prod_legacy_anon_user_measurements_insert_brian on public.user_measurements;
drop policy if exists prod_legacy_anon_user_measurements_update_brian on public.user_measurements;

revoke all on table
  public.app_users,
  public.app_users_staging,
  public.program,
  public.program_staging,
  public.monthly_program,
  public.monthly_program_staging,
  public.sessions,
  public.sessions_staging,
  public.user_profile,
  public.user_profile_staging,
  public.user_measurements,
  public.user_measurements_staging,
  public.program_full,
  public.program_staging_full,
  public.monthly_program_full,
  public.monthly_program_staging_full,
  public.exercises
from anon;

revoke all on table
  public.app_users,
  public.app_users_staging,
  public.program,
  public.program_staging,
  public.monthly_program,
  public.monthly_program_staging,
  public.sessions,
  public.sessions_staging,
  public.user_profile,
  public.user_profile_staging,
  public.user_measurements,
  public.user_measurements_staging,
  public.program_full,
  public.program_staging_full,
  public.monthly_program_full,
  public.monthly_program_staging_full,
  public.exercises
from authenticated;

grant select on table public.app_users to authenticated;
grant select on table public.app_users_staging to authenticated;

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
  public.program_full,
  public.program_staging_full,
  public.monthly_program_full,
  public.monthly_program_staging_full
to authenticated;

grant select on table public.exercises to anon, authenticated;
