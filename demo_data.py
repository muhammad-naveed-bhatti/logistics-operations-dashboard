import pandas as pd
from datetime import datetime, timedelta, timezone

def build_demo_data():
    now = datetime.now(timezone.utc)

    fleet = pd.DataFrame([
        {"id":"fleet-101","truck_id":"FLT-101","driver":"Ahsan Malik","status":"In Transit","lat":31.5204,"lon":74.3587,"destination":"Lahore Dry Port","cargo":"Aircraft wheel assemblies","priority":"High","eta":now+timedelta(hours=3),"last_update":now},
        {"id":"fleet-102","truck_id":"FLT-102","driver":"Bilal Ahmed","status":"Loading","lat":31.4504,"lon":73.1350,"destination":"Islamabad Logistics Hub","cargo":"Avionics LRUs","priority":"Critical","eta":now+timedelta(hours=7),"last_update":now-timedelta(minutes=18)},
        {"id":"fleet-103","truck_id":"FLT-103","driver":"Usman Tariq","status":"Delayed","lat":33.6844,"lon":73.0479,"destination":"Rawalpindi Depot","cargo":"Hydraulic components","priority":"High","eta":now+timedelta(hours=5),"last_update":now-timedelta(minutes=55)},
        {"id":"fleet-104","truck_id":"FLT-104","driver":"Hamza Raza","status":"Available","lat":31.4180,"lon":73.0790,"destination":"Faisalabad Warehouse","cargo":"General stores","priority":"Normal","eta":pd.NaT,"last_update":now-timedelta(minutes=8)},
        {"id":"fleet-105","truck_id":"FLT-105","driver":"Saad Iqbal","status":"Maintenance","lat":32.1877,"lon":74.1945,"destination":"Gujranwala Workshop","cargo":"Vehicle spares","priority":"Normal","eta":pd.NaT,"last_update":now-timedelta(hours=2)},
        {"id":"fleet-106","truck_id":"FLT-106","driver":"Noman Ali","status":"In Transit","lat":24.8607,"lon":67.0011,"destination":"Karachi Cargo Terminal","cargo":"Engine consumables","priority":"Critical","eta":now+timedelta(hours=10),"last_update":now-timedelta(minutes=12)},
        {"id":"fleet-107","truck_id":"FLT-107","driver":"Fahad Khan","status":"Unloading","lat":30.1575,"lon":71.5249,"destination":"Multan Supply Depot","cargo":"Ground support equipment spares","priority":"High","eta":now+timedelta(hours=1),"last_update":now-timedelta(minutes=4)},
        {"id":"fleet-108","truck_id":"FLT-108","driver":"Imran Shah","status":"Available","lat":31.7054,"lon":72.9784,"destination":"Sargodha Materials Depot","cargo":"Routine replenishment","priority":"Low","eta":pd.NaT,"last_update":now-timedelta(minutes=25)},
        {"id":"fleet-109","truck_id":"FLT-109","driver":"Allah Ditta","status":"Available","lat":31.5204,"lon":74.3587,"destination":"Lahore Transport Yard","cargo":"Standby / local tasking","priority":"Normal","eta":pd.NaT,"last_update":now-timedelta(minutes=6)},
    ])

    inventory = pd.DataFrame([
        {"item_code":"AVN-001","item_name":"VHF Communication LRU","category":"Avionics","stock_qty":4,"reorder_level":3,"location":"Rack A-01","condition":"Serviceable","updated_at":now},
        {"item_code":"HYD-014","item_name":"Hydraulic Pump Assembly","category":"Hydraulics","stock_qty":2,"reorder_level":4,"location":"Rack B-12","condition":"Serviceable","updated_at":now},
        {"item_code":"ENG-207","item_name":"Oil Filter Element","category":"Engine Consumables","stock_qty":18,"reorder_level":12,"location":"Bin C-05","condition":"Serviceable","updated_at":now},
        {"item_code":"WHL-032","item_name":"Main Wheel Tyre","category":"Landing Gear","stock_qty":5,"reorder_level":6,"location":"Bay D-02","condition":"Serviceable","updated_at":now},
        {"item_code":"ELE-118","item_name":"28V DC Contactor","category":"Electrical","stock_qty":9,"reorder_level":5,"location":"Rack A-09","condition":"Serviceable","updated_at":now},
        {"item_code":"GSE-044","item_name":"Tow Bar Shear Pin Kit","category":"Ground Support Equipment","stock_qty":3,"reorder_level":5,"location":"GSE Store","condition":"Serviceable","updated_at":now},
        {"item_code":"SAF-011","item_name":"Safety Harness","category":"Safety Equipment","stock_qty":12,"reorder_level":8,"location":"Safety Store","condition":"Serviceable","updated_at":now},
        {"item_code":"GEN-087","item_name":"Industrial Grease Cartridge","category":"General Stores","stock_qty":26,"reorder_level":15,"location":"Bulk Store","condition":"Serviceable","updated_at":now},
        {"item_code":"FLT-901","item_name":"Fuel Hose Coupling","category":"Fuel Systems","stock_qty":1,"reorder_level":3,"location":"Hazmat Store","condition":"Serviceable","updated_at":now},
        {"item_code":"TOO-055","item_name":"Torque Wrench 40-200 Nm","category":"Tools","stock_qty":6,"reorder_level":4,"location":"Tool Crib","condition":"Calibration Due","updated_at":now},
    ])

    dispatch = pd.DataFrame([
        {"fleet_id":"fleet-101","event_type":"DISPATCHED","details":"Priority aviation spares dispatched to Lahore Dry Port.","event_time":now-timedelta(hours=2)},
        {"fleet_id":"fleet-103","event_type":"DELAY_ALERT","details":"Traffic disruption reported; ETA reviewed by control desk.","event_time":now-timedelta(minutes=35)},
        {"fleet_id":"fleet-102","event_type":"LOADING","details":"Critical avionics consignment under loading supervision.","event_time":now-timedelta(minutes=22)},
        {"fleet_id":"fleet-107","event_type":"ARRIVED","details":"GSE spares arrived at Multan Supply Depot.","event_time":now-timedelta(minutes=14)},
    ])
    return fleet, inventory, dispatch



