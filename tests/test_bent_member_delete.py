"""Bent-member Delete Member regressions."""

import sys
import types
from types import SimpleNamespace


sys.modules.setdefault(
    "FreeCAD",
    types.ModuleType(
        "FreeCAD"
    ),
)

sys.modules.setdefault(
    "FreeCADGui",
    types.ModuleType(
        "FreeCADGui"
    ),
)

sys.modules.setdefault(
    "Part",
    types.ModuleType(
        "Part"
    ),
)

pyside = types.ModuleType(
    "PySide"
)
pyside.QtGui = types.ModuleType(
    "PySide.QtGui"
)

sys.modules.setdefault(
    "PySide",
    pyside,
)
sys.modules.setdefault(
    "PySide.QtGui",
    pyside.QtGui,
)


from forgecad.adapters.freecad import member_removal
from forgecad.adapters.freecad.commands import delete_member as module


class FakeGroup:
    def __init__(self, objects=()):
        self.Group = list(objects)

    def removeObject(self, obj):
        if obj in self.Group:
            self.Group.remove(obj)


class FakeDocument:
    def __init__(self, frame=(), layouts=()):
        self.frame = FakeGroup(frame)
        self.layout = FakeGroup(layouts)
        self.objects = {
            obj.Name: obj
            for obj in (*frame, *layouts)
        }
        self.removed = []
        self.recompute_count = 0

    def getObject(self, name):
        if name == "ForgeCADFrame":
            return self.frame
        if name == "ForgeCADLayout":
            return self.layout
        return self.objects.get(name)

    def removeObject(self, name):
        self.removed.append(name)
        self.objects.pop(name, None)

    def recompute(self):
        self.recompute_count += 1


def layout(name, layout_id):
    return SimpleNamespace(
        Name=name,
        LayoutID=layout_id,
    )


def bent(name, source_layouts):
    proxy = SimpleNamespace(
        replace_tube_definition=lambda *args, **kwargs: None,
        _tube_from_properties=lambda *args, **kwargs: None,
    )

    return SimpleNamespace(
        Name=name,
        Proxy=proxy,
        StartPoint=SimpleNamespace(),
        InitialDirection=SimpleNamespace(),
        InitialBendNormal=SimpleNamespace(),
        TubeProfile=SimpleNamespace(),
        BendCount=1,
        StartNode=SimpleNamespace(Name=f"{name}_Start"),
        EndNode=SimpleNamespace(Name=f"{name}_End"),
        DesignJointNode=SimpleNamespace(Name=f"{name}_Joint"),
        SourceLayoutLines=list(source_layouts),
        StartFabricationLayoutID=source_layouts[0].LayoutID,
        EndFabricationLayoutID=source_layouts[-1].LayoutID,
    )


def test_bent_source_layout_ids_include_all_owned_layouts():
    first = layout("Layout1", "layout-1")
    second = layout("Layout2", "layout-2")
    obj = bent("Bent1", (first, second))

    assert member_removal.bent_source_layout_ids(obj) == (
        "layout-1",
        "layout-2",
    )


def test_remove_bent_member_removes_owned_hidden_layouts():
    first = layout("Layout1", "layout-1")
    second = layout("Layout2", "layout-2")
    obj = bent("Bent1", (first, second))

    document = FakeDocument(
        frame=(obj,),
        layouts=(first, second),
    )

    assert member_removal.remove_bent_member_and_unused_layouts(
        document,
        obj,
    )

    assert document.removed == [
        "Bent1",
        "Layout1",
        "Layout2",
    ]


def test_remove_bent_member_preserves_layout_still_owned_elsewhere():
    first = layout("Layout1", "layout-1")
    second = layout("Layout2", "layout-2")
    obj = bent("Bent1", (first, second))

    other = SimpleNamespace(
        Name="Straight1",
        MemberID="member-1",
        SourceLayoutID="layout-2",
    )

    document = FakeDocument(
        frame=(obj, other),
        layouts=(first, second),
    )

    member_removal.remove_bent_member_and_unused_layouts(
        document,
        obj,
    )

    assert "Bent1" in document.removed
    assert "Layout1" in document.removed
    assert "Layout2" not in document.removed


def test_delete_member_recognizes_bent_member():
    obj = bent(
        "Bent1",
        (
            layout("Layout1", "layout-1"),
        ),
    )

    assert module.is_forgecad_member(obj)


def test_design_joint_nodes_collects_numbered_and_legacy_links():
    legacy = SimpleNamespace(Name="Joint1")
    second = SimpleNamespace(Name="Joint2")

    obj = SimpleNamespace(
        DesignJointNode=legacy,
        DesignJointNode1=legacy,
        DesignJointNode2=second,
    )

    assert module.design_joint_nodes(obj) == (
        legacy,
        second,
    )
