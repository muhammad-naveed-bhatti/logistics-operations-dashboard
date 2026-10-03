from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROLES = [
    "Senior Officers",
    "Log Staff Supervisor",
    "Log Staff",
    "Motor Vehicle Operations",
    "Fleet Drivers",
    "Accountant",
    "Motor Vehicle Maintenance",
    "Gate Security",
]


def assert_no_exceptions(app, context):
    if app.exception:
        messages = [str(item.value) for item in app.exception]
        raise AssertionError(f"{context} exceptions: {messages}")


def find_button(app, label):
    for widget in app.button:
        if widget.label == label:
            return widget
    raise AssertionError(f"Button not found: {label}")


def role_widget(app):
    for widget in app.selectbox:
        if widget.label == "Demo role":
            return widget
    raise AssertionError("Demo role selector was not rendered.")


def main():
    app_path = ROOT / "app.py"
    app = AppTest.from_file(app_path, default_timeout=20).run()
    assert_no_exceptions(app, "Login screen")

    find_button(app, "Enter Portfolio Demo").click()
    app.run()
    assert_no_exceptions(app, "Portfolio demo entry")

    assert len(app.metric) >= 5, "Expected executive KPI metrics were not rendered."
    assert len(app.radio) >= 1, "Role-specific workspace navigation was not rendered."

    for role in ROLES:
        role_widget(app).select(role)
        app.run()
        assert_no_exceptions(app, f"{role} workspace")
        assert len(app.radio) >= 1, f"{role} workspace navigation missing."

    print("Login gate and all role workspaces passed the Streamlit smoke test.")


if __name__ == "__main__":
    main()
