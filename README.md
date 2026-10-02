# Logistics Streamlit Dashboard

Portfolio-ready logistics dashboard built with Python, Streamlit and Supabase.

## Scope
- Fleet / dispatch visibility
- Live location map from latitude/longitude
- Status filters and operational alerts
- Inventory / materials tracking
- Suitable foundation for aviation spares, technical procurement and logistics supervision portfolio use
- 10-second cached Supabase reads

## Local setup
1. Create a dedicated Supabase project.
2. Run `sql/001_initial_schema.sql` in the Supabase SQL editor.
3. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.
4. Add your Supabase project URL and publishable key.
5. Install dependencies:
   `pip install -r requirements.txt`
6. Run:
   `streamlit run app.py`

## Security
- Public/anonymous access is read-only.
- Authenticated operator access is granted CRUD permissions through RLS policies.
- Never put a Supabase secret/service-role key in Streamlit client-facing configuration.
