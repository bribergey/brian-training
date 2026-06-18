begin;

create extension if not exists pgcrypto;

create or replace function public.phase3_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid,
  user_id text not null,
  email text,
  display_name text,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.app_users_staging (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid,
  user_id text not null,
  email text,
  display_name text,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

alter table public.app_users add column if not exists auth_user_id uuid;
alter table public.app_users add column if not exists user_id text;
alter table public.app_users add column if not exists email text;
alter table public.app_users add column if not exists display_name text;
alter table public.app_users add column if not exists is_active boolean not null default true;
alter table public.app_users add column if not exists created_at timestamptz not null default timezone('utc', now());
alter table public.app_users add column if not exists updated_at timestamptz not null default timezone('utc', now());

alter table public.app_users_staging add column if not exists auth_user_id uuid;
alter table public.app_users_staging add column if not exists user_id text;
alter table public.app_users_staging add column if not exists email text;
alter table public.app_users_staging add column if not exists display_name text;
alter table public.app_users_staging add column if not exists is_active boolean not null default true;
alter table public.app_users_staging add column if not exists created_at timestamptz not null default timezone('utc', now());
alter table public.app_users_staging add column if not exists updated_at timestamptz not null default timezone('utc', now());

create unique index if not exists app_users_user_id_uidx
  on public.app_users (user_id);
create unique index if not exists app_users_auth_user_id_uidx
  on public.app_users (auth_user_id)
  where auth_user_id is not null;
create unique index if not exists app_users_email_uidx
  on public.app_users (lower(email))
  where email is not null;

create unique index if not exists app_users_staging_user_id_uidx
  on public.app_users_staging (user_id);
create unique index if not exists app_users_staging_auth_user_id_uidx
  on public.app_users_staging (auth_user_id)
  where auth_user_id is not null;
create unique index if not exists app_users_staging_email_uidx
  on public.app_users_staging (lower(email))
  where email is not null;

drop trigger if exists phase3_touch_updated_at_app_users on public.app_users;
create trigger phase3_touch_updated_at_app_users
before update on public.app_users
for each row
execute function public.phase3_touch_updated_at();

drop trigger if exists phase3_touch_updated_at_app_users_staging on public.app_users_staging;
create trigger phase3_touch_updated_at_app_users_staging
before update on public.app_users_staging
for each row
execute function public.phase3_touch_updated_at();

alter table public.app_users enable row level security;
alter table public.app_users_staging enable row level security;

drop policy if exists app_users_select_self on public.app_users;
create policy app_users_select_self
on public.app_users
for select
to authenticated
using (auth.uid() = auth_user_id and is_active = true);

drop policy if exists app_users_staging_select_self on public.app_users_staging;
create policy app_users_staging_select_self
on public.app_users_staging
for select
to authenticated
using (auth.uid() = auth_user_id and is_active = true);

create or replace function public.current_app_user_id()
returns text
language sql
stable
as $$
  select au.user_id
  from public.app_users au
  where au.auth_user_id = auth.uid()
    and au.is_active = true
  limit 1
$$;

create or replace function public.current_staging_app_user_id()
returns text
language sql
stable
as $$
  select au.user_id
  from public.app_users_staging au
  where au.auth_user_id = auth.uid()
    and au.is_active = true
  limit 1
$$;

grant execute on function public.current_app_user_id() to anon, authenticated, service_role;
grant execute on function public.current_staging_app_user_id() to anon, authenticated, service_role;

do $$
declare
  policy_row record;
  prod_tables text[] := array[
    'sessions',
    'program',
    'monthly_program',
    'user_profile',
    'user_measurements'
  ];
  staging_tables text[] := array[
    'sessions_staging',
    'program_staging',
    'monthly_program_staging',
    'user_profile_staging',
    'user_measurements_staging'
  ];
  table_name text;
begin
  for policy_row in
    select policyname, tablename
    from pg_policies
    where schemaname = 'public'
      and tablename = any(prod_tables || staging_tables)
  loop
    execute format('drop policy if exists %I on public.%I', policy_row.policyname, policy_row.tablename);
  end loop;

  foreach table_name in array prod_tables
  loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format(
      'create policy %I_select_own on public.%I for select to authenticated using (user_id = public.current_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_insert_own on public.%I for insert to authenticated with check (user_id = public.current_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_update_own on public.%I for update to authenticated using (user_id = public.current_app_user_id()) with check (user_id = public.current_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_delete_own on public.%I for delete to authenticated using (user_id = public.current_app_user_id())',
      table_name, table_name
    );
  end loop;

  foreach table_name in array staging_tables
  loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format(
      'create policy %I_select_own on public.%I for select to authenticated using (user_id = public.current_staging_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_insert_own on public.%I for insert to authenticated with check (user_id = public.current_staging_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_update_own on public.%I for update to authenticated using (user_id = public.current_staging_app_user_id()) with check (user_id = public.current_staging_app_user_id())',
      table_name, table_name
    );
    execute format(
      'create policy %I_delete_own on public.%I for delete to authenticated using (user_id = public.current_staging_app_user_id())',
      table_name, table_name
    );
  end loop;
end;
$$;

comment on table public.app_users is
  'Phase 3 auth mapping: production auth.users identities to app user_id ownership.';
comment on table public.app_users_staging is
  'Phase 3 auth mapping: staging auth.users identities to app user_id ownership.';

commit;
