"""Regression coverage for Tube Stock Plan CSV export UI."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG_PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "dialogs"
    / "tube_stock_plan.py"
)


def _source():
    return DIALOG_PATH.read_text(
        encoding="utf-8"
    )


def _dialog_class():
    tree = ast.parse(
        _source()
    )

    return next(
        node
        for node in tree.body
        if isinstance(
            node,
            ast.ClassDef,
        )
        and node.name
        == "TubeStockPlanDialog"
    )


def test_stock_plan_dialog_has_export_csv_method():
    dialog = _dialog_class()

    method_names = {
        node.name
        for node in dialog.body
        if isinstance(
            node,
            ast.FunctionDef,
        )
    }

    assert (
        "export_csv"
        in method_names
    )


def test_stock_plan_dialog_has_export_button():
    source = _source()

    assert (
        '"Export CSV"'
        in source
    )

    assert (
        "self.export_csv"
        in source
    )


def test_stock_plan_dialog_uses_stock_export_service():
    source = _source()

    assert (
        "tube_stock_plan_to_csv"
        in source
    )

    assert (
        "tube_stock_export"
        in source
    )


def test_stock_plan_export_uses_save_dialog_and_csv_extension():
    source = _source()

    assert (
        "QFileDialog.getSaveFileName"
        in source
    )

    assert (
        'endswith(".csv")'
        in source
    )

    assert (
        "ForgeCAD_stock_plan.csv"
        in source
    )
