-- Edge Functions use the service_role client for private-schema audit and
-- reusable-food writes. Table grants already exist, but the role also needs
-- USAGE on the containing schema.

begin;

grant usage on schema training to service_role;

commit;
