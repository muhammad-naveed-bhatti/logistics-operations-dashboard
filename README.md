# Logistics Operations Dashboard

**Live Demo:** https://logistics-operations-dashboard-wo4jzwehznchbxovucckxq.streamlit.app/

Portfolio-ready logistics operations system built with Python and Streamlit, with an optional Supabase backend.

## Purpose
This project demonstrates practical logistics-management capability in a recruiter-friendly, zero-cost demo: fleet visibility, dispatch monitoring, inventory/materials control, exception handling, operational KPIs, and aviation/technical-spares awareness.

## Zero-cost demo mode
A live database is not required. If Supabase secrets are absent, the app automatically loads the realistic dataset in `demo_data.py`. This makes the Streamlit deployment self-contained for portfolio visitors.

## Optional Supabase mode
When `SUPABASE_URL` and `SUPABASE_KEY` are configured, the same user interface reads from Supabase tables. The public demo can therefore remain free while the repository still demonstrates a database-ready architecture.

## Authentication architecture
The application now contains a secure-login path for Supabase email/password authentication while preserving a separate recruiter-friendly Portfolio Demo mode.

Authenticated roles are server-assigned and are never selectable from the UI. Permanent RBAC is prepared through `public.user_roles` + a Custom Access Token Hook; see `docs/authentication.md`.

## Role-based access
The demo now includes role-specific workspaces for Senior Officers, Log Staff Supervisor, Log Staff, Motor Vehicle Operations, Fleet Drivers, Accountant, Motor Vehicle Maintenance, and Gate Security.

Motor Vehicle Operations can generate soft gate passes. Gate Security can validate the active pass and record vehicle IN/OUT movements. Driver access is limited to the selected driver's own assignment/pass in the demo simulation.

See `docs/role_matrix.md` for the full access matrix. UI restrictions are a demo layer; production enforcement will use Supabase Auth + RLS.

## Dashboard capabilities
- Executive operational-readiness KPIs
- Schedule-health and stock-readiness indicators
- Fleet status and priority filters
- Vehicle location map
- Delay / critical-load exception board
- Aviation and technical-spares inventory
- Reorder alerts
- Dispatch event log
- Automated management brief
- CSV exports for operational snapshots
- Automatic local demo-data fallback

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Quality checks
```bash
python -m compileall app.py demo_data.py scripts
python scripts/check_migrations.py
python scripts/smoke_test.py
python scripts/app_smoke_test.py
```

GitHub Actions runs the same checks on pushes and pull requests.

## Database versioning / migration discipline
SQL is versioned under `sql/`:

- `001_initial_schema.sql` — initial schema, indexes, RLS and grants
- `002_sample_data.sql` — optional database seed/checkpoint data
- `pending_rbac_gate_workflow.sql` — reviewed schema draft for gate/maintenance/finance workflow
- `pending_auth_rbac.sql` — permanent user-role + Auth-hook schema draft
Both are intentionally pending until the dedicated Supabase project/migration workflow is approved.

Future schema changes should receive the next numbered migration/checkpoint rather than silently rewriting earlier database history. The migration checker validates sequential numbering.

## Streamlit deployment
The repository is intentionally self-contained. A public Streamlit deployment can run in demo mode without secrets. Supabase can be connected later without redesigning the dashboard.

## Security
- Never commit `.streamlit/secrets.toml`.
- Use only a Supabase publishable key in Streamlit.
- Keep service-role / secret keys out of client-facing configuration.
