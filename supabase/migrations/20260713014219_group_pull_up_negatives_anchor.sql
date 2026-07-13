-- Treat the strict pull-up plus negative-rep variation as part of the same
-- rep-based Pull-up anchor metric. Existing workout JSON keeps the exercise
-- name; Analytics resolves it through this shared catalog row.

begin;

do $$
begin
  if not exists (
    select 1
    from training.exercises
    where name = 'Pull-up (Strict + Negatives)'
  ) then
    raise exception 'Expected exercise catalog row is missing: Pull-up (Strict + Negatives)';
  end if;
end
$$;

update training.exercises
set anchor_group = 'Pull-up',
    badge = 'anchor',
    rep_type = 'reps'
where name = 'Pull-up (Strict + Negatives)';

commit;
