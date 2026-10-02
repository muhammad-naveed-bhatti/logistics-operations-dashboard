from demo_data import build_demo_data


def main():
    fleet, inventory, dispatch = build_demo_data()

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

    print("Demo data smoke test passed.")


if __name__ == "__main__":
    main()
