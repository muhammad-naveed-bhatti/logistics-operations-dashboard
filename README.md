# Logistics Operations Dashboard

Portfolio-ready logistics dashboard built with Python and Streamlit, with an optional Supabase backend.

## Why this project exists
This is a zero-cost portfolio demonstration of logistics operations capability: fleet visibility, dispatch monitoring, inventory/materials control, exception management, and aviation/technical-spares awareness.

## Demo mode
No live database is required. If Supabase secrets are absent, the app automatically loads the realistic dataset in `demo_data.py`. This makes the Streamlit deployment self-contained and suitable for recruiters and portfolio visitors.

## Optional Supabase mode
When `SUPABASE_URL` and `SUPABASE_KEY` are configured, the same UI reads from Supabase tables.

## Features
- Fleet KPI scorecard
- Fleet status and priority filters
- Vehicle location map
- Delayed/critical shipment exception board
- Aviation and technical-spares inventory
- Reorder alerts
- Dispatch event log
- Automatic demo-data fallback

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Database versioning
SQL is versioned under `sql/`:
- `001_initial_schema.sql` — initial schema, indexes, RLS, grants
- `002_sample_data.sql` — optional database seed data

For future schema changes, add a new numbered migration/checkpoint rather than editing history silently.

## Security
- Never commit `.streamlit/secrets.toml`.
- Use only a Supabase publishable key in Streamlit.
- Keep service-role/secret keys out of client-facing configuration.
