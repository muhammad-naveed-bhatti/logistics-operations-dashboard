grant usage on schema private to authenticated;

create or replace function private.current_app_role()
returns public.app_role
language sql
stable
security definer
set search_path = ''
as $$
    select ur.role
    from public.user_roles ur
    where ur.user_id = (select auth.uid())
    limit 1
$$;

revoke execute on function private.current_app_role() from public, anon;
grant execute on function private.current_app_role() to authenticated;

grant select on public.user_roles to authenticated;

create policy "users can view own role"
on public.user_roles
for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "fleet role read" on public.fleet_data;
create policy "fleet role read"
on public.fleet_data for select to authenticated
using (
    (select private.current_app_role()) in (
        'senior_officer','log_staff_supervisor','log_staff',
        'motor_vehicle_operations','motor_vehicle_maintenance'
    )
    or (
        (select private.current_app_role()) = 'fleet_driver'
        and driver_user_id = (select auth.uid())
    )
);

drop policy if exists "fleet ops update" on public.fleet_data;
create policy "fleet ops update"
on public.fleet_data for update to authenticated
using ((select private.current_app_role()) in ('log_staff_supervisor','motor_vehicle_operations'))
with check ((select private.current_app_role()) in ('log_staff_supervisor','motor_vehicle_operations'));

drop policy if exists "dispatch role read" on public.dispatch_log;
create policy "dispatch role read"
on public.dispatch_log for select to authenticated
using ((select private.current_app_role()) in (
    'senior_officer','log_staff_supervisor','log_staff','motor_vehicle_operations'
));

drop policy if exists "dispatch role insert" on public.dispatch_log;
create policy "dispatch role insert"
on public.dispatch_log for insert to authenticated
with check ((select private.current_app_role()) in (
    'log_staff_supervisor','log_staff','motor_vehicle_operations'
));

drop policy if exists "inventory role read" on public.inventory_items;
create policy "inventory role read"
on public.inventory_items for select to authenticated
using ((select private.current_app_role()) in (
    'senior_officer','log_staff_supervisor','log_staff'
));

drop policy if exists "inventory logistics insert" on public.inventory_items;
create policy "inventory logistics insert"
on public.inventory_items for insert to authenticated
with check ((select private.current_app_role()) in ('log_staff_supervisor','log_staff'));

drop policy if exists "inventory logistics update" on public.inventory_items;
create policy "inventory logistics update"
on public.inventory_items for update to authenticated
using ((select private.current_app_role()) in ('log_staff_supervisor','log_staff'))
with check ((select private.current_app_role()) in ('log_staff_supervisor','log_staff'));

drop policy if exists "gate pass read by role" on public.vehicle_gate_passes;
create policy "gate pass read by role"
on public.vehicle_gate_passes for select to authenticated
using (
    (select private.current_app_role()) in (
        'senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security'
    )
    or (
        (select private.current_app_role()) = 'fleet_driver'
        and driver_user_id = (select auth.uid())
    )
);

drop policy if exists "mv ops create gate pass" on public.vehicle_gate_passes;
create policy "mv ops create gate pass"
on public.vehicle_gate_passes for insert to authenticated
with check (
    (select private.current_app_role()) = 'motor_vehicle_operations'
    and issued_by = (select auth.uid())
);

drop policy if exists "authorized gate pass update" on public.vehicle_gate_passes;
create policy "authorized gate pass update"
on public.vehicle_gate_passes for update to authenticated
using ((select private.current_app_role()) in ('motor_vehicle_operations','gate_security'))
with check ((select private.current_app_role()) in ('motor_vehicle_operations','gate_security'));

drop policy if exists "gate movement read" on public.vehicle_gate_movements;
create policy "gate movement read"
on public.vehicle_gate_movements for select to authenticated
using ((select private.current_app_role()) in (
    'senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security'
));

drop policy if exists "gate security movement insert" on public.vehicle_gate_movements;
create policy "gate security movement insert"
on public.vehicle_gate_movements for insert to authenticated
with check (
    (select private.current_app_role()) = 'gate_security'
    and recorded_by = (select auth.uid())
);

drop policy if exists "maintenance role read" on public.vehicle_maintenance_records;
create policy "maintenance role read"
on public.vehicle_maintenance_records for select to authenticated
using ((select private.current_app_role()) in (
    'senior_officer','log_staff_supervisor','motor_vehicle_maintenance'
));

drop policy if exists "maintenance staff insert" on public.vehicle_maintenance_records;
create policy "maintenance staff insert"
on public.vehicle_maintenance_records for insert to authenticated
with check ((select private.current_app_role()) = 'motor_vehicle_maintenance');

drop policy if exists "maintenance staff update" on public.vehicle_maintenance_records;
create policy "maintenance staff update"
on public.vehicle_maintenance_records for update to authenticated
using ((select private.current_app_role()) = 'motor_vehicle_maintenance')
with check ((select private.current_app_role()) = 'motor_vehicle_maintenance');

drop policy if exists "finance read" on public.transport_finance_entries;
create policy "finance read"
on public.transport_finance_entries for select to authenticated
using ((select private.current_app_role()) in ('senior_officer','accountant'));

drop policy if exists "accountant insert finance" on public.transport_finance_entries;
create policy "accountant insert finance"
on public.transport_finance_entries for insert to authenticated
with check (
    (select private.current_app_role()) = 'accountant'
    and recorded_by = (select auth.uid())
);
