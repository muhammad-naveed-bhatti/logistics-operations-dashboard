from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from auth_layer import (
    authenticated_client,
    current_auth,
    enter_demo,
    set_demo_role,
    sign_in,
    sign_out,
    supabase_configured,
)
from demo_data import build_demo_data, build_role_demo_data
from rbac import ROLE_CONFIG, has_permission, role_description, role_panels

st.set_page_config(
    page_title="Role-Based Logistics Operations System",
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
.role-chip {
    display:inline-block;
    padding:.28rem .65rem;
    border:1px solid rgba(128,128,128,.28);
    border-radius:999px;
    font-size:.85rem;
    margin:.1rem 0 .55rem 0;
}
</style>
""", unsafe_allow_html=True)


def load_authenticated_table(client, name, order_col=None):
    query = client.table(name).select("*")
    if order_col:
        query = query.order(order_col, desc=True)
    return pd.DataFrame(query.execute().data)


def load_data():
    auth = current_auth()
    if auth and auth.get("mode") == "authenticated":
        client = authenticated_client()
        if client is not None:
            try:
                return (
                    load_authenticated_table(client, "fleet_data", "last_update"),
                    load_authenticated_table(client, "inventory_items", "updated_at"),
                    load_authenticated_table(client, "dispatch_log", "event_time"),
                    "Authenticated Supabase / RLS",
                )
            except Exception as exc:
                st.warning(
                    "Authenticated session is active, but live operational tables are not "
                    "available yet. Showing fictional portfolio data until the backend migration "
                    "is deployed."
                )
                st.caption(str(exc))

    fleet, inventory, dispatch = build_demo_data()
    return fleet, inventory, dispatch, "Demo dataset"


def render_login():
    st.title("Logistics Operations Management System")
    st.caption("Secure role-based access • Fleet • Finance • Maintenance • Gate Control")

    secure_tab, demo_tab = st.tabs(["Secure Login", "Portfolio Demo"])

    with secure_tab:
        if not supabase_configured():
            st.info(
                "Secure login is code-ready. Connect the dedicated Supabase project in "
                "Streamlit secrets to activate email/password authentication."
            )
        else:
            with st.form("secure_login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", use_container_width=True)

            if submitted:
                try:
                    sign_in(email.strip(), password)
                    st.success("Signed in successfully.")
                    st.rerun()
                except PermissionError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Login failed. Check the email/password and try again.")

        st.caption(
            "Production roles are assigned by the system administrator and are not "
            "selectable by authenticated users."
        )

    with demo_tab:
        st.write(
            "Recruiters and portfolio visitors can explore the fictional demo without "
            "creating an account."
        )
        if st.button("Enter Portfolio Demo", use_container_width=True):
            enter_demo("Senior Officers")
            st.rerun()


if current_auth() is None:
    render_login()
    st.stop()


def initialise_role_demo_state():
    if "gate_passes" not in st.session_state:
        passes, movements, maintenance, finance = build_role_demo_data()
        st.session_state.gate_passes = passes.to_dict("records")
        st.session_state.gate_movements = movements.to_dict("records")
        st.session_state.maintenance_records = maintenance.to_dict("records")
        st.session_state.finance_entries = finance.to_dict("records")


def format_utc(series):
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.dt.strftime("%d %b %Y %H:%M UTC").fillna("—")


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


def event_badge(value):
    icons = {
        "DISPATCHED": "🚚 Dispatched",
        "DELAY_ALERT": "⚠️ Delay Alert",
        "LOADING": "📥 Loading",
        "ARRIVED": "✅ Arrived",
    }
    return icons.get(value, str(value).replace("_", " ").title())


def pct(numerator, denominator):
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


fleet, inventory, dispatch, data_source = load_data()
initialise_role_demo_state()
auth_context = current_auth()
auth_mode = auth_context.get("mode")
selected_role = auth_context.get("role_name")

gate_passes = pd.DataFrame(st.session_state.gate_passes)
gate_movements = pd.DataFrame(st.session_state.gate_movements)
maintenance_records = pd.DataFrame(st.session_state.maintenance_records)
finance_entries = pd.DataFrame(st.session_state.finance_entries)

fleet_count = len(fleet)
maintenance_count = int((fleet["status"] == "Maintenance").sum()) if not fleet.empty else 0
delayed = int((fleet["status"] == "Delayed").sum()) if not fleet.empty else 0
critical = int((fleet["priority"] == "Critical").sum()) if not fleet.empty else 0
active_movements = int(
    fleet["status"].isin(["In Transit", "Loading", "Unloading", "Delayed"]).sum()
) if not fleet.empty else 0
low_stock = int(
    (inventory["stock_qty"] <= inventory["reorder_level"]).sum()
) if not inventory.empty else 0

operational_units = max(fleet_count - maintenance_count, 0)
operational_readiness = pct(operational_units, fleet_count)
schedule_health = pct(max(active_movements - delayed, 0), active_movements)
stock_readiness = pct(max(len(inventory) - low_stock, 0), len(inventory))
attention_items = delayed + low_stock

with st.sidebar:
    st.header("Access")
    if auth_mode == "authenticated":
        st.success("Authenticated")
        st.caption(auth_context.get("email") or "Signed-in user")
        st.write(f"**Role:** {selected_role}")
    else:
        st.caption("Portfolio demo mode")
        demo_role = st.selectbox(
            "Demo role",
            list(ROLE_CONFIG.keys()),
            index=list(ROLE_CONFIG.keys()).index(selected_role),
            help="Demo only. Authenticated users cannot choose their own role.",
        )
        if demo_role != selected_role:
            set_demo_role(demo_role)
            selected_role = demo_role

    st.caption(role_description(selected_role))
    selected_panel = st.radio("Workspace", role_panels(selected_role))

    st.divider()
    st.caption(f"Data source: **{data_source}**")
    if st.button("Refresh dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("Sign out / Exit demo", use_container_width=True):
        sign_out()
        st.rerun()

    with st.expander("Access restrictions"):
        for permission in sorted(ROLE_CONFIG[selected_role]["permissions"]):
            st.write("✓", permission.replace("_", " ").title())
        if auth_mode == "authenticated":
            st.caption("Role is assigned server-side and cannot be changed from this UI.")
        else:
            st.caption("Demo role switching is enabled only for portfolio exploration.")

st.title("Logistics Operations Management System")
st.caption("Role-based Fleet • Dispatch • Materials • Finance • Maintenance • Gate Control")
st.markdown(
    f'<span class="role-chip">Current role: {selected_role}</span>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="small-note">Portfolio demonstration using fictional operational data. '
    'Authenticated users receive their role from the identity system; demo visitors may switch roles.</p>',
    unsafe_allow_html=True,
)


def render_executive_overview():
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

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Fleet Status Mix")
        status_counts = (
            fleet["status"].value_counts().rename_axis("status").reset_index(name="units")
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
        exceptions.append({
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
        })
    for _, row in inventory[
        inventory["stock_qty"] <= inventory["reorder_level"]
    ].iterrows():
        exceptions.append({
            "Type": "Inventory",
            "Reference": row["item_code"],
            "Issue": "🔻 Reorder",
            "Priority": "Stock",
            "Detail": row["item_name"],
            "Location": row["location"],
            "Recommended Action": "Raise replenishment / expedite supply",
        })
    st.dataframe(pd.DataFrame(exceptions), use_container_width=True, hide_index=True)


def render_fleet():
    st.subheader("Fleet & Movement Control")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        selected_status = st.selectbox(
            "Fleet status",
            ["All"] + sorted(fleet["status"].dropna().unique().tolist()),
            key="fleet_status_filter",
        )
    with f2:
        selected_priority = st.selectbox(
            "Priority",
            ["All"] + sorted(fleet["priority"].dropna().unique().tolist()),
            key="fleet_priority_filter",
        )
    with f3:
        search = st.text_input(
            "Search vehicle / driver / cargo / destination",
            key="fleet_search",
        )

    filtered = fleet.copy()
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"] == selected_priority]
    if search:
        mask = (
            filtered[["driver", "destination", "cargo", "truck_id"]]
            .fillna("")
            .astype(str)
            .apply(lambda col: col.str.contains(search, case=False))
            .any(axis=1)
        )
        filtered = filtered[mask]

    if filtered.empty:
        st.info("No fleet rows match the selected filters.")
        return

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

    table = filtered.copy()
    table["status"] = table["status"].map(status_badge)
    table["eta"] = format_utc(table["eta"])
    table["last_update"] = format_utc(table["last_update"])
    st.dataframe(
        table[
            ["truck_id", "driver", "status", "priority", "destination", "cargo", "eta", "last_update"]
        ].rename(columns={
            "truck_id":"Fleet ID",
            "driver":"Driver",
            "status":"Status",
            "priority":"Priority",
            "destination":"Destination",
            "cargo":"Cargo",
            "eta":"ETA (UTC)",
            "last_update":"Last Update (UTC)",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download filtered fleet CSV",
        csv_bytes(filtered),
        file_name="fleet_snapshot.csv",
        mime="text/csv",
    )


def render_materials():
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

    view = inventory.copy()
    view["Stock Gap"] = view["stock_qty"] - view["reorder_level"]
    view["Status"] = view.apply(
        lambda row: "🔴 Reorder" if row["stock_qty"] <= row["reorder_level"] else "🟢 OK",
        axis=1,
    )
    category = st.selectbox(
        "Category",
        ["All"] + sorted(view["category"].dropna().unique().tolist()),
        key="material_category",
    )
    if category != "All":
        view = view[view["category"] == category]

    st.dataframe(
        view[
            ["item_code","item_name","category","stock_qty","reorder_level","Stock Gap","Status","location","condition"]
        ].rename(columns={
            "item_code":"Item Code",
            "item_name":"Item",
            "category":"Category",
            "stock_qty":"Stock",
            "reorder_level":"Reorder Level",
            "location":"Location",
            "condition":"Condition",
        }),
        use_container_width=True,
        hide_index=True,
    )

    reorder = inventory[inventory["stock_qty"] <= inventory["reorder_level"]]
    if not reorder.empty:
        st.markdown("#### Reorder Watchlist")
        st.dataframe(
            reorder[["item_code","item_name","stock_qty","reorder_level","location"]].rename(
                columns={
                    "item_code":"Item Code",
                    "item_name":"Item",
                    "stock_qty":"Stock",
                    "reorder_level":"Reorder Level",
                    "location":"Location",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_dispatch():
    st.subheader("Dispatch Log")
    display = dispatch.merge(
        fleet[["id", "truck_id"]],
        left_on="fleet_id",
        right_on="id",
        how="left",
    )
    display["event_time"] = pd.to_datetime(display["event_time"], errors="coerce", utc=True)
    display = display.sort_values("event_time", ascending=False)
    alerts = int((display["event_type"] == "DELAY_ALERT").sum())
    arrivals = int((display["event_type"] == "ARRIVED").sum())

    d1, d2, d3 = st.columns(3)
    d1.metric("Logged Events", len(display))
    d2.metric("Delay Alerts", alerts)
    d3.metric("Arrivals", arrivals)

    display["event_time"] = format_utc(display["event_time"])
    display["event_type"] = display["event_type"].map(event_badge)
    view = display[["event_time","truck_id","event_type","details"]].rename(columns={
        "event_time":"Event Time (UTC)",
        "truck_id":"Fleet ID",
        "event_type":"Event",
        "details":"Operational Detail",
    })
    st.dataframe(view, use_container_width=True, hide_index=True)


def render_management_brief():
    st.subheader("Management Brief")
    st.info(
        f"Fleet operational readiness is {operational_readiness}%. "
        f"{active_movements} unit(s) are engaged in active movements with {delayed} delay(s)."
    )
    st.info(
        f"Inventory readiness is {stock_readiness}%. "
        f"{low_stock} of {len(inventory)} tracked material line(s) are at/below reorder level."
    )
    st.markdown("#### Priority Actions")
    actions = []
    for _, row in fleet[fleet["status"] == "Delayed"].iterrows():
        actions.append(
            f"**{row['truck_id']}** — review ETA/route and escalate the delay for {row['cargo']}."
        )
    for _, row in inventory[
        inventory["stock_qty"] <= inventory["reorder_level"]
    ].iterrows():
        actions.append(
            f"**{row['item_code']}** — replenish {row['item_name']} "
            f"(stock {row['stock_qty']}, reorder level {row['reorder_level']})."
        )
    for _, row in fleet[fleet["status"] == "Maintenance"].iterrows():
        actions.append(
            f"**{row['truck_id']}** — track maintenance completion before restoring availability."
        )
    st.markdown("\n".join(f"- {item}" for item in actions))


def render_gate_pass_operations(role_name):
    st.subheader("Motor Vehicle Operations — Soft Gate Pass")
    if not has_permission(role_name, "create_gate_pass"):
        st.error("This role is not permitted to generate gate passes.")
        return

    st.caption(
        "Operations issues the soft gate pass. Gate Security validates it and records actual IN/OUT movement."
    )

    with st.form("gate_pass_form"):
        fleet_id = st.selectbox("Vehicle", fleet["truck_id"].tolist())
        vehicle = fleet[fleet["truck_id"] == fleet_id].iloc[0]
        st.text_input("Driver", value=vehicle["driver"], disabled=True)
        destination = st.text_input("Destination", value=str(vehicle["destination"]))
        purpose = st.text_input("Movement purpose / cargo", value=str(vehicle["cargo"]))
        valid_hours = st.number_input("Validity (hours)", min_value=1, max_value=48, value=12)
        submitted = st.form_submit_button("Generate Soft Gate Pass")

    if submitted:
        now = datetime.now(timezone.utc)
        new_no = f"GP-{1001 + len(st.session_state.gate_passes)}"
        st.session_state.gate_passes.append({
            "pass_no": new_no,
            "fleet_id": fleet_id,
            "driver": vehicle["driver"],
            "destination": destination,
            "purpose": purpose,
            "issued_by": "MV Operations Desk",
            "issued_at": now,
            "valid_until": now + timedelta(hours=int(valid_hours)),
            "status": "Issued",
        })
        st.success(f"Soft gate pass {new_no} generated.")
        st.rerun()

    passes = pd.DataFrame(st.session_state.gate_passes)
    passes["issued_at"] = format_utc(passes["issued_at"])
    passes["valid_until"] = format_utc(passes["valid_until"])
    st.dataframe(passes, use_container_width=True, hide_index=True)


def render_driver_panel():
    st.subheader("Fleet Driver Panel")

    if auth_mode == "authenticated":
        driver = auth_context.get("driver_name")
        if not driver:
            st.warning(
                "Driver account is authenticated, but no driver identity mapping is assigned yet."
            )
            return
        st.caption(f"Signed-in driver: **{driver}**")
    else:
        driver = st.selectbox("Demo driver identity", sorted(fleet["driver"].unique()))

    assignment = fleet[fleet["driver"] == driver].copy()
    if assignment.empty:
        st.info("No assignment found.")
        return

    row = assignment.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vehicle", row["truck_id"])
    c2.metric("Status", row["status"])
    c3.metric("Priority", row["priority"])
    c4.metric("Destination", row["destination"])
    st.write("**Cargo / Task:**", row["cargo"])

    passes = pd.DataFrame(st.session_state.gate_passes)
    own_passes = passes[passes["driver"] == driver].copy()
    st.markdown("#### My Soft Gate Pass")
    if own_passes.empty:
        st.info("No active gate pass issued to this driver.")
    else:
        own_passes["issued_at"] = format_utc(own_passes["issued_at"])
        own_passes["valid_until"] = format_utc(own_passes["valid_until"])
        st.dataframe(
            own_passes[
                ["pass_no","fleet_id","destination","purpose","issued_at","valid_until","status"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    st.caption(
        "Driver access is restricted to own assignment and own soft gate-pass visibility. "
        "Authenticated driver identity is server-assigned; only demo mode permits driver switching."
    )


def render_gate_security(role_name):
    st.subheader("Gate Security Panel")
    if not has_permission(role_name, "record_gate_movement"):
        st.error("This role is not permitted to record gate movement.")
        return

    passes = pd.DataFrame(st.session_state.gate_passes)
    active = passes[passes["status"].isin(["Issued", "Vehicle Out"])].copy()
    if active.empty:
        st.info("No active soft gate pass available.")
        return

    selected_pass = st.selectbox("Soft Gate Pass", active["pass_no"].tolist())
    selected = active[active["pass_no"] == selected_pass].iloc[0]

    a, b, c, d = st.columns(4)
    a.metric("Vehicle", selected["fleet_id"])
    b.metric("Driver", selected["driver"])
    c.metric("Status", selected["status"])
    d.metric("Destination", selected["destination"])
    st.write("**Purpose:**", selected["purpose"])
    st.write("**Valid until:**", format_utc(pd.Series([selected["valid_until"]])).iloc[0])

    gate_name = st.selectbox("Gate", ["Main Gate", "Service Gate"])
    remarks = st.text_input("Security remarks", value="Soft gate pass verified.")

    out_disabled = selected["status"] != "Issued"
    in_disabled = selected["status"] != "Vehicle Out"
    left, right = st.columns(2)

    with left:
        if st.button("Record Vehicle OUT", disabled=out_disabled, use_container_width=True):
            now = datetime.now(timezone.utc)
            for record in st.session_state.gate_passes:
                if record["pass_no"] == selected_pass:
                    record["status"] = "Vehicle Out"
            st.session_state.gate_movements.append({
                "pass_no": selected_pass,
                "fleet_id": selected["fleet_id"],
                "driver": selected["driver"],
                "movement": "OUT",
                "gate": gate_name,
                "recorded_by": "Gate Security",
                "event_time": now,
                "remarks": remarks,
            })
            st.success(f"OUT recorded for {selected_pass}.")
            st.rerun()

    with right:
        if st.button("Record Vehicle IN", disabled=in_disabled, use_container_width=True):
            now = datetime.now(timezone.utc)
            for record in st.session_state.gate_passes:
                if record["pass_no"] == selected_pass:
                    record["status"] = "Closed"
            st.session_state.gate_movements.append({
                "pass_no": selected_pass,
                "fleet_id": selected["fleet_id"],
                "driver": selected["driver"],
                "movement": "IN",
                "gate": gate_name,
                "recorded_by": "Gate Security",
                "event_time": now,
                "remarks": remarks,
            })
            st.success(f"IN recorded and gate pass {selected_pass} closed.")
            st.rerun()

    render_gate_movement_summary()


def render_gate_movement_summary():
    st.subheader("Gate Movement Summary")
    movements = pd.DataFrame(st.session_state.gate_movements)
    if movements.empty:
        st.info("No gate movement recorded.")
        return
    movements = movements.copy()
    movements["event_time"] = format_utc(movements["event_time"])
    out_count = int((movements["movement"] == "OUT").sum())
    in_count = int((movements["movement"] == "IN").sum())
    g1, g2, g3 = st.columns(3)
    g1.metric("Movement Records", len(movements))
    g2.metric("OUT Records", out_count)
    g3.metric("IN Records", in_count)
    st.dataframe(movements, use_container_width=True, hide_index=True)


def render_finance(read_only=True):
    title = "Finance Summary" if read_only else "Accountant Panel"
    st.subheader(title)
    finance = pd.DataFrame(st.session_state.finance_entries)
    total = float(finance["amount"].sum())
    fuel = float(finance.loc[finance["category"] == "Fuel", "amount"].sum())
    maint = float(finance.loc[finance["category"] == "Maintenance", "amount"].sum())
    f1, f2, f3 = st.columns(3)
    f1.metric("Recorded Cost", f"PKR {total:,.0f}")
    f2.metric("Fuel Cost", f"PKR {fuel:,.0f}")
    f3.metric("Maintenance Cost", f"PKR {maint:,.0f}")

    by_category = finance.groupby("category", as_index=False)["amount"].sum()
    st.bar_chart(by_category, x="category", y="amount", horizontal=True, height=300)

    if not read_only and has_permission(selected_role, "record_finance"):
        with st.expander("Record finance entry"):
            with st.form("finance_entry_form"):
                fleet_id = st.selectbox(
                    "Vehicle",
                    ["General / Non-vehicle"] + fleet["truck_id"].tolist(),
                    key="finance_vehicle",
                )
                category = st.selectbox(
                    "Cost category",
                    ["Fuel", "Maintenance", "Toll", "Handling", "Other"],
                    key="finance_category",
                )
                amount = st.number_input(
                    "Amount (PKR)",
                    min_value=0.0,
                    step=500.0,
                    key="finance_amount",
                )
                reference = st.text_input(
                    "Reference / narration",
                    key="finance_reference",
                )
                submitted = st.form_submit_button("Record Finance Entry")

            if submitted:
                new_no = f"FN-{len(st.session_state.finance_entries) + 1:03d}"
                st.session_state.finance_entries.append({
                    "entry_no": new_no,
                    "fleet_id": None if fleet_id == "General / Non-vehicle" else fleet_id,
                    "category": category,
                    "amount": float(amount),
                    "reference": reference or "Demo finance entry",
                    "entry_time": datetime.now(timezone.utc),
                })
                st.success(f"{new_no} recorded.")
                st.rerun()

    view = pd.DataFrame(st.session_state.finance_entries).copy()
    view["entry_time"] = format_utc(view["entry_time"])
    st.dataframe(view, use_container_width=True, hide_index=True)


def render_maintenance(role_name, read_only=False):
    title = "Maintenance Overview" if read_only else "Motor Vehicle Maintenance Panel"
    st.subheader(title)
    records = pd.DataFrame(st.session_state.maintenance_records)

    open_jobs = int((records["status"] != "Completed").sum())
    high = int((records["priority"] == "High").sum())
    completed = int((records["status"] == "Completed").sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Open Jobs", open_jobs)
    m2.metric("High Priority", high)
    m3.metric("Completed", completed)

    view = records.copy()
    view["opened_at"] = format_utc(view["opened_at"])
    view["target_completion"] = format_utc(view["target_completion"])
    st.dataframe(view, use_container_width=True, hide_index=True)

    if read_only or not has_permission(role_name, "update_maintenance"):
        return

    st.markdown("#### Update Workshop Job")
    selected_job = st.selectbox("Job", records["job_no"].tolist())
    current = records[records["job_no"] == selected_job].iloc[0]
    new_status = st.selectbox(
        "New status",
        ["Scheduled", "In Progress", "Awaiting Parts", "Completed"],
        index=["Scheduled", "In Progress", "Awaiting Parts", "Completed"].index(current["status"])
        if current["status"] in ["Scheduled", "In Progress", "Awaiting Parts", "Completed"]
        else 0,
    )
    if st.button("Update maintenance status"):
        for record in st.session_state.maintenance_records:
            if record["job_no"] == selected_job:
                record["status"] = new_status
        st.success(f"{selected_job} updated to {new_status}.")
        st.rerun()


PANEL_RENDERERS = {
    "Executive Overview": lambda: render_executive_overview(),
    "Fleet & Map": lambda: render_fleet(),
    "Materials": lambda: render_materials(),
    "Dispatch Log": lambda: render_dispatch(),
    "Management Brief": lambda: render_management_brief(),
    "Gate Pass Operations": lambda: render_gate_pass_operations(selected_role),
    "Driver Panel": lambda: render_driver_panel(),
    "Gate Security Panel": lambda: render_gate_security(selected_role),
    "Gate Movement Summary": lambda: render_gate_movement_summary(),
    "Finance Summary": lambda: render_finance(read_only=True),
    "Accountant Panel": lambda: render_finance(read_only=False),
    "Maintenance Overview": lambda: render_maintenance(selected_role, read_only=True),
    "Maintenance Panel": lambda: render_maintenance(selected_role, read_only=False),
}

PANEL_RENDERERS[selected_panel]()

generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<p class="small-note">Portfolio demo • Role: {selected_role} • Data source: {data_source} • '
    f'Generated: {generated_at} • Access mode: {auth_mode} • '
    f'Authenticated mode is designed for Supabase Auth + RLS enforcement.</p>',
    unsafe_allow_html=True,
)
