"""Guards the layer rules from ARCHITECTURE.md, so the GUI library stays replaceable."""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "teamdraft"
GUI_LIBRARIES = {"streamlit", "tkinter", "PySide6", "PyQt6", "nicegui"}

NON_GUI_MODULES = [p for p in PACKAGE_ROOT.rglob("*.py") if "gui" not in p.relative_to(PACKAGE_ROOT).parts]


def imported_top_level_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("module", NON_GUI_MODULES, ids=lambda p: str(p.relative_to(PACKAGE_ROOT)))
def test_only_gui_package_imports_gui_libraries(module):
    forbidden = imported_top_level_names(module) & GUI_LIBRARIES
    assert not forbidden, f"{module.name} imports GUI library {forbidden}; GUI code belongs in teamdraft/gui/."
