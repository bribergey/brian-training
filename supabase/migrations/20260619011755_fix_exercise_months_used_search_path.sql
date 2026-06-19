begin;

-- Resolve Supabase advisor warning `function_search_path_mutable` for the
-- exercise catalog maintenance trigger function. This changes function
-- execution settings only; it does not mutate app data.

alter function public.update_exercise_months_used()
  set search_path = public, pg_temp;

commit;
