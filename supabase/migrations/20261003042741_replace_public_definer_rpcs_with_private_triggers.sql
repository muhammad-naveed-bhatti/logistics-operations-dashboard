drop function if exists public.record_gate_movement(uuid,text,text,text);
drop function if exists public.record_finance_entry(text,text,numeric,text);

create or replace function private.prepare_gate_movement()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    caller uuid := (select auth.uid());
    current_status text;
    current_valid_until timestamptz;
begin
    if caller is null then
        raise exception 'Authentication required';
    end if;

    if (select private.current_app_role()) <> 'gate_security' then
        raise exception 'Gate movement recording is restricted to Gate Security';
    end if;

    if new.movement_type not in ('IN','OUT') then
        raise exception 'Movement must be IN or OUT';
    end if;

    select gp.status, gp.valid_until
      into current_status, current_valid_until
      from public.vehicle_gate_passes gp
     where gp.id = new.gate_pass_id
     for update;

    if current_status is null then
        raise exception 'Gate pass not found';
    end if;

    if new.movement_type = 'OUT' then
        if current_status <> 'Issued' then
            raise exception 'Vehicle OUT requires an Issued gate pass';
        end if;
        if current_valid_until < now() then
            raise exception 'Gate pass has expired';
        end if;
    elsif new.movement_type = 'IN' and current_status <> 'Vehicle Out' then
        raise exception 'Vehicle IN requires a Vehicle Out gate pass';
    end if;

    new.recorded_by := caller;
    new.event_time := now();
    return new;
end;
$$;

create or replace function private.apply_gate_movement_status()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    update public.vehicle_gate_passes
       set status = case
           when new.movement_type = 'OUT' then 'Vehicle Out'
           when new.movement_type = 'IN' then 'Closed'
           else status
       end
     where id = new.gate_pass_id;

    return new;
end;
$$;

revoke execute on function private.prepare_gate_movement()
from public, anon, authenticated;
revoke execute on function private.apply_gate_movement_status()
from public, anon, authenticated;

drop trigger if exists prepare_gate_movement_before_insert
on public.vehicle_gate_movements;
create trigger prepare_gate_movement_before_insert
before insert on public.vehicle_gate_movements
for each row execute function private.prepare_gate_movement();

drop trigger if exists apply_gate_movement_status_after_insert
on public.vehicle_gate_movements;
create trigger apply_gate_movement_status_after_insert
after insert on public.vehicle_gate_movements
for each row execute function private.apply_gate_movement_status();

grant insert on public.vehicle_gate_movements to authenticated;
grant usage, select on sequence public.vehicle_gate_movements_id_seq to authenticated;

drop policy if exists "gate security movement insert" on public.vehicle_gate_movements;
create policy "gate security movement insert"
on public.vehicle_gate_movements
for insert
to authenticated
with check (
    (select private.current_app_role()) = 'gate_security'
    and recorded_by = (select auth.uid())
);

create or replace function private.prepare_finance_entry()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    caller uuid := (select auth.uid());
    resolved_fleet_id uuid;
    canonical_vehicle_code text;
begin
    if caller is null then
        raise exception 'Authentication required';
    end if;

    if (select private.current_app_role()) <> 'accountant' then
        raise exception 'Finance entry is restricted to Accountant';
    end if;

    if new.category not in ('Fuel','Maintenance','Toll','Handling','Other') then
        raise exception 'Invalid finance category';
    end if;

    if new.amount is null or new.amount < 0 then
        raise exception 'Amount must be zero or greater';
    end if;

    canonical_vehicle_code := nullif(btrim(new.vehicle_code), '');

    if canonical_vehicle_code is not null then
        select f.id, f.truck_id
          into resolved_fleet_id, canonical_vehicle_code
          from public.fleet_data f
         where lower(f.truck_id) = lower(canonical_vehicle_code)
         limit 1;

        if resolved_fleet_id is null then
            raise exception 'Vehicle code not found';
        end if;
    end if;

    new.fleet_id := resolved_fleet_id;
    new.vehicle_code := canonical_vehicle_code;
    new.recorded_by := caller;
    new.entry_time := now();

    if new.entry_no is null or btrim(new.entry_no) = '' then
        new.entry_no :=
            'FN-' ||
            to_char(clock_timestamp(), 'YYMMDDHH24MISS') ||
            '-' ||
            upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 4));
    end if;

    return new;
end;
$$;

revoke execute on function private.prepare_finance_entry()
from public, anon, authenticated;

drop trigger if exists prepare_finance_entry_before_insert
on public.transport_finance_entries;
create trigger prepare_finance_entry_before_insert
before insert on public.transport_finance_entries
for each row execute function private.prepare_finance_entry();

grant insert on public.transport_finance_entries to authenticated;

drop policy if exists "accountant insert finance" on public.transport_finance_entries;
create policy "accountant insert finance"
on public.transport_finance_entries
for insert
to authenticated
with check (
    (select private.current_app_role()) = 'accountant'
    and recorded_by = (select auth.uid())
);
