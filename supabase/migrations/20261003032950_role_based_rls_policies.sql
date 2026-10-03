-- Initial role-based RLS policy set.
-- Superseded for performance by 20261003033037, but retained to mirror remote migration history.

create policy "fleet role read"
on public.fleet_data for select to authenticated
using (
    (select auth.jwt() ->> 'user_role') in (
        'senior_officer','log_staff_supervisor','log_staff',
        'motor_vehicle_operations','motor_vehicle_maintenance'
    )
    or (
        (select auth.jwt() ->> 'user_role') = 'fleet_driver'
        and driver_user_id = (select auth.uid())
    )
);

create policy "fleet ops update"
on public.fleet_data for update to authenticated
using ((select auth.jwt() ->> 'user_role') in ('log_staff_supervisor','motor_vehicle_operations'))
with check ((select auth.jwt() ->> 'user_role') in ('log_staff_supervisor','motor_vehicle_operations'));

create policy "dispatch role read"
on public.dispatch_log for select to authenticated
using ((select auth.jwt() ->> 'user_role') in (
    'senior_officer','log_staff_supervisor','log_staff','motor_vehicle_operations'
));

create policy "dispatch role insert"
on public.dispatch_log for insert to authenticated
with check ((select auth.jwt() ->> 'user_role') in (
    'log_staff_supervisor','log_staff','motor_vehicle_operations'
));

create policy "inventory role read"
on public.inventory_items for select to authenticated
using ((select auth.jwt() ->> 'user_role') in ('senior_officer','log_staff_supervisor','log_staff'));

create policy "inventory logistics insert"
on public.inventory_items for insert to authenticated
with check ((select auth.jwt() ->> 'user_role') in ('log_staff_supervisor','log_staff'));

create policy "inventory logistics update"
on public.inventory_items for update to authenticated
using ((select auth.jwt() ->> 'user_role') in ('log_staff_supervisor','log_staff'))
with check ((select auth.jwt() ->> 'user_role') in ('log_staff_supervisor','log_staff'));

create policy "gate pass read by role"
on public.vehicle_gate_passes for select to authenticated
using (
    (select auth.jwt() ->> 'user_role') in (
        'senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security'
    )
    or (
        (select auth.jwt() ->> 'user_role') = 'fleet_driver'
        and driver_user_id = (select auth.uid())
    )
);

create policy "mv ops create gate pass"
on public.vehicle_gate_passes for insert to authenticated
with check (
    (select auth.jwt() ->> 'user_role') = 'motor_vehicle_operations'
    and issued_by = (select auth.uid())
);

create policy "mv ops gate pass update"
on public.vehicle_gate_passes for update to authenticated
using ((select auth.jwt() ->> 'user_role') = 'motor_vehicle_operations')
with check ((select auth.jwt() ->> 'user_role') = 'motor_vehicle_operations');

create policy "gate security pass status update"
on public.vehicle_gate_passes for update to authenticated
using ((select auth.jwt() ->> 'user_role') = 'gate_security')
with check ((select auth.jwt() ->> 'user_role') = 'gate_security');

create policy "gate movement read"
on public.vehicle_gate_movements for select to authenticated
using ((select auth.jwt() ->> 'user_role') in (
    'senior_officer','log_staff_supervisor','motor_vehicle_operations','gate_security'
));

create policy "gate security movement insert"
on public.vehicle_gate_movements for insert to authenticated
with check (
    (select auth.jwt() ->> 'user_role') = 'gate_security'
    and recorded_by = (select auth.uid())
);

create policy "maintenance role read"
on public.vehicle_maintenance_records for select to authenticated
using ((select auth.jwt() ->> 'user_role') in (
    'senior_officer','log_staff_supervisor','motor_vehicle_maintenance'
));

create policy "maintenance staff insert"
on public.vehicle_maintenance_records for insert to authenticated
with check ((select auth.jwt() ->> 'user_role') = 'motor_vehicle_maintenance');

create policy "maintenance staff update"
on public.vehicle_maintenance_records for update to authenticated
using ((select auth.jwt() ->> 'user_role') = 'motor_vehicle_maintenance')
with check ((select auth.jwt() ->> 'user_role') = 'motor_vehicle_maintenance');

create policy "finance read"
on public.transport_finance_entries for select to authenticated
using ((select auth.jwt() ->> 'user_role') in ('senior_officer','accountant'));

create policy "accountant insert finance"
on public.transport_finance_entries for insert to authenticated
with check (
    (select auth.jwt() ->> 'user_role') = 'accountant'
    and recorded_by = (select auth.uid())
);
