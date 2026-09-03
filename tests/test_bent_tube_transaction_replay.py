"""Regression tests for bent-tube behavior during FreeCAD transaction replay."""

import importlib
import sys
import types


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


def import_bent_tube_module():
    module_name = (
        "forgecad.adapters.freecad.bent_tube_object"
    )

    previous_modules = {
        name: sys.modules.get(
            name
        )
        for name in (
            "FreeCAD",
            "Part",
            module_name,
        )
    }

    fake_freecad = types.ModuleType(
        "FreeCAD"
    )
    fake_freecad.Vector = FakeVector

    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad
    sys.modules[
        "Part"
    ] = fake_part

    sys.modules.pop(
        module_name,
        None,
    )

    try:
        module = importlib.import_module(
            module_name
        )
    finally:
        for (
            name,
            previous_module,
        ) in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(
                    name,
                    None,
                )
            else:
                sys.modules[
                    name
                ] = previous_module

    return module


bent_tube_object = (
    import_bent_tube_module()
)


class FakeDocument:
    def __init__(
        self,
        restoring,
    ):
        self.restoring = bool(
            restoring
        )

    def isPerformingTransaction(
        self,
    ):
        return self.restoring


class FakeObject:
    def __init__(
        self,
        document,
    ):
        self.Document = document


def make_proxy():
    proxy = object.__new__(
        bent_tube_object.BentTubeProxy
    )

    proxy._ready = True
    proxy._updating = False
    proxy._geometry_dirty = True
    proxy._bend_count = 1
    proxy._last_joint_geometry = None

    return proxy


def test_transaction_replay_detection():
    assert (
        bent_tube_object.document_is_restoring_transaction(
            FakeDocument(
                restoring=False
            )
        )
        is False
    )

    assert (
        bent_tube_object.document_is_restoring_transaction(
            FakeDocument(
                restoring=True
            )
        )
        is True
    )

    assert (
        bent_tube_object.document_is_restoring_transaction(
            None
        )
        is False
    )


def test_onchanged_does_not_mutate_bent_tube_during_transaction_replay():
    document = FakeDocument(
        restoring=True
    )
    obj = FakeObject(
        document
    )
    proxy = make_proxy()

    calls = []

    proxy._update_label = (
        lambda target: calls.append(
            (
                "label",
                target,
            )
        )
    )
    proxy.mark_geometry_dirty = (
        lambda: calls.append(
            (
                "dirty",
                obj,
            )
        )
    )
    proxy.update_shape = (
        lambda target: calls.append(
            (
                "shape",
                target,
            )
        )
    )

    proxy.onChanged(
        obj,
        "TubeName",
    )

    proxy.onChanged(
        obj,
        "TubeProfile",
    )

    assert calls == []


def test_execute_does_not_rebuild_bent_tube_during_transaction_replay():
    document = FakeDocument(
        restoring=True
    )
    obj = FakeObject(
        document
    )
    proxy = make_proxy()

    calls = []

    proxy._linked_start_node_changed = (
        lambda target: calls.append(
            (
                "start-check",
                target,
            )
        )
        or True
    )
    proxy._joint_link_geometry_changed = (
        lambda target: calls.append(
            (
                "joint-check",
                target,
            )
        )
        or True
    )
    proxy.update_shape = (
        lambda target: calls.append(
            (
                "shape",
                target,
            )
        )
    )
    proxy._update_label = (
        lambda target: calls.append(
            (
                "label",
                target,
            )
        )
    )

    proxy.execute(
        obj
    )

    assert calls == []
