revoke all on public.fleet_data,
              public.dispatch_log,
              public.inventory_items,
              public.user_roles,
              public.personnel_profiles,
              public.vehicle_gate_passes,
              public.vehicle_gate_movements,
              public.vehicle_maintenance_records,
              public.transport_finance_entries
from anon, authenticated;

grant select, update on public.fleet_data to authenticated;
grant select, insert on public.dispatch_log to authenticated;
grant select, insert, update on public.inventory_items to authenticated;
grant select on public.personnel_profiles to authenticated;
grant select, insert, update on public.vehicle_gate_passes to authenticated;
grant select, insert on public.vehicle_gate_movements to authenticated;
grant select, insert, update on public.vehicle_maintenance_records to authenticated;
grant select, insert on public.transport_finance_entries to authenticated;

grant select on public.user_roles, public.personnel_profiles to supabase_auth_admin;

revoke all on sequence public.dispatch_log_id_seq,
                       public.vehicle_gate_movements_id_seq
from anon, authenticated;

grant usage, select on sequence public.dispatch_log_id_seq,
                                public.vehicle_gate_movements_id_seq
to authenticated;
