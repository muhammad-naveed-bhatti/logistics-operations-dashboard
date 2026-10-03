from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    app_path = ROOT / "app.py"
    app = AppTest.from_file(app_path, default_timeout=20).run()

    if app.exception:
        messages = [str(item.value) for item in app.exception]
        raise AssertionError(f"Streamlit runtime exceptions: {messages}")

    assert len(app.metric) >= 5, "Expected dashboard KPI metrics were not rendered."
    assert len(app.tabs) >= 5, "Expected dashboard tabs were not rendered."

    print("Streamlit app runtime smoke test passed.")


if __name__ == "__main__":
    main()
