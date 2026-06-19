grant select on table public.exercises to authenticated;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'exercises'
      and policyname = 'authenticated_select_exercises'
  ) then
    create policy authenticated_select_exercises
      on public.exercises
      for select
      to authenticated
      using (true);
  end if;
end $$;
