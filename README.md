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
Permanent roles are stored in `public.user_roles`. A Custom Access Token Hook injects server-controlled `user_role`, `personnel_id` and `driver_name` claims into the JWT.

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
python -m compileall app.py auth_layer.py rbac.py demo_data.py scripts
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

The `sql/` folder contains the original starter schema and demo seed data; it is no longer the authoritative live migration history.

Future schema changes must be applied as a new migration and then mirrored into `supabase/migrations/`. Existing applied migrations should not be silently rewritten.

## Current backend verification
- RLS enabled on all public application tables.
- Supabase security advisor reports no security lints.
- Anonymous table grants removed.
- Authenticated table grants reduced to the operations required by the application.
- Role policies use server-issued JWT role claims.
- Demo seed data loaded: 8 fleet rows, 10 inventory rows and 4 dispatch events.

## Security
- Never commit `.streamlit/secrets.toml`.
- Use only the Supabase project URL + publishable key in Streamlit.
- Never expose the service-role/secret key.
- UI hiding is not treated as a security boundary; database RLS independently enforces access.
