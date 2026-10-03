# Authentication & Permanent Role Assignment

## Runtime model

The Streamlit app has two access modes:

1. **Secure Login** — email/password authentication through Supabase Auth. The authenticated user's role is server-assigned and cannot be changed from the UI.
2. **Portfolio Demo** — a clearly labelled fictional-data mode where a recruiter can switch roles to inspect every panel.

## Permanent roles

Permanent application roles are stored in `public.user_roles`, keyed by `auth.users.id`.

Database RLS resolves the current role directly from `public.user_roles` using a private `SECURITY DEFINER` helper that is bound to `auth.uid()`. This is the authorization source of truth.

The optional Custom Access Token Hook can also expose the user's role and personnel identity as server-controlled JWT claims:

- `user_role`
- `personnel_id`
- `driver_name`

The Streamlit UI first reads safe server claims when available, then falls back to the user's own RLS-protected `user_roles` and `personnel_profiles` records. PostgreSQL RLS independently enforces permissions on protected tables.

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
4. Optionally enable the Custom Access Token Hook if JWT convenience claims are desired; RLS does not depend on it.
5. Create Auth users. The allowlisted demo accounts are auto-provisioned by database trigger.
6. Run RLS/security advisors and role-by-role access tests.
7. Add only the project URL + publishable key to Streamlit secrets.
8. Verify secure login, logout, role assignment, driver ownership and prohibited cross-role actions.


## Demo account registry

The private database registry pre-approves these role mappings:

- logofficer14406@gmail.com → Log Staff Supervisor
- technision865887@gmail.com → Motor Vehicle Maintenance
- gatesecuritystaff65@gmail.com → Gate Security
- driverAllahditta@gmail.com → Fleet Driver / Allah Ditta

Creating an Auth user with one of these addresses automatically provisions `public.user_roles` and `public.personnel_profiles`. The driver identity also binds to the fictional Allah Ditta fleet assignment.

Passwords are never stored in the repository or migration history.


## Restricted write workflows

- **Gate Security:** inserts a gate movement only. A private trigger verifies the user's permanent role, locks the gate-pass row, validates the legal transition, stamps `recorded_by = auth.uid()`, and updates the pass status. Gate Security has no direct gate-pass update policy.
- **Motor Vehicle Maintenance:** may insert maintenance jobs only with `opened_by = auth.uid()`; updates remain limited by maintenance-role RLS.
- **Accountant:** inserts finance rows only. A private trigger validates the accountant role, resolves an optional vehicle code to the canonical fleet UUID/code, stamps the authenticated recorder, and generates the entry number.
- **Motor Vehicle Operations:** creates soft gate passes; a server-side trigger canonicalizes vehicle code, driver name and linked driver user from the selected fleet record.

These database controls remain active even if the Streamlit UI is bypassed.
