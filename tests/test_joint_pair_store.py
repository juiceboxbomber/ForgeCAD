"""Isolated tests for selection-first pair persistence writes."""
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "forgecad/adapters/freecad"


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeObject:
    def __init__(self, name):
        self.Name = name
        self.NodeKey = ""
        self.TreatmentMode = ""
        self.ThroughLayoutIDs = ""
        self.ExplicitCopePairs = ""
        self.Label = ""
    def addProperty(self, kind, name, group): setattr(self, name, "")
    def setEditorMode(self, name, mode): pass


class FakeGroup:
    def __init__(self): self.Group = []
    def addObject(self, obj): self.Group.append(obj)


class FakeDocument:
    def __init__(self):
        self.group = FakeGroup()
        self.objects = {"ForgeCADJointTreatments": self.group}
        self.recomputes = 0
    def getObject(self, name): return self.objects.get(name)
    def addObject(self, kind, name):
        obj = FakeObject(name)
        self.objects[name] = obj
        return obj
    def recompute(self): self.recomputes += 1


@pytest.fixture
def store(monkeypatch):
    core = load_file("joint_pair_store_core", SRC / "joint_pair_validation.py")
    def mod(name, **values):
        module = types.ModuleType(name)
        module.__dict__.update(values)
        monkeypatch.setitem(sys.modules, name, module)
    for name in ("forgecad", "forgecad.adapters", "forgecad.adapters.freecad"):
        mod(name)
    mod("forgecad.adapters.freecad.joint_pair_validation", **core.__dict__)
    mod("forgecad.adapters.freecad.document_tree",
        initialize_project_tree=lambda doc: {"Joint Treatments": doc.group})
    return load_file("joint_pair_store_isolated", SRC / "joint_treatment_store.py")


def test_batch_write_preserves_primary_and_other_joint(store):
    doc = FakeDocument()
    store.save_joint_treatment(doc, "node-a", "both_coped", ("a", "b"))
    store.save_joint_treatment(doc, "node-b", "member_through", ("u",))
    before = store.load_joint_treatment(doc, "node-a")
    other = store.load_joint_treatment(doc, "node-b")
    store.replace_joint_cope_pairs(doc, "node-a", (("d", "a"), ("d", "b")))
    assert store.load_joint_treatment(doc, "node-a") == before
    assert store.load_joint_treatment(doc, "node-b") == other
    assert store.load_joint_cope_pairs(doc, "node-a") == (("d", "a"), ("d", "b"))
    assert store.load_joint_cope_pairs(doc, "node-b") == ()
    assert doc.recomputes == 3
    store.replace_joint_cope_pairs(doc, "node-a", (("d", "b"),))
    assert store.load_joint_cope_pairs(doc, "node-a") == (("d", "b"),)
    assert store.load_joint_treatment(doc, "node-a") == before


def test_new_record_defaults_to_auto_without_changing_primary(store):
    doc = FakeDocument()
    store.replace_joint_cope_pairs(doc, "node", (("d", "a"),))
    assert store.load_joint_treatment(doc, "node") == ("auto", ())
    assert store.load_joint_cope_pairs(doc, "node") == (("d", "a"),)


def test_invalid_batch_is_rejected_before_mutation(store):
    doc = FakeDocument()
    store.save_joint_treatment(doc, "node", "both_coped", ("a", "b"))
    before = doc.recomputes
    with pytest.raises(ValueError, match="different"):
        store.replace_joint_cope_pairs(doc, "node", (("a", "a"),))
    assert doc.recomputes == before
    assert store.load_joint_cope_pairs(doc, "node") == ()
    obj = store.find_joint_treatment(doc, "node")
    obj.ExplicitCopePairs = "not json"
    with pytest.raises(ValueError, match="malformed"):
        store.replace_joint_cope_pairs(doc, "node", (("d", "a"),))
    assert obj.ExplicitCopePairs == "not json"
    assert doc.recomputes == before
