begin;

-- Temporary production-only bridge for the legacy public app.
--
-- Phase 3 locked user-owned tables behind authenticated RLS before the
-- production frontend had moved to the authenticated path. This restores the
-- minimum Brian-scoped anon access needed by the live production app while
-- staging remains the auth test bed.

drop policy if exists prod_legacy_anon_program_select_brian on public.program;
create policy prod_legacy_anon_program_select_brian
on public.program
for select
to anon
using (user_id = 'brian');

drop policy if exists prod_legacy_anon_monthly_program_select_brian on public.monthly_program;
create policy prod_legacy_anon_monthly_program_select_brian
on public.monthly_program
for select
to anon
using (user_id = 'brian');

drop policy if exists prod_legacy_anon_sessions_select_brian on public.sessions;
create policy prod_legacy_anon_sessions_select_brian
on public.sessions
for select
to anon
using (user_id = 'brian');

drop policy if exists prod_legacy_anon_sessions_insert_brian on public.sessions;
create policy prod_legacy_anon_sessions_insert_brian
on public.sessions
for insert
to anon
with check (user_id = 'brian');

drop policy if exists prod_legacy_anon_sessions_update_brian on public.sessions;
create policy prod_legacy_anon_sessions_update_brian
on public.sessions
for update
to anon
using (user_id = 'brian')
with check (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_profile_select_brian on public.user_profile;
create policy prod_legacy_anon_user_profile_select_brian
on public.user_profile
for select
to anon
using (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_profile_insert_brian on public.user_profile;
create policy prod_legacy_anon_user_profile_insert_brian
on public.user_profile
for insert
to anon
with check (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_profile_update_brian on public.user_profile;
create policy prod_legacy_anon_user_profile_update_brian
on public.user_profile
for update
to anon
using (user_id = 'brian')
with check (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_measurements_select_brian on public.user_measurements;
create policy prod_legacy_anon_user_measurements_select_brian
on public.user_measurements
for select
to anon
using (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_measurements_insert_brian on public.user_measurements;
create policy prod_legacy_anon_user_measurements_insert_brian
on public.user_measurements
for insert
to anon
with check (user_id = 'brian');

drop policy if exists prod_legacy_anon_user_measurements_update_brian on public.user_measurements;
create policy prod_legacy_anon_user_measurements_update_brian
on public.user_measurements
for update
to anon
using (user_id = 'brian')
with check (user_id = 'brian');

commit;
