-- User-managed labels and recipe-revision state for reusable foods.
-- Production and staging receive the same schema while their rows remain
-- physically separate.

begin;

alter table training.nutrition_food_memory
  add column if not exists display_name text
    check (display_name is null or char_length(display_name) between 1 and 60),
  add column if not exists needs_reestimate boolean not null default false;

alter table training.nutrition_food_memory_staging
  add column if not exists display_name text
    check (display_name is null or char_length(display_name) between 1 and 60),
  add column if not exists needs_reestimate boolean not null default false;

comment on column training.nutrition_food_memory.display_name is
  'Optional user-chosen short label shown in reusable-food controls.';
comment on column training.nutrition_food_memory_staging.display_name is
  'Optional user-chosen short label shown in staging reusable-food controls.';
comment on column training.nutrition_food_memory.needs_reestimate is
  'True when the saved recipe changed and nutrient values must be refreshed on next use.';
comment on column training.nutrition_food_memory_staging.needs_reestimate is
  'True when the staging saved recipe changed and nutrient values must be refreshed on next use.';

commit;
