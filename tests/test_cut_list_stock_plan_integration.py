"""Regression coverage for Cut List stock-plan integration."""

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
CUT_LIST_PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "cut_list.py"
)
DIALOG_PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "dialogs"
    / "tube_stock_plan.py"
)


def _function_source(name):
    source = CUT_LIST_PATH.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        source
    )

    node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == name
    )

    return ast.get_source_segment(
        source,
        node,
    )


class FakeCutListItem:
    def __init__(
        self,
        **values,
    ):
        self.__dict__.update(
            values
        )


class FakeCutList:
    def __init__(
        self,
        items,
    ):
        self.items = items


def test_cut_list_conversion_preserves_member_name():
    namespace = {
        "CutListItem": FakeCutListItem,
        "CutList": FakeCutList,
    }

    exec(
        _function_source(
            "cut_list_from_rows"
        ),
        namespace,
    )

    result = namespace[
        "cut_list_from_rows"
    ](
        [
            {
                "member_id": "ForgeCADBentTube",
                "member_name": "Main Hoop",
                "tube_profile": "1.750 x .120 DOM",
                "material": "A513 Type 5 DOM",
                "length_mm": 2200.0,
                "outside_diameter_mm": 44.45,
                "wall_thickness_mm": 3.048,
                "weight_kg": 10.0,
            }
        ]
    )

    assert (
        result.items[0].member_name
        == "Main Hoop"
    )


def test_cut_list_dialog_contains_stock_plan_action():
    source = CUT_LIST_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"Stock Plan"'
        in source
    )

    assert (
        "self.open_stock_plan"
        in source
    )

    assert (
        "TubeStockPlanDialog"
        in source
    )


def test_stock_plan_dialog_source_is_valid_python():
    source = DIALOG_PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    assert (
        "plan_tube_stock"
        in source
    )

    assert (
        "DEFAULT_STOCK_LENGTH_MM"
        in source
    )

    assert (
        "DEFAULT_SAW_KERF_MM"
        in source
    )
