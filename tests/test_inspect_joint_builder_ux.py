"""Tests for builder-facing Joint Inspector treatment wording."""

import ast
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(
    "forgecad/adapters/freecad/commands/inspect_joint.py"
)

tree = ast.parse(
    SOURCE.read_text(
        encoding="utf-8"
    )
)

wanted = {
    "treatment_builder_label",
    "treatment_builder_prompt",
}

helper_nodes = [
    node
    for node in tree.body
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name in wanted
    )
]

module = ast.Module(
    body=helper_nodes,
    type_ignores=[],
)

namespace = {}

exec(
    compile(
        module,
        str(
            SOURCE
        ),
        "exec",
    ),
    namespace,
)

treatment_builder_label = (
    namespace[
        "treatment_builder_label"
    ]
)

treatment_builder_prompt = (
    namespace[
        "treatment_builder_prompt"
    ]
)


def option(
    mode,
    label,
):
    return SimpleNamespace(
        mode=SimpleNamespace(
            value=mode
        ),
        label=label,
    )


def test_builder_prompt_is_plain_language():
    assert (
        treatment_builder_prompt()
        == "How should this joint be built?"
    )


def test_automatic_choice_explains_forgecad_decides():
    assert (
        treatment_builder_label(
            option(
                "auto",
                "Automatic",
            )
        )
        == "Automatic - Let ForgeCAD choose"
    )


def test_member_through_choice_explains_continuous_member():
    assert (
        treatment_builder_label(
            option(
                "member_through",
                "M003 Through",
            )
        )
        == (
            "M003 Through - "
            "Keep M003 continuous"
        )
    )


def test_through_pair_choice_explains_continuous_members():
    assert (
        treatment_builder_label(
            option(
                "through_pair",
                "M001 + M002 Through",
            )
        )
        == (
            "M001 + M002 Through - "
            "Keep these members continuous"
        )
    )


def test_miter_choice_explains_physical_result():
    assert (
        treatment_builder_label(
            option(
                "both_mitered",
                "Both Mitered",
            )
        )
        == (
            "Both Mitered - "
            "Miter both members at the joint"
        )
    )
