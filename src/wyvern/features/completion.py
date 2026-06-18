from __future__ import annotations

from lsprotocol import types

from wyvern.builtins import BUILTINS, BuiltinInfo
from wyvern.parser.analysis import parse


_KIND_MAP: dict[str, types.CompletionItemKind] = {
    "function": types.CompletionItemKind.Function,
    "class": types.CompletionItemKind.Class,
    "variable": types.CompletionItemKind.Variable,
    "constant": types.CompletionItemKind.Constant,
}

_USER_KIND_MAP: dict[str, types.CompletionItemKind] = {
    "function": types.CompletionItemKind.Function,
    "variable": types.CompletionItemKind.Variable,
    "argument": types.CompletionItemKind.Variable,
    "for_target": types.CompletionItemKind.Variable,
}


def get_completions(source: str, position: types.Position) -> types.CompletionList:
    items: list[types.CompletionItem] = []

    # Built-in completions
    for name, info in BUILTINS.items():
        items.append(_builtin_item(name, info))

    # User-defined symbol completions
    result = parse(source)
    for name, defn in result.definitions.items():
        if name not in BUILTINS:
            items.append(
                types.CompletionItem(
                    label=name,
                    kind=_USER_KIND_MAP.get(defn.kind, types.CompletionItemKind.Variable),
                )
            )

    return types.CompletionList(is_incomplete=False, items=items)


def _builtin_item(name: str, info: BuiltinInfo) -> types.CompletionItem:
    insert_text = name
    insert_format = types.InsertTextFormat.PlainText

    # For functions, add a snippet with parameter placeholders
    if info.kind == "function" and info.params:
        placeholders = ", ".join(
            f"${{{i + 1}:{p}}}" for i, p in enumerate(info.params)
        )
        insert_text = f"{name}({placeholders})"
        insert_format = types.InsertTextFormat.Snippet

    return types.CompletionItem(
        label=name,
        kind=_KIND_MAP.get(info.kind, types.CompletionItemKind.Text),
        detail=info.signature,
        documentation=types.MarkupContent(
            kind=types.MarkupKind.Markdown, value=info.doc
        ),
        insert_text=insert_text,
        insert_text_format=insert_format,
    )
