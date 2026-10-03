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


def format_utc(series):
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.dt.strftime("%d %b %Y %H:%M UTC").fillna("—")


def event_badge(value):
    icons = {
        "DISPATCHED": "🚚 Dispatched",
        "DELAY_ALERT": "⚠️ Delay Alert",
        "LOADING": "📥 Loading",
        "ARRIVED": "✅ Arrived",
    }
    return icons.get(value, value.replace("_", " ").title())


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
st.markdown(
    '<p class="small-note">Portfolio demonstration using fictional operational data.</p>',
    unsafe_allow_html=True,
)

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
        status_counts = (
            fleet["status"]
            .value_counts()
            .rename_axis("status")
            .reset_index(name="units")
        )
        st.bar_chart(
            status_counts,
            x="status",
            y="units",
            horizontal=True,
            sort="-units",
            height=300,
        )

    with right:
        st.markdown("#### Inventory by Category")
        category_stock = (
            inventory.groupby("category", as_index=False)["stock_qty"]
            .sum()
            .sort_values("stock_qty", ascending=False)
        )
        st.bar_chart(
            category_stock,
            x="category",
            y="stock_qty",
            horizontal=True,
            sort="-stock_qty",
            height=360,
        )

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
                "Recommended Action": (
                    "Review ETA / route and escalate delay"
                    if row["status"] == "Delayed"
                    else "Monitor priority movement to handover"
                ),
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
                "Recommended Action": "Raise replenishment / expedite supply",
            }
        )

    if exceptions:
        st.dataframe(
            pd.DataFrame(exceptions),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Reference": st.column_config.TextColumn("Reference", width="small"),
                "Issue": st.column_config.TextColumn("Issue", width="medium"),
                "Detail": st.column_config.TextColumn("Detail", width="medium"),
                "Location": st.column_config.TextColumn("Location", width="medium"),
                "Recommended Action": st.column_config.TextColumn(
                    "Recommended Action",
                    width="large",
                ),
            },
        )
    else:
        st.success("No operational exceptions.")

