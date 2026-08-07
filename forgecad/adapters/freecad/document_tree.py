"""Helpers for organizing ForgeCAD objects in a FreeCAD document."""

import FreeCAD


GROUP_DEFINITIONS = {
    
    "Layout": ("ForgeCADLayout", "Layout"),
    "Frame": ("ForgeCADFrame", "Frame"),
    "Nodes": ("ForgeCADNodes", "Nodes"),
    "Tube Library": ("ForgeCADTubeLibrary", "Tube Library"),
    "Settings": ("ForgeCADSettings", "Settings"),
}


def get_or_create_group(document, internal_name, label):
    """Return an existing document group or create it."""

    group = document.getObject(internal_name)

    if group is None:
        group = document.addObject(
            "App::DocumentObjectGroup",
            internal_name,
        )

    group.Label = label

    return group


def initialize_project_tree(document):
    """Create or return the standard ForgeCAD project tree."""

    root = document.getObject("ForgeCADProject")

    if root is None:
        root = document.addObject(
            "App::DocumentObjectGroupPython",
            "ForgeCADProject",
        )
        root.Label = "ForgeCAD Project"

    children = {}

    for key in (
        "Layout",
        "Frame",
        "Nodes",
        "Tube Library",
        "Settings",
    ):
        internal_name, label = GROUP_DEFINITIONS[key]

        group = get_or_create_group(
            document,
            internal_name,
            label,
        )

        if group not in root.Group:
            root.addObject(group)

        children[key] = group

    return children

