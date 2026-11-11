from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "teamdraft" / "gui" / "app.py"
# The first run imports Streamlit and pandas (cold start), which can exceed the 3 s default.
STARTUP_TIMEOUT = 15


def test_app_runs_without_exception():
    # AppTest executes the script headless, like a browser session would.
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    assert not app.exception
    assert app.title[0].value == "Pokémon Team Draft"


def test_app_shows_data_model():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    assert "Data model" in [header.value for header in app.header]
    assert any("GameData" in expander.label for expander in app.expander)
