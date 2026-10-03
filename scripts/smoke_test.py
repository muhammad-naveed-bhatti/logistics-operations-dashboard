from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo_data import build_demo_data, build_role_demo_data


def main():
    fleet, inventory, dispatch = build_demo_data()
    gate_passes, gate_movements, maintenance, finance = build_role_demo_data()

    required_fleet = {
        "id", "truck_id", "driver", "status", "lat", "lon",
        "destination", "cargo", "priority", "eta", "last_update"
    }
    required_inventory = {
        "item_code", "item_name", "category", "stock_qty",
        "reorder_level", "location", "condition", "updated_at"
    }
    required_dispatch = {"fleet_id", "event_type", "details", "event_time"}

    assert required_fleet.issubset(fleet.columns)
    assert required_inventory.issubset(inventory.columns)
    assert required_dispatch.issubset(dispatch.columns)
    assert fleet["truck_id"].is_unique
    assert inventory["item_code"].is_unique
    assert len(fleet) >= 8
    assert len(inventory) >= 10
    assert len(dispatch) >= 4
    assert (fleet["status"] == "Delayed").any()
    assert (inventory["stock_qty"] <= inventory["reorder_level"]).any()

    assert {"pass_no", "fleet_id", "driver", "status"}.issubset(gate_passes.columns)
    assert gate_passes["pass_no"].is_unique
    assert {"movement", "gate", "event_time"}.issubset(gate_movements.columns)
    assert {"job_no", "fleet_id", "status", "priority"}.issubset(maintenance.columns)
    assert maintenance["job_no"].is_unique
    assert {"entry_no", "category", "amount", "entry_time"}.issubset(finance.columns)
    assert finance["entry_no"].is_unique
    assert (finance["amount"] >= 0).all()

    print("Core and role-specific demo data smoke tests passed.")


if __name__ == "__main__":
    main()
