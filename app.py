import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Logistics Operations Dashboard", page_icon="📦", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(128,128,128,.08); border: 1px solid rgba(128,128,128,.20); padding: 14px; border-radius: 14px;}
.small-note {opacity:.75;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=10)
def load_table(name, order_col=None):
    q = get_supabase().table(name).select("*")
    if order_col:
        q = q.order(order_col, desc=True)
    return pd.DataFrame(q.execute().data)


def status_badge(value):
    icons = {"In Transit":"🚚","Delayed":"⚠️","Loading":"📥","Unloading":"📤","Available":"✅","Maintenance":"🛠️"}
    return f"{icons.get(value,'•')} {value}"

st.title("Logistics Operations Dashboard")
st.caption("Fleet • Dispatch • Materials • Aviation / Technical Spares")

try:
    fleet = load_table("fleet_data", "last_update")
    inventory = load_table("inventory_items", "updated_at")
    dispatch = load_table("dispatch_log", "event_time")
except Exception as exc:
    st.error("Supabase connection is not configured yet. Add project URL + publishable key to Streamlit secrets after the database is created.")
    st.code(str(exc))
    st.stop()

st.sidebar.header("Operational Filters")
status_options = ["All"] + sorted(fleet["status"].dropna().unique().tolist()) if not fleet.empty else ["All"]
priority_options = ["All"] + sorted(fleet["priority"].dropna().unique().tolist()) if not fleet.empty else ["All"]
selected_status = st.sidebar.selectbox("Fleet status", status_options)
selected_priority = st.sidebar.selectbox("Priority", priority_options)
search = st.sidebar.text_input("Search cargo / destination / driver")

filtered = fleet.copy()
if not filtered.empty:
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"] == selected_priority]
    if search:
        mask = filtered[["driver","destination","cargo","truck_id"]].fillna("").astype(str).apply(lambda c: c.str.contains(search, case=False)).any(axis=1)
        filtered = filtered[mask]

fleet_count = len(fleet)
in_transit = int((fleet["status"] == "In Transit").sum()) if not fleet.empty else 0
delayed = int((fleet["status"] == "Delayed").sum()) if not fleet.empty else 0
critical = int((fleet["priority"] == "Critical").sum()) if not fleet.empty else 0
low_stock = int((inventory["stock_qty"] <= inventory["reorder_level"]).sum()) if not inventory.empty else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Fleet Units", fleet_count)
c2.metric("In Transit", in_transit)
c3.metric("Delayed", delayed)
c4.metric("Critical Loads", critical)
c5.metric("Low Stock", low_stock)

if delayed or low_stock:
    st.warning(f"Attention required: {delayed} delayed vehicle(s) and {low_stock} item(s) at/below reorder level.")
else:
    st.success("No current delay or reorder exceptions.")

overview_tab, fleet_tab, materials_tab, dispatch_tab = st.tabs(["Overview","Fleet & Map","Materials","Dispatch Log"])

with overview_tab:
    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Fleet Status Mix")
        if fleet.empty:
            st.info("No fleet data available.")
        else:
            status_counts = fleet["status"].value_counts().rename_axis("status").reset_index(name="units")
            st.bar_chart(status_counts.set_index("status"))
    with right:
        st.subheader("Inventory by Category")
        if inventory.empty:
            st.info("No inventory data available.")
        else:
            category_stock = inventory.groupby("category", as_index=False)["stock_qty"].sum().sort_values("stock_qty", ascending=False)
            st.bar_chart(category_stock.set_index("category"))

    st.subheader("Exception Board")
    exceptions = []
    if not fleet.empty:
        for _, r in fleet[fleet["status"].eq("Delayed") | fleet["priority"].eq("Critical")].iterrows():
            exceptions.append({"Type":"Fleet","Reference":r["truck_id"],"Issue":status_badge(r["status"]),"Detail":r.get("cargo"),"Location":r.get("destination")})
    if not inventory.empty:
        for _, r in inventory[inventory["stock_qty"] <= inventory["reorder_level"]].iterrows():
            exceptions.append({"Type":"Inventory","Reference":r["item_code"],"Issue":"🔻 Reorder","Detail":r["item_name"],"Location":r.get("location")})
    if exceptions:
        st.dataframe(pd.DataFrame(exceptions), use_container_width=True, hide_index=True)
    else:
        st.success("No operational exceptions.")

with fleet_tab:
    st.subheader("Fleet Movement Map")
    if filtered.empty:
        st.info("No fleet rows match the selected filters.")
    else:
        map_rows = filtered.dropna(subset=["lat", "lon"])
        if not map_rows.empty:
            st.map(map_rows.rename(columns={"lat":"latitude","lon":"longitude"})[["latitude","longitude"]])
        table = filtered.copy()
        table["status"] = table["status"].map(status_badge)
        st.dataframe(table[["truck_id","driver","status","priority","destination","cargo","eta","last_update"]], use_container_width=True, hide_index=True)

with materials_tab:
    st.subheader("Materials & Aviation Spares")
    if inventory.empty:
        st.info("No inventory records yet.")
    else:
        inv = inventory.copy()
        inv["reorder_status"] = inv.apply(lambda r: "🔴 Reorder" if r["stock_qty"] <= r["reorder_level"] else "🟢 OK", axis=1)
        category = st.selectbox("Category", ["All"] + sorted(inv["category"].dropna().unique().tolist()))
        if category != "All":
            inv = inv[inv["category"] == category]
        st.dataframe(inv[["item_code","item_name","category","stock_qty","reorder_level","reorder_status","location","condition"]], use_container_width=True, hide_index=True)

with dispatch_tab:
    st.subheader("Recent Dispatch Events")
    if dispatch.empty:
        st.info("No dispatch events yet.")
    else:
        display = dispatch.merge(fleet[["id","truck_id"]], left_on="fleet_id", right_on="id", how="left", suffixes=("","_fleet")) if not fleet.empty else dispatch
        cols = [c for c in ["event_time","truck_id","event_type","details"] if c in display.columns]
        st.dataframe(display[cols], use_container_width=True, hide_index=True)

st.markdown('<p class="small-note">Portfolio demo: Python + Streamlit + Supabase. Public view is read-only; operational writes should use authenticated access.</p>', unsafe_allow_html=True)
