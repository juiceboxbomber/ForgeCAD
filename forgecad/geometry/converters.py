from forgecad.fabrication.member import Member
from forgecad.geometry.primitives import LineSegment, Point3D


def member_to_line(member: Member) -> LineSegment:
    return LineSegment(
        start=Point3D(
            member.start_node.x,
            member.start_node.y,
            member.start_node.z,
        ),
        end=Point3D(
            member.end_node.x,
            member.end_node.y,
            member.end_node.z,
        ),
    )
