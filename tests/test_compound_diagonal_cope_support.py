import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def f(path,name):
    s=(ROOT/path).read_text(encoding="utf-8"); tree=ast.parse(s)
    n=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    lines=s.splitlines(); return "\n".join(lines[n.lineno-1:n.end_lineno])
def test_renderer_three_slots():
    s=f("forgecad/adapters/freecad/renderer.py","configure_cope_specifications")
    assert "idx >= 3" in s or "cope_index >= 3" in s
    assert "configure_start_cope_tertiary" in s and "configure_end_cope_tertiary" in s
def test_member_shape_third_slot_bounded():
    s=f("forgecad/adapters/freecad/member_notch.py","build_member_shape")
    assert "StartCope3TargetMember" in s and "EndCope3TargetMember" in s
    assert "apply_bounded_cope_to_existing_shape" in s
def test_third_links_sync():
    s=f("forgecad/adapters/freecad/member_notch.py","sync_cope_axes_from_target_members")
    assert "StartCope3" in s and "EndCope3" in s