with fleet_tab:
    st.subheader("Fleet Movement Map")
    if filtered.empty:
        st.info("No fleet rows match the selected filters.")
    else:
        map_rows = filtered.dropna(subset=["lat", "lon"]).copy()
        if not map_rows.empty:
            map_rows["map_color"] = map_rows.apply(
                lambda row: (
                    "#D32F2F"
                    if row["status"] == "Delayed" or row["priority"] == "Critical"
                    else "#1976D2"
                ),
                axis=1,
            )
            st.map(
                map_rows,
                latitude="lat",
                longitude="lon",
                color="map_color",
                size=18000,
                zoom=4,
                height=430,
            )
            st.caption(
                "Map emphasis: red points require higher attention; blue points are routine monitored movements."
            )

        table = filtered.copy()
        table["status"] = table["status"].map(status_badge)
        table["eta"] = format_utc(table["eta"])
        table["last_update"] = format_utc(table["last_update"])
        table = table.rename(
            columns={
                "truck_id": "Fleet ID",
                "driver": "Driver",
                "status": "Status",
                "priority": "Priority",
                "destination": "Destination",
                "cargo": "Cargo",
                "eta": "ETA (UTC)",
                "last_update": "Last Update (UTC)",
            }
        )
        st.dataframe(
            table[
                [
                    "Fleet ID",
                    "Driver",
                    "Status",
                    "Priority",
                    "Destination",
                    "Cargo",
                    "ETA (UTC)",
                    "Last Update (UTC)",
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

    serviceable = int((inventory["condition"] == "Serviceable").sum())
    calibration_due = int(
        inventory["condition"].astype(str).str.contains("Calibration Due", case=False).sum()
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tracked Lines", len(inventory))
    m2.metric("Reorder Required", low_stock)
    m3.metric("Serviceable", serviceable)
    m4.metric("Calibration Due", calibration_due)

    inventory_view = inventory.copy()
    inventory_view["stock_gap"] = (
        inventory_view["stock_qty"] - inventory_view["reorder_level"]
    )
    inventory_view["reorder_status"] = inventory_view.apply(
        lambda row: "🔴 Reorder"
        if row["stock_qty"] <= row["reorder_level"]
        else "🟢 OK",
        axis=1,
    )

    low_stock_view = inventory_view[
        inventory_view["stock_qty"] <= inventory_view["reorder_level"]
    ].copy()

    left_materials, right_materials = st.columns([1.2, 1])
    with left_materials:
        category = st.selectbox(
            "Category",
            ["All"] + sorted(inventory_view["category"].dropna().unique().tolist()),
        )
    with right_materials:
        if not low_stock_view.empty:
            st.warning(
                f"{len(low_stock_view)} material line(s) need replenishment attention."
            )
        else:
            st.success("No material line is at or below reorder level.")

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
                "stock_gap",
                "reorder_status",
                "location",
                "condition",
            ]
        ].rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Item",
                "category": "Category",
                "stock_qty": "Stock",
                "reorder_level": "Reorder Level",
                "stock_gap": "Stock Gap",
                "reorder_status": "Status",
                "location": "Location",
                "condition": "Condition",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    if not low_stock_view.empty:
        st.markdown("#### Reorder Watchlist")
        st.dataframe(
            low_stock_view[
                ["item_code", "item_name", "stock_qty", "reorder_level", "location"]
            ].rename(
                columns={
                    "item_code": "Item Code",
                    "item_name": "Item",
                    "stock_qty": "Stock",
                    "reorder_level": "Reorder Level",
                    "location": "Location",
                }
            ),
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

    if not display.empty:
        dispatch_alerts = int((display["event_type"] == "DELAY_ALERT").sum())
        dispatch_arrivals = int((display["event_type"] == "ARRIVED").sum())
        dispatch_starts = int(
            display["event_type"].isin(["DISPATCHED", "LOADING"]).sum()
        )

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Logged Events", len(display))
        d2.metric("Delay Alerts", dispatch_alerts)
        d3.metric("Movement Starts", dispatch_starts)
        d4.metric("Arrivals", dispatch_arrivals)

        display = display.copy()
        display["event_time"] = pd.to_datetime(
            display["event_time"], errors="coerce", utc=True
        )
        display = display.sort_values("event_time", ascending=False)
        display["event_time"] = format_utc(display["event_time"])
        display["event_type"] = display["event_type"].map(event_badge)

    cols = [
        column
        for column in ["event_time", "truck_id", "event_type", "details"]
        if column in display.columns
    ]
    dispatch_view = display[cols].rename(
        columns={
            "event_time": "Event Time (UTC)",
            "truck_id": "Fleet ID",
            "event_type": "Event",
            "details": "Operational Detail",
        }
    )
    st.dataframe(dispatch_view, use_container_width=True, hide_index=True)

    st.download_button(
        "Download dispatch log CSV",
        csv_bytes(dispatch_view),
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

    st.markdown("#### Priority Actions")
    action_items = []

    for _, row in fleet[fleet["status"] == "Delayed"].iterrows():
        action_items.append(
            f"**{row['truck_id']}** — review ETA/route and escalate the delay for {row['cargo']}."
        )

    for _, row in inventory[
        inventory["stock_qty"] <= inventory["reorder_level"]
    ].iterrows():
        action_items.append(
            f"**{row['item_code']}** — replenish {row['item_name']} "
            f"(stock {row['stock_qty']}, reorder level {row['reorder_level']})."
        )

    for _, row in fleet[fleet["status"] == "Maintenance"].iterrows():
        action_items.append(
            f"**{row['truck_id']}** — track maintenance completion before returning the unit to availability."
        )

    if action_items:
        st.markdown("\n".join(f"- {item}" for item in action_items))
    else:
        st.success("No immediate management action is required.")

    st.markdown("#### Demonstrated Capabilities")
    cap_left, cap_right = st.columns(2)
    with cap_left:
        st.markdown(
            """
- Fleet and dispatch visibility
- Status / priority filtering
- Delay and critical-load control
- Geographic fleet visualization
            """
        )
    with cap_right:
        st.markdown(
            """
- Inventory reorder monitoring
- Technical / aviation spares visibility
- Management KPIs and briefing
- Downloadable operational snapshots
            """
        )

    st.caption(
        "Architecture note: the portfolio demo is self-contained and can optionally use Supabase as its live data layer."
    )

generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<p class="small-note">Portfolio demo • Data source: {data_source} • '
    f'Generated: {generated_at} • Python + Streamlit + Supabase-ready architecture.</p>',
    unsafe_allow_html=True,
)
