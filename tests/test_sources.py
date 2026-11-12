from teamdraft.data.sources import load_manifest
from teamdraft.reporting.data_model import ENTITY_GROUPS

MANIFEST = load_manifest()


def test_manifest_pins_a_full_commit_hash():
    assert len(MANIFEST.commit) == 40


def test_file_names_are_unique_csv_files():
    names = [file.name for file in MANIFEST.files]
    assert len(names) == len(set(names))
    assert all(name.endswith(".csv") for name in names)


def test_required_files_feed_existing_domain_classes():
    domain_classes = {cls.__name__ for cls in ENTITY_GROUPS}
    for file in MANIFEST.required_files:
        assert file.feeds, f"{file.name} is required but feeds nothing"
        assert set(file.feeds) <= domain_classes, f"{file.name} feeds unknown classes {file.feeds}"


def test_missing_files_lists_only_absent_required_files(tmp_path):
    (tmp_path / "versions.csv").write_text("id\n", encoding="utf-8")
    missing = {file.name for file in MANIFEST.missing_files(tmp_path)}
    assert "versions.csv" not in missing
    assert "pokemon_moves.csv" in missing
    assert "locations.csv" not in missing  # optional
    assert len(missing) == len(MANIFEST.required_files) - 1
