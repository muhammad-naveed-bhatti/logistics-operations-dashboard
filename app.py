import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Logistics Operations Dashboard", layout="wide")

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=10)
def load_fleet():
    response = (
        get_supabase()
        .table("fleet_data")
        .select("*")
        .order("last_update", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)

@st.cache_data(ttl=10)
def load_inventory():
    response = (
        get_supabase()
        .table("inventory_items")
        .select("*")
        .order("item_name")
        .execute()
    )
    return pd.DataFrame(response.data)

st.title("Logistics Operations Dashboard")
st.caption("Fleet, dispatch and inventory visibility for a logistics / materials portfolio project.")

fleet = load_fleet()
inventory = load_inventory()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fleet Units", len(fleet))
c2.metric("In Transit", int((fleet.get("status") == "In Transit").sum()) if not fleet.empty else 0)
c3.metric("Delayed", int((fleet.get("status") == "Delayed").sum()) if not fleet.empty else 0)

if inventory.empty:
    low_stock = 0
else:
    low_stock = int((inventory["stock_qty"] <= inventory["reorder_level"]).sum())
c4.metric("Low Stock Items", low_stock)

st.subheader("Fleet Status")
if fleet.empty:
    st.info("No fleet records yet.")
else:
    statuses = ["All"] + sorted(fleet["status"].dropna().unique().tolist())
    selected = st.selectbox("Filter by status", statuses)
    filtered = fleet if selected == "All" else fleet[fleet["status"] == selected]

    map_rows = filtered.dropna(subset=["lat", "lon"])
    if not map_rows.empty:
        st.map(map_rows.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

    st.dataframe(
        filtered[["truck_id", "driver", "status", "destination", "cargo", "priority", "eta", "last_update"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Inventory / Materials")
if inventory.empty:
    st.info("No inventory records yet.")
else:
    inv = inventory.copy()
    inv["reorder_flag"] = inv["stock_qty"] <= inv["reorder_level"]
    st.dataframe(
        inv[["item_code", "item_name", "category", "stock_qty", "reorder_level", "location", "condition", "reorder_flag"]],
        use_container_width=True,
        hide_index=True,
    )
