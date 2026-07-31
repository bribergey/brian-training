-- Add explicit nutrition-adjacent Daily Context flags without rewriting any
-- existing production or staging Daily Log rows. Existing rows remain null
-- until they are next saved through the app.

begin;

alter table training.daily_logs
  add column if not exists took_electrolytes boolean,
  add column if not exists had_protein_powder boolean;

alter table training.daily_logs_staging
  add column if not exists took_electrolytes boolean,
  add column if not exists had_protein_powder boolean;

comment on column training.daily_logs.took_electrolytes is
  'Whether electrolytes were intentionally consumed that day; null means not captured on the historical row.';
comment on column training.daily_logs.had_protein_powder is
  'Whether protein powder was consumed that day; null means not captured on the historical row.';
comment on column training.daily_logs_staging.took_electrolytes is
  'Staging equivalent of the production Daily Context electrolytes flag.';
comment on column training.daily_logs_staging.had_protein_powder is
  'Staging equivalent of the production Daily Context protein powder flag.';

commit;
