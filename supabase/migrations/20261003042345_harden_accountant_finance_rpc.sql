alter table public.transport_finance_entries
add column if not exists vehicle_code text;

update public.transport_finance_entries e
set vehicle_code = f.truck_id
from public.fleet_data f
where f.id = e.fleet_id
  and e.vehicle_code is null;

drop policy if exists "accountant insert finance" on public.transport_finance_entries;
revoke insert on public.transport_finance_entries from authenticated;

create or replace function public.record_finance_entry(
    p_vehicle_code text,
    p_category text,
    p_amount numeric,
    p_reference text default null
)
returns table (
    entry_id uuid,
    entry_no text,
    vehicle_code text,
    category text,
    amount numeric,
    entry_time timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
    caller uuid := (select auth.uid());
    resolved_fleet_id uuid;
    normalized_vehicle_code text;
    generated_entry_no text;
    event_ts timestamptz := now();
begin
    if caller is null then
        raise exception 'Authentication required';
    end if;

    if (select private.current_app_role()) <> 'accountant' then
        raise exception 'Finance entry is restricted to Accountant';
    end if;

    if p_category not in ('Fuel','Maintenance','Toll','Handling','Other') then
        raise exception 'Invalid finance category';
    end if;

    if p_amount is null or p_amount < 0 then
        raise exception 'Amount must be zero or greater';
    end if;

    normalized_vehicle_code := nullif(btrim(p_vehicle_code), '');

    if normalized_vehicle_code is not null then
        select f.id, f.truck_id
          into resolved_fleet_id, normalized_vehicle_code
          from public.fleet_data f
         where lower(f.truck_id) = lower(normalized_vehicle_code)
         limit 1;

        if resolved_fleet_id is null then
            raise exception 'Vehicle code not found';
        end if;
    end if;

    generated_entry_no :=
        'FN-' ||
        to_char(clock_timestamp(), 'YYMMDDHH24MISS') ||
        '-' ||
        upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 4));

    insert into public.transport_finance_entries (
        entry_no, fleet_id, vehicle_code, category, amount,
        reference, recorded_by, entry_time
    )
    values (
        generated_entry_no, resolved_fleet_id, normalized_vehicle_code,
        p_category, p_amount, p_reference, caller, event_ts
    )
    returning
        id,
        transport_finance_entries.entry_no,
        transport_finance_entries.vehicle_code,
        transport_finance_entries.category,
        transport_finance_entries.amount,
        transport_finance_entries.entry_time
    into
        entry_id, entry_no, vehicle_code, category, amount, entry_time;

    return next;
end;
$$;

revoke execute on function public.record_finance_entry(text,text,numeric,text)
from public, anon;

grant execute on function public.record_finance_entry(text,text,numeric,text)
to authenticated;
