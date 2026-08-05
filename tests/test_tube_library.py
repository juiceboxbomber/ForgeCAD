import pytest

from forgecad.fabrication import TubeLibrary, TubeProfile


def test_add_profile():
    library = TubeLibrary()
    profile = TubeProfile(44.45, 3.048)

    library.add("1.750 x .120 DOM", profile)

    assert library.get("1.750 x .120 DOM") is profile
    assert library.names == ("1.750 x .120 DOM",)


def test_first_profile_becomes_active():
    library = TubeLibrary()
    profile = TubeProfile(44.45, 3.048)

    library.add("Main Tube", profile)

    assert library.active_profile is profile


def test_change_active_profile():
    library = TubeLibrary()

    main_tube = TubeProfile(44.45, 3.048)
    brace_tube = TubeProfile(31.75, 2.413)

    library.add("Main Tube", main_tube)
    library.add("Brace Tube", brace_tube)
    library.set_active("Brace Tube")

    assert library.active_profile is brace_tube
    assert library.active_name == "Brace Tube"


def test_duplicate_name_is_rejected():
    library = TubeLibrary()
    library.add("Main Tube", TubeProfile(44.45, 3.048))

    with pytest.raises(ValueError):
        library.add("Main Tube", TubeProfile(38.1, 3.048))


def test_unknown_profile_is_rejected():
    library = TubeLibrary()

    with pytest.raises(KeyError):
        library.set_active("Missing")


def test_empty_library_has_no_active_profile():
    library = TubeLibrary()

    with pytest.raises(RuntimeError):
        _ = library.active_profile
        