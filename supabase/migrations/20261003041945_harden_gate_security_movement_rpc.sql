drop policy if exists "authorized gate pass update" on public.vehicle_gate_passes;
drop policy if exists "mv ops gate pass update" on public.vehicle_gate_passes;

create policy "mv ops gate pass update"
on public.vehicle_gate_passes
for update
to authenticated
using ((select private.current_app_role()) = 'motor_vehicle_operations')
with check ((select private.current_app_role()) = 'motor_vehicle_operations');

drop policy if exists "gate security movement insert" on public.vehicle_gate_movements;

revoke insert on public.vehicle_gate_movements from authenticated;
revoke usage, select on sequence public.vehicle_gate_movements_id_seq from authenticated;

create or replace function public.record_gate_movement(
    p_gate_pass_id uuid,
    p_movement_type text,
    p_gate_name text,
    p_remarks text default null
)
returns table (
    gate_pass_id uuid,
    pass_no text,
    new_status text,
    movement_type text,
    event_time timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    current_pass_no text;
    current_valid_until timestamptz;
    next_status text;
    event_ts timestamptz := now();
    caller uuid := (select auth.uid());
begin
    if caller is null then
        raise exception 'Authentication required';
    end if;

    if (select private.current_app_role()) <> 'gate_security' then
        raise exception 'Gate movement recording is restricted to Gate Security';
    end if;

    if p_movement_type not in ('IN','OUT') then
        raise exception 'Movement must be IN or OUT';
    end if;

    select gp.status, gp.pass_no, gp.valid_until
      into current_status, current_pass_no, current_valid_until
      from public.vehicle_gate_passes gp
     where gp.id = p_gate_pass_id
     for update;

    if current_status is null then
        raise exception 'Gate pass not found';
    end if;

    if p_movement_type = 'OUT' and current_status = 'Issued' then
        if current_valid_until < event_ts then
            raise exception 'Gate pass has expired';
        end if;
        next_status := 'Vehicle Out';
    elsif p_movement_type = 'IN' and current_status = 'Vehicle Out' then
        next_status := 'Closed';
    else
        raise exception 'Invalid gate movement transition from status % using %',
            current_status, p_movement_type;
    end if;

    insert into public.vehicle_gate_movements (
        gate_pass_id, movement_type, gate_name, recorded_by, remarks, event_time
    )
    values (
        p_gate_pass_id, p_movement_type, p_gate_name, caller, p_remarks, event_ts
    );

    update public.vehicle_gate_passes
       set status = next_status
     where id = p_gate_pass_id;

    return query
    select p_gate_pass_id, current_pass_no, next_status, p_movement_type, event_ts;
end;
$$;

revoke execute on function public.record_gate_movement(uuid,text,text,text)
from public, anon;

grant execute on function public.record_gate_movement(uuid,text,text,text)
to authenticated;
