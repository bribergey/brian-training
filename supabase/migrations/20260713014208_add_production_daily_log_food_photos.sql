-- Private production food photos for Daily Log entries.
--
-- Objects use the path:
--   production/<auth-user-id>/<log-date>/<food-entry-id>/<photo-id>.<ext>
--
-- The existing bucket is shared by staging and production, while RLS keeps
-- both environments and users isolated by path prefix and auth user id.

begin;

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'daily-log-food-photos',
  'daily-log-food-photos',
  false,
  26214400,
  array[
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif'
  ]::text[]
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create policy production_daily_log_food_photos_select_own
on storage.objects
for select
to authenticated
using (
  bucket_id = 'daily-log-food-photos'
  and (storage.foldername(name))[1] = 'production'
  and (storage.foldername(name))[2] = (select auth.uid())::text
);

create policy production_daily_log_food_photos_insert_own
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'daily-log-food-photos'
  and (storage.foldername(name))[1] = 'production'
  and (storage.foldername(name))[2] = (select auth.uid())::text
);

create policy production_daily_log_food_photos_delete_own
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'daily-log-food-photos'
  and (storage.foldername(name))[1] = 'production'
  and (storage.foldername(name))[2] = (select auth.uid())::text
);

comment on column training.daily_logs.food_entries is
  'User-entered JSON array of {id, time, description, photos[]}; photo objects contain private Storage metadata only.';

commit;
