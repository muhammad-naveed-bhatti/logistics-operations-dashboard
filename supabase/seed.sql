-- Fictional portfolio/test data for the live Supabase backend.
-- Safe to re-run: fleet/inventory use upserts; event/workflow seeds use stable keys.

insert into public.fleet_data (
    truck_id, driver, status, lat, lon, destination, cargo, priority, eta, last_update
)
values
('FLT-101','Ahsan Malik','In Transit',31.5204,74.3587,'Lahore Dry Port','Aircraft wheel assemblies','High',now() + interval '3 hours',now()),
('FLT-102','Bilal Ahmed','Loading',31.4504,73.1350,'Islamabad Logistics Hub','Avionics LRUs','Critical',now() + interval '7 hours',now() - interval '18 minutes'),
('FLT-103','Usman Tariq','Delayed',33.6844,73.0479,'Rawalpindi Depot','Hydraulic components','High',now() + interval '5 hours',now() - interval '55 minutes'),
('FLT-104','Hamza Raza','Available',31.4180,73.0790,'Faisalabad Warehouse','General stores','Normal',null,now() - interval '8 minutes'),
('FLT-105','Saad Iqbal','Maintenance',32.1877,74.1945,'Gujranwala Workshop','Vehicle spares','Normal',null,now() - interval '2 hours'),
('FLT-106','Noman Ali','In Transit',24.8607,67.0011,'Karachi Cargo Terminal','Engine consumables','Critical',now() + interval '10 hours',now() - interval '12 minutes'),
('FLT-107','Fahad Khan','Unloading',30.1575,71.5249,'Multan Supply Depot','Ground support equipment spares','High',now() + interval '1 hour',now() - interval '4 minutes'),
('FLT-108','Imran Shah','Available',31.7054,72.9784,'Sargodha Materials Depot','Routine replenishment','Low',null,now() - interval '25 minutes'),
('FLT-109','Allah Ditta','Available',31.5204,74.3587,'Lahore Transport Yard','Standby / local tasking','Normal',null,now() - interval '6 minutes')
on conflict (truck_id) do update set
 driver=excluded.driver,
 status=excluded.status,
 lat=excluded.lat,
 lon=excluded.lon,
 destination=excluded.destination,
 cargo=excluded.cargo,
 priority=excluded.priority,
 eta=excluded.eta,
 last_update=excluded.last_update;

insert into public.inventory_items (
    item_code,item_name,category,stock_qty,reorder_level,location,condition,updated_at
)
values
('AVN-001','VHF Communication LRU','Avionics',4,3,'Rack A-01','Serviceable',now()),
('HYD-014','Hydraulic Pump Assembly','Hydraulics',2,4,'Rack B-12','Serviceable',now()),
('ENG-207','Oil Filter Element','Engine Consumables',18,12,'Bin C-05','Serviceable',now()),
('WHL-032','Main Wheel Tyre','Landing Gear',5,6,'Bay D-02','Serviceable',now()),
('ELE-118','28V DC Contactor','Electrical',9,5,'Rack A-09','Serviceable',now()),
('GSE-044','Tow Bar Shear Pin Kit','Ground Support Equipment',3,5,'GSE Store','Serviceable',now()),
('SAF-011','Safety Harness','Safety Equipment',12,8,'Safety Store','Serviceable',now()),
('GEN-087','Industrial Grease Cartridge','General Stores',26,15,'Bulk Store','Serviceable',now()),
('FLT-901','Fuel Hose Coupling','Fuel Systems',1,3,'Hazmat Store','Serviceable',now()),
('TOO-055','Torque Wrench 40-200 Nm','Tools',6,4,'Tool Crib','Calibration Due',now())
on conflict (item_code) do update set
 item_name=excluded.item_name,
 category=excluded.category,
 stock_qty=excluded.stock_qty,
 reorder_level=excluded.reorder_level,
 location=excluded.location,
 condition=excluded.condition,
 updated_at=excluded.updated_at;

