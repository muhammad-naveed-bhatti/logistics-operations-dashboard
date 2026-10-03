# Authentication & Permanent Role Assignment

## Runtime model

The Streamlit app has two access modes:

1. **Secure Login** — email/password authentication through Supabase Auth. The authenticated user's role is server-assigned and cannot be changed from the UI.
2. **Portfolio Demo** — a clearly labelled fictional-data mode where a recruiter can switch roles to inspect every panel.

## Permanent roles

Permanent application roles are stored in `public.user_roles`, keyed by `auth.users.id`.

The Custom Access Token Hook reads the user's role and personnel identity and adds these server-controlled JWT claims:

- `user_role`
- `personnel_id`
- `driver_name`

The Streamlit UI uses these claims to choose the correct workspace. PostgreSQL RLS must independently enforce the same permissions on every protected table.

## Security rules

- Never authorize from `raw_user_meta_data`; users can edit it.
- Authenticated users cannot select their own role in the application.
- Driver accounts must be bound to a personnel/driver identity before the driver panel is available.
- Gate-security write policies should permit gate movement recording only.
- Motor Vehicle Operations should be the only operational role allowed to create gate passes.
- Accountant write policies should be limited to finance records.
- Maintenance write policies should be limited to maintenance workflow fields.
- Senior Officers receive broad read access, not automatic write authority.
- Service-role or secret keys must never be placed in Streamlit secrets or the public repository.

## Deployment sequence

1. Create the dedicated free Supabase project.
2. Apply the initial schema and RBAC/gate/auth schema through the migration workflow.
3. Explicitly grant Data API privileges required by each table.
4. Enable the Custom Access Token Hook.
5. Create test users and assign one role to each user in `public.user_roles`.
6. Run RLS/security advisors and role-by-role access tests.
7. Add only the project URL + publishable key to Streamlit secrets.
8. Verify secure login, logout, role assignment, driver ownership and prohibited cross-role actions.
