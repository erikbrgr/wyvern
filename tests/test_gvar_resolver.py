from wyvern.parser.gvar_resolver import is_usings_path


def test_is_usings_path_matches_nested_gvar():
    assert is_usings_path("/home/erik/project/.wyvern/usings/abc123.gvar")


def test_is_usings_path_matches_relative():
    assert is_usings_path(".wyvern/usings/abc123.gvar")


def test_is_usings_path_matches_windows_style():
    assert is_usings_path("C:\\project\\.wyvern\\usings\\abc123.gvar")


def test_is_usings_path_ignores_unrelated_dirs():
    assert not is_usings_path("/home/erik/project/gvars/abc123.gvar")


def test_is_usings_path_requires_both_parts_adjacent():
    assert not is_usings_path("/home/erik/.wyvern/other/usings/abc123.gvar")


def test_is_usings_path_requires_usings_not_just_wyvern():
    assert not is_usings_path("/home/erik/.wyvern/abc123.gvar")
