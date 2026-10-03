alter table public.vehicle_gate_passes
add column if not exists vehicle_code text;

update public.vehicle_gate_passes gp
set vehicle_code = f.truck_id
from public.fleet_data f
where f.id = gp.fleet_id
  and gp.vehicle_code is null;

alter table public.vehicle_gate_passes
alter column vehicle_code set not null;

alter table public.vehicle_gate_passes
alter column pass_no set default (
  'GP-' ||
  to_char(clock_timestamp(), 'YYMMDDHH24MISS') ||
  '-' ||
  upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 4))
);

create or replace function public.canonicalize_gate_pass_vehicle()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
    fleet_record record;
begin
    select f.truck_id, f.driver, f.driver_user_id
      into fleet_record
      from public.fleet_data f
     where f.id = new.fleet_id;

    if not found then
        raise exception 'Fleet vehicle not found';
    end if;

    new.vehicle_code := fleet_record.truck_id;
    new.driver_name := fleet_record.driver;
    new.driver_user_id := fleet_record.driver_user_id;

    return new;
end;
$$;

revoke execute on function public.canonicalize_gate_pass_vehicle()
from public, anon, authenticated;

drop trigger if exists canonicalize_gate_pass_vehicle_before_insert
on public.vehicle_gate_passes;

create trigger canonicalize_gate_pass_vehicle_before_insert
before insert on public.vehicle_gate_passes
for each row
execute function public.canonicalize_gate_pass_vehicle();

drop policy if exists "maintenance staff insert" on public.vehicle_maintenance_records;

create policy "maintenance staff insert"
on public.vehicle_maintenance_records
for insert
to authenticated
with check (
    (select private.current_app_role()) = 'motor_vehicle_maintenance'
    and opened_by = (select auth.uid())
    and (assigned_to is null or assigned_to = (select auth.uid()))
);
