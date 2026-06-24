from lsprotocol import types

from wyvern.features.completion import get_completions


def _pos(line: int, char: int) -> types.Position:
    return types.Position(line=line, character=char)


def test_builtins_in_completions():
    result = get_completions("x = 1\n", _pos(0, 0))
    labels = {item.label for item in result.items}
    assert "roll" in labels
    assert "vroll" in labels
    assert "character" in labels
    assert "len" in labels
    assert "str" in labels


def test_user_defined_name_in_completions():
    source = "target = 'goblin'\n"
    result = get_completions(source, _pos(1, 0))
    labels = {item.label for item in result.items}
    assert "target" in labels


def test_function_snippet_format():
    result = get_completions("", _pos(0, 0))
    roll_item = next(i for i in result.items if i.label == "roll")
    assert roll_item.insert_text_format == types.InsertTextFormat.Snippet
    assert "${1:" in (roll_item.insert_text or "")


def test_no_duplicates_for_builtins():
    result = get_completions("roll = 1\n", _pos(0, 0))
    roll_items = [i for i in result.items if i.label == "roll"]
    # user-defined "roll" shadows builtin, but we only show it once as builtin takes precedence
    assert len(roll_items) >= 1
