"""Tests for deferred member Shape refresh during transaction replay."""

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


def import_member_module():
    previous_modules = {
        name: sys.modules.get(
            name
        )
        for name in (
            "FreeCAD",
            "Part",
        )
    }

    fake_freecad = types.ModuleType(
        "FreeCAD"
    )

    fake_freecad.Vector = (
        FakeVector
    )

    fake_freecad.getDocument = (
        lambda name: None
    )

    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad

    sys.modules[
        "Part"
    ] = fake_part

    try:
        module = importlib.import_module(
            "forgecad.adapters.freecad.member_object"
        )

    finally:
        for (
            module_name,
            previous_module,
        ) in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(
                    module_name,
                    None,
                )
            else:
                sys.modules[
                    module_name
                ] = previous_module

    return module


member_object = (
    import_member_module()
)


class FakeDocument:
    def __init__(
        self,
        restoring,
    ):
        self.Name = "Doc"
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
        self.Name = "Member"


def make_proxy():
    proxy = object.__new__(
        member_object.TubeMemberProxy
    )

    proxy._ready = True
    proxy._updating = False
    proxy._replay_refresh_pending = False

    return proxy


def test_execute_defers_shape_rebuild_during_transaction_replay():
    document = FakeDocument(
        restoring=True
    )

    obj = FakeObject(
        document
    )

    proxy = make_proxy()

    obj.Proxy = proxy

    calls = []

    original_schedule = (
        member_object.schedule_member_refresh_after_transaction
    )

    member_object.schedule_member_refresh_after_transaction = (
        lambda target: calls.append(
            (
                "schedule",
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

    try:
        proxy.execute(
            obj
        )

    finally:
        member_object.schedule_member_refresh_after_transaction = (
            original_schedule
        )

    assert calls == [
        (
            "schedule",
            obj,
        ),
    ]


def test_execute_rebuilds_immediately_outside_transaction_replay():
    document = FakeDocument(
        restoring=False
    )

    obj = FakeObject(
        document
    )

    proxy = make_proxy()

    obj.Proxy = proxy

    calls = []

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

    assert calls == [
        (
            "shape",
            obj,
        ),
        (
            "label",
            obj,
        ),
    ]