def build_role_demo_data():
    now = datetime.now(timezone.utc)

    gate_passes = pd.DataFrame([
        {
            "pass_no": "GP-1001",
            "fleet_id": "FLT-101",
            "driver": "Ahsan Malik",
            "destination": "Lahore Dry Port",
            "purpose": "Aircraft wheel assemblies delivery",
            "issued_by": "MV Operations Desk",
            "issued_at": now - timedelta(hours=2),
            "valid_until": now + timedelta(hours=6),
            "status": "Issued",
        },
        {
            "pass_no": "GP-1002",
            "fleet_id": "FLT-106",
            "driver": "Noman Ali",
            "destination": "Karachi Cargo Terminal",
            "purpose": "Engine consumables movement",
            "issued_by": "MV Operations Desk",
            "issued_at": now - timedelta(hours=3),
            "valid_until": now + timedelta(hours=9),
            "status": "Vehicle Out",
        },
    ])

    gate_movements = pd.DataFrame([
        {
            "pass_no": "GP-1002",
            "fleet_id": "FLT-106",
            "driver": "Noman Ali",
            "movement": "OUT",
            "gate": "Main Gate",
            "recorded_by": "Gate Security",
            "event_time": now - timedelta(hours=2, minutes=45),
            "remarks": "Soft gate pass verified.",
        }
    ])

    maintenance_records = pd.DataFrame([
        {
            "job_no": "MX-001",
            "fleet_id": "FLT-105",
            "work_type": "Corrective",
            "complaint": "Brake inspection and workshop check",
            "priority": "High",
            "status": "In Progress",
            "opened_at": now - timedelta(hours=5),
            "target_completion": now + timedelta(hours=8),
        },
        {
            "job_no": "MX-002",
            "fleet_id": "FLT-104",
            "work_type": "Preventive",
            "complaint": "Scheduled oil/filter service",
            "priority": "Normal",
            "status": "Scheduled",
            "opened_at": now - timedelta(hours=1),
            "target_completion": now + timedelta(days=1),
        },
        {
            "job_no": "MX-003",
            "fleet_id": "FLT-108",
            "work_type": "Inspection",
            "complaint": "Tyre and battery condition inspection",
            "priority": "Low",
            "status": "Completed",
            "opened_at": now - timedelta(days=1),
            "target_completion": now - timedelta(hours=3),
        },
    ])

    finance_entries = pd.DataFrame([
        {"entry_no":"FN-001","fleet_id":"FLT-101","category":"Fuel","amount":28500.0,"reference":"Fuel issue / movement","entry_time":now-timedelta(hours=4)},
        {"entry_no":"FN-002","fleet_id":"FLT-103","category":"Toll","amount":6500.0,"reference":"Route toll / motorway","entry_time":now-timedelta(hours=3)},
        {"entry_no":"FN-003","fleet_id":"FLT-105","category":"Maintenance","amount":42000.0,"reference":"Brake inspection / workshop","entry_time":now-timedelta(hours=2)},
        {"entry_no":"FN-004","fleet_id":"FLT-106","category":"Fuel","amount":36000.0,"reference":"Long-route fuel issue","entry_time":now-timedelta(hours=1)},
        {"entry_no":"FN-005","fleet_id":"FLT-107","category":"Handling","amount":8500.0,"reference":"Loading/unloading support","entry_time":now-timedelta(minutes=40)},
    ])

    return gate_passes, gate_movements, maintenance_records, finance_entries
