"""Frame-layout conversion services."""

from forgecad import FrameLayout, Project
from forgecad.fabrication import Frame, Member, Node


def build_frame_from_layout(
    project: Project,
    layout: FrameLayout,
) -> Frame:
    """Build a structural frame from a centerline layout."""

    if project.default_material is None:
        raise ValueError(
            "The project must have a default material."
        )

    profile = project.tube_library.active_profile
    material = project.default_material

    frame = Frame()
    nodes_by_point = {}

    for point in layout.points:
        node = Node(point.x, point.y, point.z)
        nodes_by_point[point] = node
        frame.add_node(node)

    for line in layout.lines:
        frame.add_member(
            Member(
                start=nodes_by_point[line.start],
                end=nodes_by_point[line.end],
                profile=profile,
                material=material,
            )
        )

    return frame
