import pytest

from teamdraft.config import DEFAULT_CONFIG_PATH, Settings, load_settings


def test_missing_file_uses_defaults(tmp_path):
    assert load_settings(tmp_path / "missing.toml") == Settings(level=50)


def test_missing_key_uses_default(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[team]\n", encoding="utf-8")
    assert load_settings(path).level == 50


def test_level_is_read_from_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[team]\nlevel = 35\n", encoding="utf-8")
    assert load_settings(path).level == 35


@pytest.mark.parametrize("value", ["0", "101", '"50"', "true"])
def test_invalid_level_raises(tmp_path, value):
    path = tmp_path / "config.toml"
    path.write_text(f"[team]\nlevel = {value}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="team.level"):
        load_settings(path)


def test_shipped_config_is_valid():
    assert load_settings(DEFAULT_CONFIG_PATH).level == 50
