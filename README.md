# Logistics Operations Dashboard

**Live Demo:** https://logistics-operations-dashboard-wo4jzwehznchbxovucckxq.streamlit.app/

Portfolio-ready role-based logistics operations system built with Python, Streamlit and Supabase.

## Purpose
This project demonstrates practical logistics-management capability: fleet visibility, dispatch monitoring, inventory/materials control, finance, maintenance, soft gate-pass control, role-based access, operational KPIs and aviation/technical-spares awareness.

## Access modes
The public Streamlit app has two paths:

- **Secure Login** — Supabase email/password authentication with server-assigned roles.
- **Portfolio Demo** — fictional operational data that recruiters can explore without an account.

Authenticated users cannot choose their own role from the UI.

## Live Supabase backend
A dedicated zero-cost Supabase project has been created in region `ap-south-1`.

Project URL:
`https://duuzhgmvklnqiebadusc.supabase.co`

The repository does **not** contain the live publishable key or any secret/service-role key.

## Authentication architecture
Permanent roles are stored in `public.user_roles`. Database RLS resolves the signed-in user's role directly from that table using `auth.uid()`. A Custom Access Token Hook is optional convenience metadata, not the authorization source of truth.

See `docs/authentication.md` and `docs/role_matrix.md`.

## Role-based access
Supported roles:

- Senior Officers
- Log Staff Supervisor
- Log Staff
- Motor Vehicle Operations
- Fleet Drivers
- Accountant
- Motor Vehicle Maintenance
- Gate Security

Motor Vehicle Operations generates soft gate passes. Gate Security validates passes and records vehicle IN/OUT movement. Drivers are restricted to their own assignment/pass in authenticated mode.

## Dashboard capabilities
- Executive operational-readiness KPIs
- Fleet status / priority filters and map
- Dispatch event monitoring
- Technical and aviation-spares inventory
- Reorder watchlist
- Finance panel
- Maintenance workflow
- Soft gate-pass generation
- Gate IN/OUT movement log
- Management brief and exception board
- CSV operational snapshots
- Secure login + Portfolio Demo fallback

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Quality checks
```bash
python -m compileall app.py auth_layer.py data_access.py rbac.py demo_data.py scripts
python scripts/check_migrations.py
python scripts/smoke_test.py
python scripts/app_smoke_test.py
```

GitHub Actions runs these checks on pushes and pull requests.

## Database migration discipline
The authoritative applied migration history is mirrored under:

`supabase/migrations/`

Current live migration chain:

- `20261003032938_base_operational_schema.sql`
- `20261003032943_permanent_auth_rbac.sql`
- `20261003032947_role_workflow_tables.sql`
- `20261003032950_role_based_rls_policies.sql`
- `20261003033037_optimize_rbac_policies_and_indexes.sql`
- `20261003033153_harden_data_api_grants.sql`
- `20261003040221_provision_allowlisted_demo_accounts.sql`
- `20261003040426_support_server_app_metadata_role_fallback.sql`
- `20261003040532_enable_pg_net_for_bootstrap.sql`
- `20261003040748_database_authoritative_role_resolution.sql`
- `20261003040939_remove_unused_pg_net_bootstrap.sql`
- `20261003041945_harden_gate_security_movement_rpc.sql`
- `20261003042224_canonicalize_gate_pass_and_maintenance_ownership.sql`
- `20261003042345_harden_accountant_finance_rpc.sql`
- `20261003042741_replace_public_definer_rpcs_with_private_triggers.sql`

The `sql/` folder contains the original starter schema/checkpoints. The authoritative live migration history is under `supabase/migrations/`, and reproducible fictional live data is in `supabase/seed.sql`.

Future schema changes must be applied as a new migration and then mirrored into `supabase/migrations/`. Existing applied migrations should not be silently rewritten.

## Demo account provisioning
Four demo login identities are pre-approved in the private provisioning registry. When an Auth user is created with one of those emails, a database trigger automatically assigns the permanent role and personnel profile. The Allah Ditta driver account is also linked to fictional fleet unit `FLT-109`.

Actual passwords are deliberately not stored in GitHub, SQL migrations, or documentation.

## Current backend verification
- RLS enabled on all public application tables.
- Database/RLS security-definer warnings have been cleared. The remaining Auth advisor warning is that leaked-password protection is disabled and should be enabled from the Supabase Auth password settings.
- Anonymous table grants removed.
- Authenticated table grants reduced to the operations required by the application.
- Current RLS authorization resolves the permanent role directly from `public.user_roles` through a private security-definer helper bound to `auth.uid()`; JWT role claims are optional convenience metadata, not the authorization source of truth.
- Live fictional seed data currently includes 9 fleet rows, 10 inventory rows, 4 dispatch events, 3 maintenance jobs and 1 active Allah Ditta gate pass.

## Security
- Never commit `.streamlit/secrets.toml`.
- Use only the Supabase project URL + publishable key in Streamlit.
- Never expose the service-role/secret key.
- UI hiding is not treated as a security boundary; database RLS independently enforces access.
- Gate Security writes only movement records; private database triggers validate IN/OUT transitions and update gate-pass status.
- Accountant inserts are canonicalized by a private trigger, so recorder identity and optional vehicle linkage cannot be spoofed through the UI.
