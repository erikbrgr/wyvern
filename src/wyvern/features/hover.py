from __future__ import annotations

from lsprotocol import types

from wyvern.builtins import BUILTINS
from wyvern.parser.analysis import find_name_at, parse


def get_hover(source: str, position: types.Position) -> types.Hover | None:
    name = find_name_at(source, position)
    if not name:
        return None

    # Check built-in registry first
    if name in BUILTINS:
        info = BUILTINS[name]
        md = f"```draconic\n{info.signature}\n```\n\n{info.doc}"
        if info.return_type:
            md += f"\n\n**Returns:** `{info.return_type}`"
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
        )

    # Fall back to user-defined symbols
    result = parse(source)
    if name in result.definitions:
        defn = result.definitions[name]
        kind_label = {"function": "function", "variable": "variable", "argument": "parameter", "for_target": "variable"}[defn.kind]
        md = f"```draconic\n({kind_label}) {name}\n```\n\nDefined at line {defn.line + 1}."
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
        )

    return None
