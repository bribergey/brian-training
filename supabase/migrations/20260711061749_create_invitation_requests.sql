create table training.invitation_requests (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null,
  source text not null default 'marketing_home',
  status text not null default 'new',
  created_at timestamptz not null default now(),
  notified_at timestamptz,
  constraint invitation_requests_name_length check (char_length(btrim(name)) between 1 and 120),
  constraint invitation_requests_email_length check (char_length(email) between 3 and 320),
  constraint invitation_requests_email_format check (email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'),
  constraint invitation_requests_source_check check (source = 'marketing_home'),
  constraint invitation_requests_status_check check (status in ('new', 'invited', 'declined', 'spam'))
);

comment on table training.invitation_requests is
  'Public marketing-site invitation requests. No workout or profile data is stored here.';

create unique index invitation_requests_email_unique
  on training.invitation_requests (lower(email));

create index invitation_requests_created_at_idx
  on training.invitation_requests (created_at desc);

alter table training.invitation_requests enable row level security;

revoke all on table training.invitation_requests from anon, authenticated;
grant insert (name, email, source) on training.invitation_requests to anon, authenticated;

create policy "public can request an invitation"
  on training.invitation_requests
  for insert
  to anon, authenticated
  with check (
    status = 'new'
    and source = 'marketing_home'
    and notified_at is null
    and created_at between now() - interval '5 minutes' and now() + interval '5 minutes'
  );
