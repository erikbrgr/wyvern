from wyvern.parser.preprocessor import extract_regions, _normalize


def test_drac2_extraction():
    source = "!alias foo <drac2>\nx = 1\nreturn x\n</drac2> done"
    regions = extract_regions(source, "foo.alias")
    assert len(regions) == 1
    assert "x = 1" in regions[0].code
    assert regions[0].line_offset == 1  # inner content starts on line after <drac2>


def test_double_brace_extraction():
    source = "Hello {{name}} world"
    regions = extract_regions(source, "foo.alias")
    assert len(regions) == 1
    assert regions[0].code.strip() == "name"


def test_gvar_whole_file():
    source = "x = 1\ny = 2\n"
    regions = extract_regions(source, "vars.gvar")
    assert len(regions) == 1
    assert regions[0].code == source
    assert regions[0].line_offset == 0


def test_normalize_arg_placeholders():
    code = "x = &ARGS&\nn = &1&"
    result = _normalize(code)
    assert "__arg_args__" in result
    assert "__arg_1__" in result
    assert "&" not in result


def test_multiple_drac2_blocks():
    source = "<drac2>\na = 1\n</drac2> text <drac2>\nb = 2\n</drac2>"
    regions = extract_regions(source, "multi.alias")
    assert len(regions) == 2
