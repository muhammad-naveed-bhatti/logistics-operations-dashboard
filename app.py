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
from data_access import (
    create_gate_pass,
    create_maintenance_job,
    fetch_workflow_data,
    record_finance_entry,
    record_gate_movement,
    update_maintenance_status,
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
                st.error("Live operational data could not be loaded for this session.")
                st.caption(str(exc))
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Supabase error"

    fleet, inventory, dispatch = build_demo_data()
    return fleet, inventory, dispatch, "Portfolio demo dataset"


def render_login():
    st.title("Logistics Operations Management System")
    st.caption("Secure role-based access • Fleet • Finance • Maintenance • Gate Control")

    secure_tab, demo_tab = st.tabs(["Secure Login", "Portfolio Demo"])

    with secure_tab:
        if not supabase_configured():
            st.info(
                "Secure login is ready. Add the Supabase URL and publishable key "
                "to Streamlit secrets to activate authenticated access."
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
            "Authenticated roles are assigned by the system and cannot be selected by users."
        )

    with demo_tab:
        st.write(
            "Recruiters and portfolio visitors can explore fictional data without an account."
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


def ensure_columns(frame, columns):
    frame = frame.copy()
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype="object")
    return frame


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


auth_context = current_auth()
auth_mode = auth_context.get("mode")
selected_role = auth_context.get("role_name")
client = authenticated_client() if auth_mode == "authenticated" else None

fleet, inventory, dispatch, data_source = load_data()
initialise_role_demo_state()

if auth_mode == "authenticated" and client is not None:
    try:
        workflow = fetch_workflow_data(client)
        gate_passes = workflow["gate_passes"]
        gate_movements = workflow["gate_movements"]
        maintenance_records = workflow["maintenance"]
        finance_entries = workflow["finance"]
    except Exception as exc:
        st.error("Role-specific live data could not be loaded.")
        st.caption(str(exc))
        gate_passes = pd.DataFrame()
        gate_movements = pd.DataFrame()
        maintenance_records = pd.DataFrame()
        finance_entries = pd.DataFrame()
else:
    gate_passes = pd.DataFrame(st.session_state.gate_passes)
    gate_movements = pd.DataFrame(st.session_state.gate_movements)
    maintenance_records = pd.DataFrame(st.session_state.maintenance_records)
    finance_entries = pd.DataFrame(st.session_state.finance_entries)

fleet = ensure_columns(
    fleet,
    [
        "id", "truck_id", "driver", "driver_user_id", "status", "lat", "lon",
        "destination", "cargo", "priority", "eta", "last_update"
    ],
)
inventory = ensure_columns(
    inventory,
    [
        "item_code", "item_name", "category", "stock_qty", "reorder_level",
        "location", "condition", "updated_at"
    ],
)
dispatch = ensure_columns(
    dispatch, ["fleet_id", "event_type", "details", "event_time"]
)

fleet_count = len(fleet)
maintenance_count = int((fleet["status"] == "Maintenance").sum()) if fleet_count else 0
delayed = int((fleet["status"] == "Delayed").sum()) if fleet_count else 0
critical = int((fleet["priority"] == "Critical").sum()) if fleet_count else 0
active_movements = int(
    fleet["status"].isin(["In Transit", "Loading", "Unloading", "Delayed"]).sum()
) if fleet_count else 0
low_stock = int(
    (pd.to_numeric(inventory["stock_qty"], errors="coerce").fillna(0)
     <= pd.to_numeric(inventory["reorder_level"], errors="coerce").fillna(0)).sum()
) if len(inventory) else 0

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
        if auth_context.get("personnel_id"):
            st.caption(f"Personnel ID: {auth_context['personnel_id']}")
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
            st.caption("Role is server-assigned and database RLS independently enforces access.")
        else:
            st.caption("Role switching is enabled only inside the fictional portfolio demo.")

st.title("Logistics Operations Management System")
st.caption("Role-based Fleet • Dispatch • Materials • Finance • Maintenance • Gate Control")
st.markdown(
    f'<span class="role-chip">Current role: {selected_role}</span>',
    unsafe_allow_html=True,
)
if auth_mode == "authenticated":
    st.markdown(
        '<p class="small-note">Authenticated RLS session. The current backend uses fictional '
        'test data for portfolio/system validation.</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p class="small-note">Portfolio demonstration using fictional operational data.</p>',
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
            status_counts, x="status", y="units",
            horizontal=True, sort="-units", height=300
        )
    with right:
        st.markdown("#### Inventory by Category")
        category_stock = (
            inventory.groupby("category", as_index=False)["stock_qty"]
            .sum()
            .sort_values("stock_qty", ascending=False)
        )
        st.bar_chart(
            category_stock, x="category", y="stock_qty",
            horizontal=True, sort="-stock_qty", height=360
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
        pd.to_numeric(inventory["stock_qty"], errors="coerce").fillna(0)
        <= pd.to_numeric(inventory["reorder_level"], errors="coerce").fillna(0)
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
    if fleet.empty:
        st.info("No fleet rows are available to this role.")
        return

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
            .apply(lambda col: col.str.contains(search, case=False, regex=False))
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
            "truck_id": "Fleet ID",
            "driver": "Driver",
            "status": "Status",
            "priority": "Priority",
            "destination": "Destination",
            "cargo": "Cargo",
            "eta": "ETA (UTC)",
            "last_update": "Last Update (UTC)",
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
    if inventory.empty:
        st.info("No inventory rows are available to this role.")
        return

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
    view["Stock Gap"] = (
        pd.to_numeric(view["stock_qty"], errors="coerce").fillna(0)
        - pd.to_numeric(view["reorder_level"], errors="coerce").fillna(0)
    )
    view["Status"] = view.apply(
        lambda row: "🔴 Reorder"
        if row["stock_qty"] <= row["reorder_level"] else "🟢 OK",
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
            ["item_code", "item_name", "category", "stock_qty", "reorder_level",
             "Stock Gap", "Status", "location", "condition"]
        ].rename(columns={
            "item_code": "Item Code",
            "item_name": "Item",
            "category": "Category",
            "stock_qty": "Stock",
            "reorder_level": "Reorder Level",
            "location": "Location",
            "condition": "Condition",
        }),
        use_container_width=True,
        hide_index=True,
    )

    reorder = inventory[
        pd.to_numeric(inventory["stock_qty"], errors="coerce").fillna(0)
        <= pd.to_numeric(inventory["reorder_level"], errors="coerce").fillna(0)
    ]
    if not reorder.empty:
        st.markdown("#### Reorder Watchlist")
        st.dataframe(
            reorder[["item_code", "item_name", "stock_qty", "reorder_level", "location"]]
            .rename(columns={
                "item_code": "Item Code",
                "item_name": "Item",
                "stock_qty": "Stock",
                "reorder_level": "Reorder Level",
                "location": "Location",
            }),
            use_container_width=True,
            hide_index=True,
        )


def render_dispatch():
    st.subheader("Dispatch Log")
    if dispatch.empty:
        st.info("No dispatch rows are available to this role.")
        return

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
    view = display[["event_time", "truck_id", "event_type", "details"]].rename(columns={
        "event_time": "Event Time (UTC)",
        "truck_id": "Fleet ID",
        "event_type": "Event",
        "details": "Operational Detail",
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
        pd.to_numeric(inventory["stock_qty"], errors="coerce").fillna(0)
        <= pd.to_numeric(inventory["reorder_level"], errors="coerce").fillna(0)
    ].iterrows():
        actions.append(
            f"**{row['item_code']}** — replenish {row['item_name']} "
            f"(stock {row['stock_qty']}, reorder level {row['reorder_level']})."
        )
    for _, row in fleet[fleet["status"] == "Maintenance"].iterrows():
        actions.append(
            f"**{row['truck_id']}** — track maintenance completion before restoring availability."
        )
    if actions:
        st.markdown("\n".join(f"- {item}" for item in actions))
    else:
        st.success("No immediate management action is required.")


def gate_pass_table(frame):
    if auth_mode == "authenticated":
        frame = ensure_columns(
            frame,
            [
                "pass_no", "vehicle_code", "driver_name", "destination", "purpose",
                "issued_at", "valid_until", "status"
            ],
        )
        view = frame[
            ["pass_no", "vehicle_code", "driver_name", "destination", "purpose",
             "issued_at", "valid_until", "status"]
        ].copy()
        view["issued_at"] = format_utc(view["issued_at"])
        view["valid_until"] = format_utc(view["valid_until"])
        return view.rename(columns={
            "pass_no": "Gate Pass",
            "vehicle_code": "Vehicle",
            "driver_name": "Driver",
            "destination": "Destination",
            "purpose": "Purpose",
            "issued_at": "Issued (UTC)",
            "valid_until": "Valid Until (UTC)",
            "status": "Status",
        })

    frame = ensure_columns(
        frame,
        ["pass_no", "fleet_id", "driver", "destination", "purpose", "issued_at", "valid_until", "status"],
    )
    view = frame[
        ["pass_no", "fleet_id", "driver", "destination", "purpose", "issued_at", "valid_until", "status"]
    ].copy()
    view["issued_at"] = format_utc(view["issued_at"])
    view["valid_until"] = format_utc(view["valid_until"])
    return view.rename(columns={
        "pass_no": "Gate Pass",
        "fleet_id": "Vehicle",
        "driver": "Driver",
        "destination": "Destination",
        "purpose": "Purpose",
        "issued_at": "Issued (UTC)",
        "valid_until": "Valid Until (UTC)",
        "status": "Status",
    })


def render_gate_pass_operations(role_name):
    st.subheader("Motor Vehicle Operations — Soft Gate Pass")
    if not has_permission(role_name, "create_gate_pass"):
        st.error("This role is not permitted to generate gate passes.")
        return

    if fleet.empty:
        st.info("No fleet vehicles are available to this role.")
        return

    st.caption(
        "Motor Vehicle Operations issues the pass; Gate Security can only validate it "
        "and record controlled IN/OUT transitions."
    )

    with st.form("gate_pass_form"):
        fleet_code = st.selectbox("Vehicle", fleet["truck_id"].tolist())
        vehicle = fleet[fleet["truck_id"] == fleet_code].iloc[0]
        st.text_input("Driver", value=str(vehicle["driver"]), disabled=True)
        destination = st.text_input("Destination", value=str(vehicle["destination"]))
        purpose = st.text_input("Movement purpose / cargo", value=str(vehicle["cargo"]))
        valid_hours = st.number_input("Validity (hours)", min_value=1, max_value=48, value=12)
        submitted = st.form_submit_button("Generate Soft Gate Pass")

    if submitted:
        now = datetime.now(timezone.utc)
        if auth_mode == "authenticated":
            try:
                create_gate_pass(
                    client,
                    vehicle["id"],
                    destination,
                    purpose,
                    auth_context["user_id"],
                    now + timedelta(hours=int(valid_hours)),
                )
                st.success("Soft gate pass generated in the live RLS backend.")
                st.rerun()
            except Exception as exc:
                st.error("Gate pass could not be generated.")
                st.caption(str(exc))
        else:
            new_no = f"GP-{1001 + len(st.session_state.gate_passes)}"
            st.session_state.gate_passes.append({
                "pass_no": new_no,
                "fleet_id": fleet_code,
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

    if auth_mode == "authenticated" and pd.isna(vehicle.get("driver_user_id")):
        st.caption(
            "Selected vehicle has no authenticated driver account linked yet; "
            "the pass remains visible to Operations and Gate Security."
        )

    st.markdown("#### Issued Gate Passes")
    if gate_passes.empty:
        st.info("No gate pass records are available.")
    else:
        st.dataframe(gate_pass_table(gate_passes), use_container_width=True, hide_index=True)


def render_driver_panel():
    st.subheader("Fleet Driver Panel")

    if auth_mode == "authenticated":
        assignment = fleet.copy()
        driver = auth_context.get("driver_name") or (
            assignment.iloc[0]["driver"] if not assignment.empty else None
        )
        if assignment.empty:
            st.warning("No fleet assignment is linked to this driver account.")
            return
        st.caption(f"Signed-in driver: **{driver or 'Assigned driver'}**")
    else:
        driver = st.selectbox("Demo driver identity", sorted(fleet["driver"].dropna().unique()))
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

    st.markdown("#### My Soft Gate Pass")
    if auth_mode == "authenticated":
        own_passes = gate_passes.copy()
    else:
        own_passes = ensure_columns(gate_passes, ["driver"])
        own_passes = own_passes[own_passes["driver"] == driver].copy()

    if own_passes.empty:
        st.info("No gate pass is currently visible to this driver.")
    else:
        st.dataframe(gate_pass_table(own_passes), use_container_width=True, hide_index=True)

    st.caption(
        "Authenticated driver access is restricted by RLS to the driver's own fleet assignment "
        "and own gate-pass records."
    )


def render_gate_security(role_name):
    st.subheader("Gate Security Panel")
    if not has_permission(role_name, "record_gate_movement"):
        st.error("This role is not permitted to record gate movement.")
        return

    if auth_mode == "authenticated":
        passes = ensure_columns(
            gate_passes,
            ["id", "pass_no", "vehicle_code", "driver_name", "destination", "purpose", "valid_until", "status"],
        )
    else:
        passes = ensure_columns(
            gate_passes,
            ["pass_no", "fleet_id", "driver", "destination", "purpose", "valid_until", "status"],
        )

    active = passes[passes["status"].isin(["Issued", "Vehicle Out"])].copy()
    if active.empty:
        st.info("No active soft gate pass is available.")
        render_gate_movement_summary()
        return

    selected_pass_no = st.selectbox("Soft Gate Pass", active["pass_no"].tolist())
    selected = active[active["pass_no"] == selected_pass_no].iloc[0]

    if auth_mode == "authenticated":
        vehicle_code = selected["vehicle_code"]
        driver_name = selected["driver_name"]
    else:
        vehicle_code = selected["fleet_id"]
        driver_name = selected["driver"]

    a, b, c, d = st.columns(4)
    a.metric("Vehicle", vehicle_code)
    b.metric("Driver", driver_name)
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
            if auth_mode == "authenticated":
                try:
                    record_gate_movement(
                        client, selected["id"], "OUT", gate_name, remarks
                    )
                    st.success(f"OUT recorded for {selected_pass_no}.")
                    st.rerun()
                except Exception as exc:
                    st.error("OUT movement could not be recorded.")
                    st.caption(str(exc))
            else:
                now = datetime.now(timezone.utc)
                for record in st.session_state.gate_passes:
                    if record["pass_no"] == selected_pass_no:
                        record["status"] = "Vehicle Out"
                st.session_state.gate_movements.append({
                    "pass_no": selected_pass_no,
                    "fleet_id": vehicle_code,
                    "driver": driver_name,
                    "movement": "OUT",
                    "gate": gate_name,
                    "recorded_by": "Gate Security",
                    "event_time": now,
                    "remarks": remarks,
                })
                st.success(f"OUT recorded for {selected_pass_no}.")
                st.rerun()

    with right:
        if st.button("Record Vehicle IN", disabled=in_disabled, use_container_width=True):
            if auth_mode == "authenticated":
                try:
                    record_gate_movement(
                        client, selected["id"], "IN", gate_name, remarks
                    )
                    st.success(f"IN recorded; {selected_pass_no} closed.")
                    st.rerun()
                except Exception as exc:
                    st.error("IN movement could not be recorded.")
                    st.caption(str(exc))
            else:
                now = datetime.now(timezone.utc)
                for record in st.session_state.gate_passes:
                    if record["pass_no"] == selected_pass_no:
                        record["status"] = "Closed"
                st.session_state.gate_movements.append({
                    "pass_no": selected_pass_no,
                    "fleet_id": vehicle_code,
                    "driver": driver_name,
                    "movement": "IN",
                    "gate": gate_name,
                    "recorded_by": "Gate Security",
                    "event_time": now,
                    "remarks": remarks,
                })
                st.success(f"IN recorded and {selected_pass_no} closed.")
                st.rerun()

    st.caption(
        "Gate Security cannot edit the pass destination, purpose or vehicle assignment; "
        "only validated IN/OUT transitions are permitted."
    )
    render_gate_movement_summary()


def render_gate_movement_summary():
    st.subheader("Gate Movement Summary")

    if gate_movements.empty:
        st.info("No gate movement has been recorded.")
        return

    if auth_mode == "authenticated":
        movements = ensure_columns(
            gate_movements,
            ["gate_pass_id", "movement_type", "gate_name", "event_time", "remarks"],
        ).copy()
        passes = ensure_columns(
            gate_passes, ["id", "pass_no", "vehicle_code", "driver_name"]
        )
        movements = movements.merge(
            passes[["id", "pass_no", "vehicle_code", "driver_name"]],
            left_on="gate_pass_id",
            right_on="id",
            how="left",
        )
        out_count = int((movements["movement_type"] == "OUT").sum())
        in_count = int((movements["movement_type"] == "IN").sum())
        movements["event_time"] = format_utc(movements["event_time"])
        view = movements[
            ["event_time", "pass_no", "vehicle_code", "driver_name",
             "movement_type", "gate_name", "remarks"]
        ].rename(columns={
            "event_time": "Event Time (UTC)",
            "pass_no": "Gate Pass",
            "vehicle_code": "Vehicle",
            "driver_name": "Driver",
            "movement_type": "Movement",
            "gate_name": "Gate",
            "remarks": "Remarks",
        })
    else:
        movements = ensure_columns(
            gate_movements,
            ["event_time", "pass_no", "fleet_id", "driver", "movement", "gate", "remarks"],
        ).copy()
        out_count = int((movements["movement"] == "OUT").sum())
        in_count = int((movements["movement"] == "IN").sum())
        movements["event_time"] = format_utc(movements["event_time"])
        view = movements[
            ["event_time", "pass_no", "fleet_id", "driver", "movement", "gate", "remarks"]
        ].rename(columns={
            "event_time": "Event Time (UTC)",
            "pass_no": "Gate Pass",
            "fleet_id": "Vehicle",
            "driver": "Driver",
            "movement": "Movement",
            "gate": "Gate",
            "remarks": "Remarks",
        })

    g1, g2, g3 = st.columns(3)
    g1.metric("Movement Records", len(movements))
    g2.metric("OUT Records", out_count)
    g3.metric("IN Records", in_count)
    st.dataframe(view, use_container_width=True, hide_index=True)


def render_finance(read_only=True):
    title = "Finance Summary" if read_only else "Accountant Panel"
    st.subheader(title)

    finance = ensure_columns(
        finance_entries,
        ["entry_no", "fleet_id", "vehicle_code", "category", "amount", "reference", "entry_time"],
    ).copy()
    finance["amount"] = pd.to_numeric(finance["amount"], errors="coerce").fillna(0.0)

    total = float(finance["amount"].sum())
    fuel = float(finance.loc[finance["category"] == "Fuel", "amount"].sum())
    maint = float(finance.loc[finance["category"] == "Maintenance", "amount"].sum())
    f1, f2, f3 = st.columns(3)
    f1.metric("Recorded Cost", f"PKR {total:,.0f}")
    f2.metric("Fuel Cost", f"PKR {fuel:,.0f}")
    f3.metric("Maintenance Cost", f"PKR {maint:,.0f}")

    if not finance.empty:
        by_category = finance.groupby("category", as_index=False)["amount"].sum()
        st.bar_chart(by_category, x="category", y="amount", horizontal=True, height=300)

    if not read_only and has_permission(selected_role, "record_finance"):
        with st.expander("Record finance entry"):
            with st.form("finance_entry_form"):
                if auth_mode == "authenticated":
                    vehicle_code = st.text_input(
                        "Vehicle code (optional)",
                        help="Example: FLT-109. Leave blank for a general/non-vehicle cost.",
                    )
                else:
                    vehicle_code = st.selectbox(
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
                    "Amount (PKR)", min_value=0.0, step=500.0, key="finance_amount"
                )
                reference = st.text_input(
                    "Reference / narration", key="finance_reference"
                )
                submitted = st.form_submit_button("Record Finance Entry")

            if submitted:
                if auth_mode == "authenticated":
                    try:
                        record_finance_entry(
                            client,
                            vehicle_code.strip(),
                            category,
                            amount,
                            reference or "Finance entry",
                        )
                        st.success("Finance entry recorded in the live RLS backend.")
                        st.rerun()
                    except Exception as exc:
                        st.error("Finance entry could not be recorded.")
                        st.caption(str(exc))
                else:
                    new_no = f"FN-{len(st.session_state.finance_entries) + 1:03d}"
                    st.session_state.finance_entries.append({
                        "entry_no": new_no,
                        "fleet_id": (
                            None if vehicle_code == "General / Non-vehicle"
                            else vehicle_code
                        ),
                        "category": category,
                        "amount": float(amount),
                        "reference": reference or "Demo finance entry",
                        "entry_time": datetime.now(timezone.utc),
                    })
                    st.success(f"{new_no} recorded.")
                    st.rerun()

    if finance.empty:
        st.info("No finance entries are currently visible to this role.")
        return

    finance["entry_time"] = format_utc(finance["entry_time"])
    if auth_mode == "authenticated":
        view = finance[
            ["entry_no", "vehicle_code", "category", "amount", "reference", "entry_time"]
        ].rename(columns={
            "entry_no": "Entry",
            "vehicle_code": "Vehicle",
            "category": "Category",
            "amount": "Amount (PKR)",
            "reference": "Reference",
            "entry_time": "Entry Time (UTC)",
        })
    else:
        view = finance[
            ["entry_no", "fleet_id", "category", "amount", "reference", "entry_time"]
        ].rename(columns={
            "entry_no": "Entry",
            "fleet_id": "Vehicle",
            "category": "Category",
            "amount": "Amount (PKR)",
            "reference": "Reference",
            "entry_time": "Entry Time (UTC)",
        })
    st.dataframe(view, use_container_width=True, hide_index=True)


def render_maintenance(role_name, read_only=False):
    title = "Maintenance Overview" if read_only else "Motor Vehicle Maintenance Panel"
    st.subheader(title)

    records = ensure_columns(
        maintenance_records,
        [
            "id", "job_no", "fleet_id", "work_type", "complaint",
            "priority", "status", "opened_at", "target_completion", "closed_at"
        ],
    ).copy()

    fleet_lookup = dict(zip(fleet["id"].astype(str), fleet["truck_id"].astype(str)))
    records["vehicle_code"] = records["fleet_id"].astype(str).map(fleet_lookup)

    open_jobs = int((records["status"] != "Completed").sum()) if not records.empty else 0
    high = int((records["priority"] == "High").sum()) if not records.empty else 0
    completed = int((records["status"] == "Completed").sum()) if not records.empty else 0
    m1, m2, m3 = st.columns(3)
    m1.metric("Open Jobs", open_jobs)
    m2.metric("High Priority", high)
    m3.metric("Completed", completed)

    if not read_only and has_permission(role_name, "update_maintenance"):
        with st.expander("Open maintenance job"):
            with st.form("maintenance_job_form"):
                vehicle_code = st.selectbox(
                    "Vehicle",
                    fleet["truck_id"].tolist(),
                    key="maintenance_vehicle",
                ) if not fleet.empty else None
                work_type = st.selectbox(
                    "Work type",
                    ["Corrective", "Preventive", "Inspection"],
                    key="maintenance_work_type",
                )
                complaint = st.text_area("Complaint / work required")
                priority = st.selectbox(
                    "Priority", ["Low", "Normal", "High", "Critical"],
                    index=1, key="maintenance_priority"
                )
                target_hours = st.number_input(
                    "Target completion (hours)",
                    min_value=1, max_value=168, value=24
                )
                submitted = st.form_submit_button("Open Maintenance Job")

            if submitted:
                if not vehicle_code:
                    st.error("No fleet vehicle is available.")
                elif auth_mode == "authenticated":
                    vehicle = fleet[fleet["truck_id"] == vehicle_code].iloc[0]
                    try:
                        create_maintenance_job(
                            client,
                            vehicle["id"],
                            work_type,
                            complaint or "Maintenance task",
                            priority,
                            auth_context["user_id"],
                            datetime.now(timezone.utc) + timedelta(hours=int(target_hours)),
                        )
                        st.success("Maintenance job opened in the live RLS backend.")
                        st.rerun()
                    except Exception as exc:
                        st.error("Maintenance job could not be opened.")
                        st.caption(str(exc))
                else:
                    new_no = f"MX-{len(st.session_state.maintenance_records) + 1:03d}"
                    st.session_state.maintenance_records.append({
                        "job_no": new_no,
                        "fleet_id": vehicle_code,
                        "work_type": work_type,
                        "complaint": complaint or "Maintenance task",
                        "priority": priority,
                        "status": "Scheduled",
                        "opened_at": datetime.now(timezone.utc),
                        "target_completion": (
                            datetime.now(timezone.utc) + timedelta(hours=int(target_hours))
                        ),
                    })
                    st.success(f"{new_no} opened.")
                    st.rerun()

    if records.empty:
        st.info("No maintenance records are currently visible to this role.")
        return

    view = records.copy()
    view["opened_at"] = format_utc(view["opened_at"])
    view["target_completion"] = format_utc(view["target_completion"])
    st.dataframe(
        view[
            ["job_no", "vehicle_code", "work_type", "complaint", "priority",
             "status", "opened_at", "target_completion"]
        ].rename(columns={
            "job_no": "Job",
            "vehicle_code": "Vehicle",
            "work_type": "Work Type",
            "complaint": "Complaint / Work",
            "priority": "Priority",
            "status": "Status",
            "opened_at": "Opened (UTC)",
            "target_completion": "Target Completion (UTC)",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if read_only or not has_permission(role_name, "update_maintenance"):
        return

    st.markdown("#### Update Workshop Job")
    selected_job = st.selectbox("Job", records["job_no"].tolist())
    current = records[records["job_no"] == selected_job].iloc[0]
    statuses = ["Scheduled", "In Progress", "Awaiting Parts", "Completed"]
    current_index = statuses.index(current["status"]) if current["status"] in statuses else 0
    new_status = st.selectbox("New status", statuses, index=current_index)

    if st.button("Update maintenance status"):
        if auth_mode == "authenticated":
            try:
                update_maintenance_status(client, current["id"], new_status)
                st.success(f"{selected_job} updated to {new_status}.")
                st.rerun()
            except Exception as exc:
                st.error("Maintenance status could not be updated.")
                st.caption(str(exc))
        else:
            for record in st.session_state.maintenance_records:
                if record["job_no"] == selected_job:
                    record["status"] = new_status
            st.success(f"{selected_job} updated to {new_status}.")
            st.rerun()


PANEL_RENDERERS = {
    "Executive Overview": render_executive_overview,
    "Fleet & Map": render_fleet,
    "Materials": render_materials,
    "Dispatch Log": render_dispatch,
    "Management Brief": render_management_brief,
    "Gate Pass Operations": lambda: render_gate_pass_operations(selected_role),
    "Driver Panel": render_driver_panel,
    "Gate Security Panel": lambda: render_gate_security(selected_role),
    "Gate Movement Summary": render_gate_movement_summary,
    "Finance Summary": lambda: render_finance(read_only=True),
    "Accountant Panel": lambda: render_finance(read_only=False),
    "Maintenance Overview": lambda: render_maintenance(selected_role, read_only=True),
    "Maintenance Panel": lambda: render_maintenance(selected_role, read_only=False),
}

PANEL_RENDERERS[selected_panel]()

generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<p class="small-note">Role: {selected_role} • Data source: {data_source} • '
    f'Generated: {generated_at} • Access mode: {auth_mode} • '
    f'RLS is the authorization boundary in authenticated mode.</p>',
    unsafe_allow_html=True,
)
