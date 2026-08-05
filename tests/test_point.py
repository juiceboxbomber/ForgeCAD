from forgecad.geometry import Point3D, Vector3D


def test_vector_between_points():
    a = Point3D(1, 2, 3)
    b = Point3D(4, 6, 3)

    v = a.vector_to(b)

    assert v == Vector3D(3, 4, 0)


def test_translate_point():
    p = Point3D(1, 2, 3)

    moved = p.translate(Vector3D(10, 20, 30))

    assert moved == Point3D(11, 22, 33)
    