create schema if not exists private;

revoke all on schema private from public, anon, authenticated;

create table if not exists private.demo_user_registry (
    email text primary key,
    role public.app_role not null,
    display_name text not null,
    personnel_id text not null unique,
    driver_name text
);

revoke all on private.demo_user_registry from public, anon, authenticated;

insert into private.demo_user_registry (email, role, display_name, personnel_id, driver_name)
values
('logofficer14406@gmail.com','log_staff_supervisor','Demo Log Staff Supervisor','DEMO-LSS-001',null),
('technision865887@gmail.com','motor_vehicle_maintenance','Demo Motor Vehicle Technician','DEMO-MVM-001',null),
('gatesecuritystaff65@gmail.com','gate_security','Demo Gate Security Staff','DEMO-GS-001',null),
('driverAllahditta@gmail.com','fleet_driver','Allah Ditta','DEMO-DRV-001','Allah Ditta')
on conflict (email) do update set
 role=excluded.role,
 display_name=excluded.display_name,
 personnel_id=excluded.personnel_id,
 driver_name=excluded.driver_name;

create or replace function private.provision_demo_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    registry private.demo_user_registry%rowtype;
begin
    select *
      into registry
      from private.demo_user_registry
     where lower(email) = lower(new.email);

    if found then
        insert into public.user_roles (user_id, role, assigned_by)
        values (new.id, registry.role, null)
        on conflict (user_id) do update
        set role = excluded.role,
            assigned_at = now();

        insert into public.personnel_profiles (
            user_id, personnel_id, display_name, driver_name, active, updated_at
        )
        values (
            new.id, registry.personnel_id, registry.display_name,
            registry.driver_name, true, now()
        )
        on conflict (user_id) do update
        set personnel_id = excluded.personnel_id,
            display_name = excluded.display_name,
            driver_name = excluded.driver_name,
            active = true,
            updated_at = now();

        if registry.role = 'fleet_driver' and registry.driver_name is not null then
            update public.fleet_data
               set driver_user_id = new.id,
                   driver = registry.driver_name
             where driver = registry.driver_name;
        end if;
    end if;

    return new;
end;
$$;

revoke execute on function private.provision_demo_user()
from public, anon, authenticated;

drop trigger if exists on_demo_auth_user_created on auth.users;
create trigger on_demo_auth_user_created
after insert on auth.users
for each row execute function private.provision_demo_user();

insert into public.fleet_data (
    truck_id, driver, status, lat, lon, destination, cargo, priority, eta, last_update
)
values (
    'FLT-109','Allah Ditta','Available',31.5204,74.3587,
    'Lahore Transport Yard','Standby / local tasking','Normal',null,now()
)
on conflict (truck_id) do update
set driver=excluded.driver,
    status=excluded.status,
    lat=excluded.lat,
    lon=excluded.lon,
    destination=excluded.destination,
    cargo=excluded.cargo,
    priority=excluded.priority,
    eta=excluded.eta,
    last_update=excluded.last_update;
