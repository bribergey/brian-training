begin;

-- Keep staging locked to authenticated access while Phase 3 auth is proven.
-- Also narrow the shared exercise catalog to anon read-only access.

drop policy if exists prod_legacy_anon_program_select_brian on public.program_staging;
drop policy if exists prod_legacy_anon_monthly_program_select_brian on public.monthly_program_staging;
drop policy if exists prod_legacy_anon_sessions_select_brian on public.sessions_staging;
drop policy if exists prod_legacy_anon_sessions_insert_brian on public.sessions_staging;
drop policy if exists prod_legacy_anon_sessions_update_brian on public.sessions_staging;
drop policy if exists prod_legacy_anon_user_profile_select_brian on public.user_profile_staging;
drop policy if exists prod_legacy_anon_user_profile_insert_brian on public.user_profile_staging;
drop policy if exists prod_legacy_anon_user_profile_update_brian on public.user_profile_staging;
drop policy if exists prod_legacy_anon_user_measurements_select_brian on public.user_measurements_staging;
drop policy if exists prod_legacy_anon_user_measurements_insert_brian on public.user_measurements_staging;
drop policy if exists prod_legacy_anon_user_measurements_update_brian on public.user_measurements_staging;

drop policy if exists anon_read_exercises on public.exercises;
drop policy if exists anon_write_exercises on public.exercises;
drop policy if exists anon_select_exercises on public.exercises;
create policy anon_select_exercises
on public.exercises
for select
to anon
using (true);

commit;
