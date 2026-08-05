"""Conversion of FreeCAD-like layout objects into ForgeCAD layouts."""

from forgecad import FrameLayout, LayoutLine
from forgecad.geometry import Point3D


def _point_from_vector(vector):
    return Point3D(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def layout_from_selected_objects(objects):
    layout = FrameLayout()

    for obj in objects:
        if not hasattr(obj, "StartPoint") or not hasattr(obj, "EndPoint"):
            continue

        layout.add_line(
            LayoutLine(
                start=_point_from_vector(obj.StartPoint),
                end=_point_from_vector(obj.EndPoint),
            )
        )

    return layout