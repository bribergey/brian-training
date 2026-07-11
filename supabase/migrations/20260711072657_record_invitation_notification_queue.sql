create or replace function training.enqueue_invitation_notification()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  webhook_secret text;
begin
  select decrypted_secret
    into webhook_secret
    from vault.decrypted_secrets
   where name = 'briq_invite_webhook_secret'
   limit 1;

  if webhook_secret is null then
    raise warning 'Briq invitation webhook secret is not configured';
    return new;
  end if;

  perform net.http_post(
    url := 'https://mimvmaotzmacgiziovvi.supabase.co/functions/v1/notify-invitation-request',
    body := jsonb_build_object(
      'type', 'INSERT',
      'schema', 'training',
      'table', 'invitation_requests',
      'record', to_jsonb(new),
      'old_record', null
    ),
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-invite-webhook-secret', webhook_secret
    ),
    timeout_milliseconds := 5000
  );

  update training.invitation_requests
     set notified_at = clock_timestamp()
   where id = new.id
     and notified_at is null;

  return new;
exception
  when others then
    raise warning 'Could not queue Briq invitation notification (SQLSTATE %)', sqlstate;
    return new;
end;
$$;

revoke all on function training.enqueue_invitation_notification()
  from public, anon, authenticated;

comment on column training.invitation_requests.notified_at is
  'Time the event-driven invitation email was queued for asynchronous delivery.';
