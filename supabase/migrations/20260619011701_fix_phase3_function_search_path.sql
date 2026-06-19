begin;

-- Resolve Supabase advisor warning `function_search_path_mutable` for Phase 3
-- helper functions. This changes function execution settings only; it does not
-- mutate app data.

alter function public.phase3_touch_updated_at()
  set search_path = public, pg_temp;

alter function public.current_app_user_id()
  set search_path = public, pg_temp;

alter function public.current_staging_app_user_id()
  set search_path = public, pg_temp;

commit;
