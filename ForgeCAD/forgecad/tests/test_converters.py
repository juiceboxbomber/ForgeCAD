from forgecad.fabrication.material import Material
from forgecad.fabrication.member import Member
from forgecad.fabrication.node import Node
from forgecad.fabrication.tube_profile import TubeProfile
from forgecad.geometry.converters import member_to_line


def test_member_to_line():
    member = Member(
        start_node=Node.at(0, 0, 0),
        end_node=Node.at(1000, 0, 0),
        profile=TubeProfile(
            outside_diameter_mm=44.45,
            wall_thickness_mm=3.048,
        ),
        material=Material(
            name="4130",
            density=7.85e-6,
            yield_strength=435,
            ultimate_strength=670,
            elastic_modulus=205000,
        ),
    )

    line = member_to_line(member)

    assert line.start.x == 0
    assert line.end.x == 1000
    assert line.length == 1000
    