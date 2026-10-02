from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from demo_data import build_demo_data

st.set_page_config(
    page_title="Logistics Operations Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: rgba(128,128,128,.08);
    border: 1px solid rgba(128,128,128,.20);
    padding: 14px;
    border-radius: 14px;
}
.small-note {opacity:.72;font-size:.86rem;}
.section-note {opacity:.80;font-size:.93rem;margin-top:-.35rem;}
</style>
""", unsafe_allow_html=True)


def has_supabase_config():
    try:
        return bool(st.secrets.get("SUPABASE_URL")) and bool(st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False


@st.cache_resource
def get_supabase():
    from supabase import create_client

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


@st.cache_data(ttl=10)
def load_table(name, order_col=None):
    query = get_supabase().table(name).select("*")
    if order_col:
        query = query.order(order_col, desc=True)
    return pd.DataFrame(query.execute().data)


def load_data():
    if has_supabase_config():
        try:
            return (
                load_table("fleet_data", "last_update"),
                load_table("inventory_items", "updated_at"),
                load_table("dispatch_log", "event_time"),
                "Live Supabase",
            )
        except Exception:
            pass

    fleet, inventory, dispatch = build_demo_data()
    return fleet, inventory, dispatch, "Demo dataset"


def status_badge(value):
    icons = {
        "In Transit": "🚚",
        "Delayed": "⚠️",
        "Loading": "📥",
        "Unloading": "📤",
        "Available": "✅",
        "Maintenance": "🛠️",
    }
    return f"{icons.get(value, '•')} {value}"


def pct(numerator, denominator):
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


fleet, inventory, dispatch, data_source = load_data()

fleet_count = len(fleet)
maintenance = int((fleet["status"] == "Maintenance").sum()) if not fleet.empty else 0
delayed = int((fleet["status"] == "Delayed").sum()) if not fleet.empty else 0
in_transit = int((fleet["status"] == "In Transit").sum()) if not fleet.empty else 0
critical = int((fleet["priority"] == "Critical").sum()) if not fleet.empty else 0
active_movements = int(fleet["status"].isin(["In Transit", "Loading", "Unloading", "Delayed"]).sum()) if not fleet.empty else 0
low_stock = int((inventory["stock_qty"] <= inventory["reorder_level"]).sum()) if not inventory.empty else 0

operational_units = max(fleet_count - maintenance, 0)
operational_readiness = pct(operational_units, fleet_count)
schedule_health = pct(max(active_movements - delayed, 0), active_movements)
stock_ready_items = max(len(inventory) - low_stock, 0)
stock_readiness = pct(stock_ready_items, len(inventory))
attention_items = delayed + low_stock

st.title("Logistics Operations Dashboard")
st.caption("Fleet • Dispatch • Materials • Aviation / Technical Spares")

with st.sidebar:
    st.caption(f"Data source: **{data_source}**")
    if st.button("Refresh dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.header("Operational Filters")
    status_options = ["All"] + sorted(fleet["status"].dropna().unique().tolist()) if not fleet.empty else ["All"]
    priority_options = ["All"] + sorted(fleet["priority"].dropna().unique().tolist()) if not fleet.empty else ["All"]
    selected_status = st.selectbox("Fleet status", status_options)
    selected_priority = st.selectbox("Priority", priority_options)
    search = st.text_input("Search cargo / destination / driver")

    st.divider()
    st.subheader("Portfolio Demo")
    st.caption(
        "Self-contained demo mode works without a database. "
        "The same interface is Supabase-ready for a live backend."
    )

filtered = fleet.copy()
if not filtered.empty:
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"] == selected_priority]
    if search:
        mask = (
            filtered[["driver", "destination", "cargo", "truck_id"]]
            .fillna("")
            .astype(str)
            .apply(lambda column: column.str.contains(search, case=False))
            .any(axis=1)
        )
        filtered = filtered[mask]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Operational Readiness", f"{operational_readiness}%")
k2.metric("Schedule Health", f"{schedule_health}%")
k3.metric("Stock Readiness", f"{stock_readiness}%")
k4.metric("Active Movements", active_movements)
k5.metric("Attention Items", attention_items)

if attention_items:
    st.warning(
        f"Control desk attention: {delayed} delayed vehicle(s), "
        f"{low_stock} item(s) at/below reorder level, and "
        f"{critical} critical-priority load(s)."
    )
else:
    st.success("Operations are within the current demo thresholds.")

overview_tab, fleet_tab, materials_tab, dispatch_tab, brief_tab = st.tabs(
    ["Executive Overview", "Fleet & Map", "Materials", "Dispatch Log", "Management Brief"]
)

with overview_tab:
    st.subheader("Operational Snapshot")
    st.markdown(
        '<p class="section-note">A compact control-room view of fleet readiness, schedule risk and stock availability.</p>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Fleet Status Mix")
        status_counts = fleet["status"].value_counts().rename_axis("status").reset_index(name="units")
        st.bar_chart(status_counts.set_index("status"))

    with right:
        st.markdown("#### Inventory by Category")
        category_stock = (
            inventory.groupby("category", as_index=False)["stock_qty"]
            .sum()
            .sort_values("stock_qty", ascending=False)
        )
        st.bar_chart(category_stock.set_index("category"))

    st.markdown("#### Exception Board")
    exceptions = []

    for _, row in fleet[
        fleet["status"].eq("Delayed") | fleet["priority"].eq("Critical")
    ].iterrows():
        exceptions.append(
            {
                "Type": "Fleet",
                "Reference": row["truck_id"],
                "Issue": status_badge(row["status"]),
                "Priority": row["priority"],
                "Detail": row["cargo"],
                "Location": row["destination"],
            }
        )

    for _, row in inventory[
        inventory["stock_qty"] <= inventory["reorder_level"]
    ].iterrows():
        exceptions.append(
            {
                "Type": "Inventory",
                "Reference": row["item_code"],
                "Issue": "🔻 Reorder",
                "Priority": "Stock",
                "Detail": row["item_name"],
                "Location": row["location"],
            }
        )

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
            st.map(
                map_rows.rename(columns={"lat": "latitude", "lon": "longitude"})[
                    ["latitude", "longitude"]
                ]
            )

        table = filtered.copy()
        table["status"] = table["status"].map(status_badge)
        st.dataframe(
            table[
                [
                    "truck_id",
                    "driver",
                    "status",
                    "priority",
                    "destination",
                    "cargo",
                    "eta",
                    "last_update",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download filtered fleet CSV",
            csv_bytes(filtered),
            file_name="fleet_snapshot.csv",
            mime="text/csv",
        )

with materials_tab:
    st.subheader("Materials & Aviation Spares")
    inventory_view = inventory.copy()
    inventory_view["reorder_status"] = inventory_view.apply(
        lambda row: "🔴 Reorder"
        if row["stock_qty"] <= row["reorder_level"]
        else "🟢 OK",
        axis=1,
    )

    category = st.selectbox(
        "Category",
        ["All"] + sorted(inventory_view["category"].dropna().unique().tolist()),
    )
    if category != "All":
        inventory_view = inventory_view[inventory_view["category"] == category]

    st.dataframe(
        inventory_view[
            [
                "item_code",
                "item_name",
                "category",
                "stock_qty",
                "reorder_level",
                "reorder_status",
                "location",
                "condition",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download materials CSV",
        csv_bytes(inventory_view),
        file_name="materials_snapshot.csv",
        mime="text/csv",
    )

with dispatch_tab:
    st.subheader("Recent Dispatch Events")
    display = (
        dispatch.merge(
            fleet[["id", "truck_id"]],
            left_on="fleet_id",
            right_on="id",
            how="left",
        )
        if not dispatch.empty
        else dispatch
    )

    cols = [
        column
        for column in ["event_time", "truck_id", "event_type", "details"]
        if column in display.columns
    ]
    st.dataframe(display[cols], use_container_width=True, hide_index=True)

    st.download_button(
        "Download dispatch log CSV",
        csv_bytes(display[cols]),
        file_name="dispatch_log.csv",
        mime="text/csv",
    )

with brief_tab:
    st.subheader("Management Brief")
    st.info(
        f"Fleet operational readiness is {operational_readiness}%. "
        f"{active_movements} unit(s) are engaged in active movements, "
        f"with {delayed} recorded delay(s)."
    )
    st.info(
        f"Inventory readiness is {stock_readiness}%. "
        f"{low_stock} of {len(inventory)} tracked material line(s) are "
        "at or below their reorder threshold."
    )

    if critical:
        st.warning(
            f"{critical} critical-priority shipment(s) require close monitoring "
            "until delivery or handover."
        )

    if maintenance:
        st.warning(
            f"{maintenance} fleet unit(s) are under maintenance and are excluded "
            "from operational availability."
        )

    st.markdown("#### Demonstrated Capabilities")
    st.markdown(
        """
- Fleet and dispatch visibility with status/priority filtering
- Exception-based control for delay and critical loads
- Inventory reorder monitoring for technical and aviation-related materials
- Geographic fleet visualization
- Management KPIs and operational briefing
- Downloadable operational snapshots
- Optional Supabase data layer with a zero-cost built-in demo fallback
        """
    )

generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<p class="small-note">Portfolio demo • Data source: {data_source} • '
    f'Generated: {generated_at} • Python + Streamlit + Supabase-ready architecture.</p>',
    unsafe_allow_html=True,
)
