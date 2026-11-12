from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "teamdraft" / "gui" / "app.py"
# The first run imports Streamlit and pandas (cold start), which took up to 10 s here.
STARTUP_TIMEOUT = 30


def test_app_runs_without_exception():
    # AppTest executes the script headless, like a browser session would.
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    assert not app.exception
    assert app.title[0].value == "Pokémon Team Draft"


def test_app_shows_draft_game_data_and_data_model():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    assert [tab.label for tab in app.tabs] == ["Team draft", "Game data", "Data model"]
    assert "Data model" in [header.value for header in app.header]
    assert any("GameData" in expander.label for expander in app.expander)


def test_switching_the_game_shows_its_data():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    if not app.selectbox:
        return  # no imported game data on this machine; the import button is shown instead
    app.selectbox[0].select_index(5).run(timeout=STARTUP_TIMEOUT)  # Crystal
    assert not app.exception
    assert app.metric[0].value == "2"


def test_gen_1_game_shows_the_draft():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    if not app.selectbox:
        return  # no imported game data on this machine
    app.selectbox[0].select_index(2).run(timeout=STARTUP_TIMEOUT)  # Yellow
    assert not app.exception
    assert "Team draft – Yellow" in [header.value for header in app.header]
    labels = [m.value for m in app.markdown]
    assert sum("**Option 1**" in label for label in labels) == 1
    assert "Team coverage" in [sub.value for sub in app.subheader]


def test_other_games_show_no_draft():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=STARTUP_TIMEOUT)
    if not app.selectbox:
        return
    app.selectbox[0].select_index(5).run(timeout=STARTUP_TIMEOUT)  # Crystal
    assert not any(header.value.startswith("Team draft") for header in app.header)
    assert any("Red, Blue and Yellow" in info.value for info in app.info)
