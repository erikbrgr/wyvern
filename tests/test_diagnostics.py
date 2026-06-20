import ast

from src.features.diagnostics import _lint_tree, _syntax_error_diagnostic
from src.parser.analysis import parse
from src.parser.preprocessor import Region


def _region(line_offset: int = 0) -> Region:
    return Region(code="", line_offset=line_offset)


def test_import_forbidden():
    tree = ast.parse("import os\nx = 1")
    diags = _lint_tree(tree, _region())
    assert len(diags) == 1
    assert "import" in diags[0].message.lower()
    assert diags[0].range.start.line == 0


def test_class_forbidden():
    tree = ast.parse("class Foo:\n    pass")
    diags = _lint_tree(tree, _region())
    assert any("class" in d.message.lower() for d in diags)


def test_raise_forbidden():
    tree = ast.parse("raise ValueError('oops')")
    diags = _lint_tree(tree, _region())
    assert any("raise" in d.message.lower() for d in diags)
    assert any("err(" in d.message for d in diags)


def test_line_offset_applied():
    tree = ast.parse("import os")
    diags = _lint_tree(tree, _region(line_offset=5))
    assert diags[0].range.start.line == 5


def test_syntax_error_from_alias_fixture():
    with open("tests/fixtures/syntax_error.alias") as f:
        source = f.read()
    result = parse(source, "syntax_error.alias")
    assert len(result.syntax_errors) == 1
    region, err = result.syntax_errors[0]
    diag = _syntax_error_diagnostic(err, region)
    assert diag.range.start.line >= 1  # error is inside <drac2> block


def test_forbidden_nodes_from_alias_fixture():
    with open("tests/fixtures/forbidden.alias") as f:
        source = f.read()
    result = parse(source, "forbidden.alias")
    assert len(result.syntax_errors) == 0
    all_diags: list = []
    from src.features.diagnostics import _lint_tree
    for region, tree in result.trees:
        all_diags.extend(_lint_tree(tree, region))
    messages = [d.message for d in all_diags]
    assert any("import" in m.lower() for m in messages)
    assert any("class" in m.lower() for m in messages)


def test_valid_alias_no_diagnostics():
    with open("tests/fixtures/simple.alias") as f:
        source = f.read()
    result = parse(source, "simple.alias")
    assert len(result.syntax_errors) == 0
    from src.features.diagnostics import _lint_tree
    diags = []
    for region, tree in result.trees:
        diags.extend(_lint_tree(tree, region))
    assert diags == []
