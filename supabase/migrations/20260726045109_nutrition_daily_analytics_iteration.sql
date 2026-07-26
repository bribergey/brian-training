-- Add auditable model usage/cost metadata and structured portion-learning
-- fields. Both production and staging receive the same schema; this migration
-- does not copy or modify production user data.

begin;

alter table training.nutrition_ai_runs
  add column if not exists prompt_tokens integer
    check (prompt_tokens is null or prompt_tokens >= 0),
  add column if not exists completion_tokens integer
    check (completion_tokens is null or completion_tokens >= 0),
  add column if not exists total_tokens integer
    check (total_tokens is null or total_tokens >= 0),
  add column if not exists cost_usd numeric(12,8)
    check (cost_usd is null or cost_usd >= 0),
  add column if not exists image_count integer not null default 0
    check (image_count >= 0),
  add column if not exists generation_id text;

alter table training.nutrition_ai_runs_staging
  add column if not exists prompt_tokens integer
    check (prompt_tokens is null or prompt_tokens >= 0),
  add column if not exists completion_tokens integer
    check (completion_tokens is null or completion_tokens >= 0),
  add column if not exists total_tokens integer
    check (total_tokens is null or total_tokens >= 0),
  add column if not exists cost_usd numeric(12,8)
    check (cost_usd is null or cost_usd >= 0),
  add column if not exists image_count integer not null default 0
    check (image_count >= 0),
  add column if not exists generation_id text;

alter table training.nutrition_food_memory
  add column if not exists description_patterns text[] not null default '{}'::text[],
  add column if not exists portion_notes jsonb not null default '{}'::jsonb
    check (jsonb_typeof(portion_notes) = 'object'),
  add column if not exists correction_count integer not null default 0
    check (correction_count >= 0);

alter table training.nutrition_food_memory_staging
  add column if not exists description_patterns text[] not null default '{}'::text[],
  add column if not exists portion_notes jsonb not null default '{}'::jsonb
    check (jsonb_typeof(portion_notes) = 'object'),
  add column if not exists correction_count integer not null default 0
    check (correction_count >= 0);

comment on column training.nutrition_food_memory.portion_notes is
  'Structured serving and visual portion cues reused in later food estimates.';
comment on column training.nutrition_food_memory_staging.portion_notes is
  'Structured serving and visual portion cues reused in later staging food estimates.';
comment on column training.nutrition_ai_runs.cost_usd is
  'Provider-reported inference cost for this model call, excluding credit-purchase fees.';
comment on column training.nutrition_ai_runs_staging.cost_usd is
  'Provider-reported inference cost for this staging model call, excluding credit-purchase fees.';

commit;
