create type public.app_role as enum (
    'senior_officer',
    'log_staff_supervisor',
    'log_staff',
    'motor_vehicle_operations',
    'fleet_driver',
    'accountant',
    'motor_vehicle_maintenance',
    'gate_security'
);

create table public.user_roles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    role public.app_role not null,
    assigned_at timestamptz not null default now(),
    assigned_by uuid references auth.users(id) on delete set null
);

create table public.personnel_profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    personnel_id text unique,
    display_name text not null,
    driver_name text,
    active boolean not null default true,
    updated_at timestamptz not null default now()
);

alter table public.user_roles enable row level security;
alter table public.personnel_profiles enable row level security;

create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
set search_path = ''
as $$
declare
    claims jsonb;
    assigned_role public.app_role;
    profile_personnel_id text;
    profile_driver_name text;
begin
    select ur.role into assigned_role
    from public.user_roles ur
    where ur.user_id = (event->>'user_id')::uuid;

    select pp.personnel_id, pp.driver_name
    into profile_personnel_id, profile_driver_name
    from public.personnel_profiles pp
    where pp.user_id = (event->>'user_id')::uuid
      and pp.active is true;

    claims := event->'claims';
    claims := jsonb_set(claims, '{user_role}', coalesce(to_jsonb(assigned_role), 'null'::jsonb));
    claims := jsonb_set(claims, '{personnel_id}', coalesce(to_jsonb(profile_personnel_id), 'null'::jsonb));
    claims := jsonb_set(claims, '{driver_name}', coalesce(to_jsonb(profile_driver_name), 'null'::jsonb));

    return jsonb_set(event, '{claims}', claims);
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook(jsonb) from authenticated, anon, public;

grant select on public.user_roles, public.personnel_profiles to supabase_auth_admin;

create policy "auth hook read roles"
on public.user_roles for select to supabase_auth_admin using (true);

create policy "auth hook read personnel"
on public.personnel_profiles for select to supabase_auth_admin using (true);

grant select on public.personnel_profiles to authenticated;

create policy "own personnel profile"
on public.personnel_profiles for select to authenticated
using ((select auth.uid()) = user_id);
