-- Emergency PostgREST/Data API restoration.
--
-- On 2026-06-29, the training app could authenticate Brian through Supabase
-- Auth, but all REST calls failed with PGRST002 while PostgREST rebuilt its
-- schema cache. Postgres logs showed the root cause:
--
--   schema "options_trader" does not exist
--
-- Supabase troubleshooting for PGRST002 recommends temporarily recreating a
-- deleted schema that remains in the Data API exposed schema list, then
-- removing it from the Data API settings before dropping it later.
--
-- This schema is intentionally empty. It is not used by the training app and
-- does not create or mutate workout, program, profile, or measurement data.
create schema if not exists options_trader;

notify pgrst, 'reload schema';
notify pgrst, 'reload config';
