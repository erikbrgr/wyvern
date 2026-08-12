import ast

from lsprotocol import types

from wyvern.features.diagnostics import _lint_tree, _syntax_error_diagnostic, publish
from wyvern.parser.analysis import parse
from wyvern.parser.preprocessor import Region


def _region(line_offset: int = 0) -> Region:
    return Region(code="", line_offset=line_offset)


class _FakeLanguageServer:
    """Minimal stand-in for pygls's LanguageServer, capturing published diagnostics."""

    def __init__(self):
        self.published = None

    def text_document_publish_diagnostics(self, params):
        self.published = params.diagnostics


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
    from wyvern.features.diagnostics import _lint_tree
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
    from wyvern.features.diagnostics import _lint_tree
    diags = []
    for region, tree in result.trees:
        diags.extend(_lint_tree(tree, region))
    assert diags == []


def test_usings_dir_gvar_suppresses_diagnostics():
    ls = _FakeLanguageServer()
    source = "import os\nclass Foo:\n    pass\n"  # would normally trigger diagnostics
    publish(ls, "file:///project/.wyvern/usings/abc123.gvar", source)
    assert ls.published == []


def test_regular_gvar_still_gets_diagnostics():
    ls = _FakeLanguageServer()
    source = "import os\n"
    publish(ls, "file:///project/gvars/abc123.gvar", source)
    assert len(ls.published) == 1


def test_unknown_leading_command_flagged():
    from wyvern.features.diagnostics import _check_leading_command

    diags = _check_leading_command('embdd\n<drac2>\nx = 1\n</drac2>\n', "test.alias")
    assert len(diags) == 1
    assert "embdd" in diags[0].message
    assert diags[0].severity == types.DiagnosticSeverity.Warning


def test_known_leading_commands_not_flagged():
    from wyvern.features.diagnostics import _check_leading_command

    for word in ("embed", "multiline", "svar", "cast"):
        assert _check_leading_command(f'{word}\n<drac2>\nx = 1\n</drac2>\n', "test.alias") == []


def test_no_leading_text_not_flagged():
    from wyvern.features.diagnostics import _check_leading_command

    assert _check_leading_command('<drac2>\nx = 1\n</drac2>\n', "test.alias") == []


def test_leading_command_check_skipped_for_gvar():
    from wyvern.features.diagnostics import _check_leading_command

    assert _check_leading_command('embdd\nx = 1\n{{x}}\n', "test.gvar") == []


def test_unexpected_indent_does_not_produce_negative_column():
    """IndentationError sets end_offset to -1 (not None) when unavailable;
    a plain `error.end_offset or col + 1` would pass -1 through, and
    lsprotocol rejects a negative Position.character."""
    try:
        ast.parse("x = 1\n  y = 2")
    except SyntaxError as e:
        error = e
    diag = _syntax_error_diagnostic(error, _region())
    assert diag.range.start.character >= 0
    assert diag.range.end.character >= 0
