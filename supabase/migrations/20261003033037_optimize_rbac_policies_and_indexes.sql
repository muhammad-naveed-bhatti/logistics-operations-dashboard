-- Add covering indexes for foreign keys flagged by Supabase advisors.
create index if not exists dispatch_log_fleet_idx on public.dispatch_log(fleet_id);
create index if not exists finance_recorded_by_idx on public.transport_finance_entries(recorded_by);
create index if not exists user_roles_assigned_by_idx on public.user_roles(assigned_by);
create index if not exists gate_movements_recorded_by_idx on public.vehicle_gate_movements(recorded_by);
create index if not exists gate_passes_issued_by_idx on public.vehicle_gate_passes(issued_by);
create index if not exists maintenance_assigned_to_idx on public.vehicle_maintenance_records(assigned_to);
create index if not exists maintenance_opened_by_idx on public.vehicle_maintenance_records(opened_by);

-- Recreate policies with cached auth.jwt() initialization and combine gate-pass update policies.
drop policy if exists "fleet role read" on public.fleet_data;
create policy "fleet role read" on public.fleet_data for select to authenticated
using (
    ((select auth.jwt()) ->> 'user_role') in (
        'senior_officer','log_staff_supervisor','log_staff',
        'motor_vehicle_operations','motor_vehicle_maintenance'
    )
    or (((select auth.jwt()) ->> 'user_role') = 'fleet_driver' and driver_user_id = (select auth.uid()))
);

drop policy if exists "fleet ops update" on public.fleet_data;
create policy "fleet ops update" on public.fleet_data for update to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','motor_vehicle_operations'))
with check (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','motor_vehicle_operations'));

drop policy if exists "dispatch role read" on public.dispatch_log;
create policy "dispatch role read" on public.dispatch_log for select to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('senior_officer','log_staff_supervisor','log_staff','motor_vehicle_operations'));

drop policy if exists "dispatch role insert" on public.dispatch_log;
create policy "dispatch role insert" on public.dispatch_log for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','log_staff','motor_vehicle_operations'));

drop policy if exists "inventory role read" on public.inventory_items;
create policy "inventory role read" on public.inventory_items for select to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('senior_officer','log_staff_supervisor','log_staff'));

drop policy if exists "inventory logistics insert" on public.inventory_items;
create policy "inventory logistics insert" on public.inventory_items for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','log_staff'));

drop policy if exists "inventory logistics update" on public.inventory_items;
create policy "inventory logistics update" on public.inventory_items for update to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','log_staff'))
with check (((select auth.jwt()) ->> 'user_role') in ('log_staff_supervisor','log_staff'));

drop policy if exists "gate pass read by role" on public.vehicle_gate_passes;
create policy "gate pass read by role" on public.vehicle_gate_passes for select to authenticated
using (
    ((select auth.jwt()) ->> 'user_role') in ('senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security')
    or (((select auth.jwt()) ->> 'user_role') = 'fleet_driver' and driver_user_id = (select auth.uid()))
);

drop policy if exists "mv ops create gate pass" on public.vehicle_gate_passes;
create policy "mv ops create gate pass" on public.vehicle_gate_passes for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') = 'motor_vehicle_operations' and issued_by = (select auth.uid()));

drop policy if exists "mv ops gate pass update" on public.vehicle_gate_passes;
drop policy if exists "gate security pass status update" on public.vehicle_gate_passes;
create policy "authorized gate pass update" on public.vehicle_gate_passes for update to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('motor_vehicle_operations','gate_security'))
with check (((select auth.jwt()) ->> 'user_role') in ('motor_vehicle_operations','gate_security'));

drop policy if exists "gate movement read" on public.vehicle_gate_movements;
create policy "gate movement read" on public.vehicle_gate_movements for select to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security'));

drop policy if exists "gate security movement insert" on public.vehicle_gate_movements;
create policy "gate security movement insert" on public.vehicle_gate_movements for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') = 'gate_security' and recorded_by = (select auth.uid()));

drop policy if exists "maintenance role read" on public.vehicle_maintenance_records;
create policy "maintenance role read" on public.vehicle_maintenance_records for select to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('senior_officer','log_staff_supervisor','motor_vehicle_maintenance'));

drop policy if exists "maintenance staff insert" on public.vehicle_maintenance_records;
create policy "maintenance staff insert" on public.vehicle_maintenance_records for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') = 'motor_vehicle_maintenance');

drop policy if exists "maintenance staff update" on public.vehicle_maintenance_records;
create policy "maintenance staff update" on public.vehicle_maintenance_records for update to authenticated
using (((select auth.jwt()) ->> 'user_role') = 'motor_vehicle_maintenance')
with check (((select auth.jwt()) ->> 'user_role') = 'motor_vehicle_maintenance');

drop policy if exists "finance read" on public.transport_finance_entries;
create policy "finance read" on public.transport_finance_entries for select to authenticated
using (((select auth.jwt()) ->> 'user_role') in ('senior_officer','accountant'));

drop policy if exists "accountant insert finance" on public.transport_finance_entries;
create policy "accountant insert finance" on public.transport_finance_entries for insert to authenticated
with check (((select auth.jwt()) ->> 'user_role') = 'accountant' and recorded_by = (select auth.uid()));
