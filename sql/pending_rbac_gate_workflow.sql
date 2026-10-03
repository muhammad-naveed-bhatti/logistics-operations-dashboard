-- PENDING RBAC / GATE-WORKFLOW SCHEMA DRAFT
-- This is intentionally NOT a numbered migration.
-- Reason: the Supabase CLI is not available in the current runtime and no dedicated live
-- project is active. Per migration discipline, promote this draft using
-- `supabase migration new role_based_access_gate_workflow` when the project/CLI is available,
-- then review, run advisors, test, and commit the generated migration.
--
-- Authorization source for future Supabase Auth:
-- server-generated JWT claim: auth.jwt() ->> 'user_role'
-- The claim is populated from public.user_roles by the Custom Access Token Hook.
-- Never use user-editable raw_user_meta_data for authorization.

create table if not exists public.vehicle_gate_passes (
    id uuid primary key default gen_random_uuid(),
    pass_no text not null unique,
    fleet_id uuid not null references public.fleet_data(id) on delete restrict,
    driver_user_id uuid references auth.users(id) on delete set null,
    driver_name text not null,
    destination text not null,
    purpose text not null,
    issued_by uuid references auth.users(id) on delete set null,
    issued_at timestamptz not null default now(),
    valid_until timestamptz not null,
    status text not null default 'Issued'
        check (status in ('Issued','Vehicle Out','Closed','Cancelled')),
    created_at timestamptz not null default now()
);

create table if not exists public.vehicle_gate_movements (
    id bigint generated always as identity primary key,
    gate_pass_id uuid not null references public.vehicle_gate_passes(id) on delete restrict,
    movement_type text not null check (movement_type in ('IN','OUT')),
    gate_name text not null,
    recorded_by uuid not null references auth.users(id) on delete restrict,
    remarks text,
    event_time timestamptz not null default now()
);

create table if not exists public.vehicle_maintenance_records (
    id uuid primary key default gen_random_uuid(),
    job_no text not null unique,
    fleet_id uuid not null references public.fleet_data(id) on delete restrict,
    work_type text not null,
    complaint text not null,
    priority text not null default 'Normal'
        check (priority in ('Low','Normal','High','Critical')),
    status text not null default 'Scheduled'
        check (status in ('Scheduled','In Progress','Awaiting Parts','Completed','Cancelled')),
    opened_by uuid references auth.users(id) on delete set null,
    assigned_to uuid references auth.users(id) on delete set null,
    opened_at timestamptz not null default now(),
    target_completion timestamptz,
    closed_at timestamptz
);

create table if not exists public.transport_finance_entries (
    id uuid primary key default gen_random_uuid(),
    entry_no text not null unique,
    fleet_id uuid references public.fleet_data(id) on delete restrict,
    category text not null
        check (category in ('Fuel','Maintenance','Toll','Handling','Other')),
    amount numeric(14,2) not null check (amount >= 0),
    reference text,
    recorded_by uuid not null references auth.users(id) on delete restrict,
    entry_time timestamptz not null default now()
);

create index if not exists vehicle_gate_passes_fleet_idx
    on public.vehicle_gate_passes(fleet_id);
create index if not exists vehicle_gate_passes_driver_idx
    on public.vehicle_gate_passes(driver_user_id);
create index if not exists vehicle_gate_movements_pass_idx
    on public.vehicle_gate_movements(gate_pass_id);
create index if not exists vehicle_maintenance_fleet_idx
    on public.vehicle_maintenance_records(fleet_id);
create index if not exists transport_finance_fleet_idx
    on public.transport_finance_entries(fleet_id);

alter table public.vehicle_gate_passes enable row level security;
alter table public.vehicle_gate_movements enable row level security;
alter table public.vehicle_maintenance_records enable row level security;
alter table public.transport_finance_entries enable row level security;

-- Policy design to implement when promoted to a real migration:
-- senior_officer: read all operational/finance/maintenance/gate data
-- log_staff_supervisor: read operational/maintenance/gate data, no finance
-- log_staff: operational fleet/material/dispatch only
-- motor_vehicle_operations: read operations + create/manage gate passes
-- fleet_driver: read own assignment + own gate passes only
-- accountant: finance only
-- motor_vehicle_maintenance: maintenance read/update
-- gate_security: read active passes + INSERT gate movement only
--
-- Use (select auth.jwt() ->> 'user_role') for role checks.
-- Driver ownership policies must additionally bind driver_user_id = (select auth.uid()).
-- UPDATE policies require matching SELECT policy plus USING and WITH CHECK.