insert into public.dispatch_log (fleet_id,event_type,details,event_time)
select id,'DISPATCHED','Priority aviation spares dispatched to Lahore Dry Port.',now() - interval '2 hours'
from public.fleet_data f
where f.truck_id='FLT-101'
and not exists (
  select 1 from public.dispatch_log d
  where d.fleet_id=f.id and d.event_type='DISPATCHED'
);

insert into public.dispatch_log (fleet_id,event_type,details,event_time)
select id,'DELAY_ALERT','Traffic disruption reported; ETA reviewed by control desk.',now() - interval '35 minutes'
from public.fleet_data f
where f.truck_id='FLT-103'
and not exists (
  select 1 from public.dispatch_log d
  where d.fleet_id=f.id and d.event_type='DELAY_ALERT'
);

insert into public.dispatch_log (fleet_id,event_type,details,event_time)
select id,'LOADING','Critical avionics consignment under loading supervision.',now() - interval '22 minutes'
from public.fleet_data f
where f.truck_id='FLT-102'
and not exists (
  select 1 from public.dispatch_log d
  where d.fleet_id=f.id and d.event_type='LOADING'
);

insert into public.dispatch_log (fleet_id,event_type,details,event_time)
select id,'ARRIVED','GSE spares arrived at Multan Supply Depot.',now() - interval '14 minutes'
from public.fleet_data f
where f.truck_id='FLT-107'
and not exists (
  select 1 from public.dispatch_log d
  where d.fleet_id=f.id and d.event_type='ARRIVED'
);

insert into public.vehicle_maintenance_records (
    job_no, fleet_id, work_type, complaint, priority, status,
    opened_by, assigned_to, opened_at, target_completion
)
select
  'MX-LIVE-001', f.id, 'Corrective', 'Brake inspection and workshop check',
  'High', 'In Progress', u.id, u.id,
  now() - interval '5 hours', now() + interval '8 hours'
from public.fleet_data f
left join auth.users u on lower(u.email)='technision865887@gmail.com'
where f.truck_id='FLT-105'
on conflict (job_no) do nothing;

insert into public.vehicle_maintenance_records (
    job_no, fleet_id, work_type, complaint, priority, status,
    opened_by, assigned_to, opened_at, target_completion
)
select
  'MX-LIVE-002', f.id, 'Preventive', 'Scheduled oil/filter service',
  'Normal', 'Scheduled', u.id, u.id,
  now() - interval '1 hour', now() + interval '1 day'
from public.fleet_data f
left join auth.users u on lower(u.email)='technision865887@gmail.com'
where f.truck_id='FLT-104'
on conflict (job_no) do nothing;

insert into public.vehicle_maintenance_records (
    job_no, fleet_id, work_type, complaint, priority, status,
    opened_by, assigned_to, opened_at, target_completion, closed_at
)
select
  'MX-LIVE-003', f.id, 'Inspection', 'Tyre and battery condition inspection',
  'Low', 'Completed', u.id, u.id,
  now() - interval '1 day', now() - interval '3 hours', now() - interval '3 hours'
from public.fleet_data f
left join auth.users u on lower(u.email)='technision865887@gmail.com'
where f.truck_id='FLT-108'
on conflict (job_no) do nothing;

insert into public.vehicle_gate_passes (
    pass_no, fleet_id, driver_name, vehicle_code, destination, purpose,
    issued_by, valid_until, status
)
select
  'GP-DEMO-ALLAHD-01',
  f.id,
  f.driver,
  f.truck_id,
  'Lahore Logistics Gate',
  'Authenticated Gate Security workflow test',
  null,
  now() + interval '12 hours',
  'Issued'
from public.fleet_data f
where f.truck_id='FLT-109'
and not exists (
  select 1 from public.vehicle_gate_passes
  where pass_no='GP-DEMO-ALLAHD-01'
);
