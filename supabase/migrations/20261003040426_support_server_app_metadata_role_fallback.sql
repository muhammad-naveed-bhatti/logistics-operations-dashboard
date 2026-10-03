-- Historical intermediate migration.
-- This policy version added server-controlled app_metadata role fallback.
-- It was later superseded by 20261003040748_database_authoritative_role_resolution.sql.
-- Retained as a timestamped migration marker to keep repository history aligned.
select 1;
