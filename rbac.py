ROLE_CONFIG = {
    "Senior Officers": {
        "slug": "senior_officer",
        "description": "Strategic oversight with read access across operations, finance, maintenance and gate activity.",
        "panels": [
            "Executive Overview",
            "Fleet & Map",
            "Materials",
            "Dispatch Log",
            "Management Brief",
            "Finance Summary",
            "Maintenance Overview",
            "Gate Movement Summary",
        ],
        "permissions": {
            "view_all_operations",
            "view_finance",
            "view_maintenance",
            "view_gate_activity",
        },
    },
    "Log Staff Supervisor": {
        "slug": "log_staff_supervisor",
        "description": "Operational supervision across fleet, materials, dispatch, maintenance and gate movement.",
        "panels": [
            "Executive Overview",
            "Fleet & Map",
            "Materials",
            "Dispatch Log",
            "Management Brief",
            "Maintenance Overview",
            "Gate Movement Summary",
        ],
        "permissions": {
            "view_all_operations",
            "view_maintenance",
            "view_gate_activity",
        },
    },
    "Log Staff": {
        "slug": "log_staff",
        "description": "Routine logistics visibility for fleet, materials and dispatch execution.",
        "panels": ["Fleet & Map", "Materials", "Dispatch Log"],
        "permissions": {"view_operations"},
    },
    "Motor Vehicle Operations": {
        "slug": "motor_vehicle_operations",
        "description": "Vehicle tasking, movement control and soft gate-pass generation.",
        "panels": ["Fleet & Map", "Dispatch Log", "Gate Pass Operations"],
        "permissions": {
            "view_operations",
            "view_gate_activity",
            "create_gate_pass",
        },
    },
    "Fleet Drivers": {
        "slug": "fleet_driver",
        "description": "Driver-only view of assigned vehicle, movement task and active soft gate pass.",
        "panels": ["Driver Panel"],
        "permissions": {"view_own_assignment", "view_own_gate_pass"},
    },
    "Accountant": {
        "slug": "accountant",
        "description": "Finance-only panel for transport, fuel, toll and maintenance cost visibility.",
        "panels": ["Accountant Panel"],
        "permissions": {"view_finance", "record_finance"},
    },
    "Motor Vehicle Maintenance": {
        "slug": "motor_vehicle_maintenance",
        "description": "Workshop panel for vehicle defects, maintenance jobs and service status.",
        "panels": ["Maintenance Panel", "Fleet & Map"],
        "permissions": {
            "view_maintenance",
            "update_maintenance",
            "view_operations",
        },
    },
    "Gate Security": {
        "slug": "gate_security",
        "description": "Gate-control panel to validate soft gate passes and record vehicle IN/OUT movement.",
        "panels": ["Gate Security Panel"],
        "permissions": {
            "view_gate_activity",
            "record_gate_movement",
        },
    },
}


def has_permission(role_name, permission):
    return permission in ROLE_CONFIG[role_name]["permissions"]


def role_panels(role_name):
    return ROLE_CONFIG[role_name]["panels"]


def role_description(role_name):
    return ROLE_CONFIG[role_name]["description"]
