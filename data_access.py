from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd


def fetch_table(client, name, order_col=None):
    query = client.table(name).select("*")
    if order_col:
        query = query.order(order_col, desc=True)
    return pd.DataFrame(query.execute().data)


def fetch_workflow_data(client):
    return {
        "gate_passes": fetch_table(client, "vehicle_gate_passes", "issued_at"),
        "gate_movements": fetch_table(client, "vehicle_gate_movements", "event_time"),
        "maintenance": fetch_table(client, "vehicle_maintenance_records", "opened_at"),
        "finance": fetch_table(client, "transport_finance_entries", "entry_time"),
    }


def create_gate_pass(client, fleet_id, destination, purpose, issued_by, valid_until):
    payload = {
        "fleet_id": str(fleet_id),
        "destination": destination,
        "purpose": purpose,
        "issued_by": str(issued_by),
        "valid_until": valid_until.astimezone(timezone.utc).isoformat(),
        "status": "Issued",
    }
    return client.table("vehicle_gate_passes").insert(payload).execute().data


def record_gate_movement(client, gate_pass_id, movement_type, gate_name, remarks):
    payload = {
        "gate_pass_id": str(gate_pass_id),
        "movement_type": movement_type,
        "gate_name": gate_name,
        "remarks": remarks,
    }
    return client.table("vehicle_gate_movements").insert(payload).execute().data


def create_maintenance_job(
    client,
    fleet_id,
    work_type,
    complaint,
    priority,
    user_id,
    target_completion=None,
):
    payload = {
        "job_no": f"MX-{datetime.now(timezone.utc):%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}",
        "fleet_id": str(fleet_id),
        "work_type": work_type,
        "complaint": complaint,
        "priority": priority,
        "status": "Scheduled",
        "opened_by": str(user_id),
        "assigned_to": str(user_id),
        "target_completion": (
            target_completion.astimezone(timezone.utc).isoformat()
            if target_completion is not None
            else None
        ),
    }
    return client.table("vehicle_maintenance_records").insert(payload).execute().data


def update_maintenance_status(client, record_id, new_status):
    payload = {
        "status": new_status,
        "closed_at": (
            datetime.now(timezone.utc).isoformat()
            if new_status == "Completed"
            else None
        ),
    }
    return (
        client.table("vehicle_maintenance_records")
        .update(payload)
        .eq("id", str(record_id))
        .execute()
        .data
    )


def record_finance_entry(
    client,
    vehicle_code,
    category,
    amount,
    reference,
):
    payload = {
        "vehicle_code": vehicle_code or None,
        "category": category,
        "amount": float(amount),
        "reference": reference,
    }
    return client.table("transport_finance_entries").insert(payload).execute().data
