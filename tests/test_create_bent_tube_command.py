"""Tests for the Create Bent Tube command helpers."""

import sys
import types


# Adapter-package imports require FreeCAD / Part / PySide stubs.
fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)


class FakeQDialog:
    Accepted = 1


fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeQDialog,
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "Part"
] = fake_part
sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands.create_bent_tube import (
    create_tube_from_dialog,
)


class FakeDialog:
    profile_name = "1.750 x .120 DOM"

    @property
    def definition(
        self,
    ):
        from forgecad.services.bent_tube_creation import (
            BendInput,
            BentTubeInput,
        )

        return BentTubeInput(
            name="Main Hoop",
            run_lengths=(
                500.0,
                600.0,
                700.0,
            ),
            bends=(
                BendInput(
                    angle_degrees=90.0,
                    centerline_radius=100.0,
                    rotation_degrees=0.0,
                ),
                BendInput(
                    angle_degrees=45.0,
                    centerline_radius=125.0,
                    rotation_degrees=90.0,
                ),
            ),
        )


def test_create_tube_from_dialog_resolves_profile_and_path():
    tube = create_tube_from_dialog(
        FakeDialog()
    )

    assert tube.profile.outside_diameter == 44.45
    assert tube.profile.wall_thickness == 3.048
    assert tube.bend_count == 2

    assert tuple(
        run.length_mm
        for run in tube.straight_runs
    ) == (
        500.0,
        600.0,
        700.0,
    )

    assert (
        tube.bends[
            1
        ].rotation_degrees
        == 90.0
    )
