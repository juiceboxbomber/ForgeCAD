from forgecad.services.layout_conversion import (
    layout_from_selected_objects,
)


class FakeVector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class FakeLayoutObject:
    def __init__(self, start, end):
        self.StartPoint = FakeVector(*start)
        self.EndPoint = FakeVector(*end)


class FakeUnrelatedObject:
    pass


def test_layout_from_selected_objects():
    objects = [
        FakeLayoutObject(
            (0, 0, 0),
            (1000, 0, 0),
        ),
        FakeLayoutObject(
            (1000, 0, 0),
            (1000, 600, 0),
        ),
    ]

    layout = layout_from_selected_objects(objects)

    assert layout.line_count == 2
    assert len(layout.points) == 3


def test_unrelated_objects_are_ignored():
    layout = layout_from_selected_objects(
        [FakeUnrelatedObject()]
    )

    assert layout.line_count == 0
