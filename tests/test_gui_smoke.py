from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "teamdraft" / "gui" / "app.py"


def test_app_runs_without_exception():
    # AppTest executes the script headless, like a browser session would.
    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    assert app.title[0].value == "Pokémon Team Draft"
