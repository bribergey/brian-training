-- CREATE OR REPLACE reset the view option in the already-applied nutrition
-- migration. Restore caller-scoped RLS behavior explicitly.

begin;

alter view public.user_profile set (security_invoker = true);
alter view public.user_profile_staging set (security_invoker = true);

commit;
