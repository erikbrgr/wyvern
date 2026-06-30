from __future__ import annotations

import re

from lsprotocol import types

from wyvern.builtins import BUILTINS, CLASS_REGISTRY, BuiltinInfo
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
    lines = source.splitlines()
    line_text = lines[position.line] if position.line < len(lines) else ""
    prefix = line_text[: position.character]

    # Check for attribute access (e.g. "character().", "ctx.author.", "args.")
    members = _get_member_completions(prefix)
    if members is not None:
        return types.CompletionList(is_incomplete=False, items=members)

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


def _normalize_calls(prefix: str) -> str:
    """Collapse function argument lists to () so the chain regex handles non-empty args.

    list(level_mult).    ->  list().
    character().cc("x"). ->  character().cc().
    """
    result = []
    depth = 0
    for ch in prefix:
        if ch == "(":
            depth += 1
            result.append("(")
        elif ch == ")":
            if depth > 0:
                depth -= 1
            if depth == 0:
                result.append(")")
        elif depth == 0:
            result.append(ch)
    return "".join(result)


def _get_member_completions(prefix: str) -> list[types.CompletionItem] | None:
    """
    If `prefix` ends with an attribute-access chain, return completion items
    for the final type's members.  Returns None if no attribute access is detected.

    Handles single-level:   character().      ->  AliasCharacter members
    Handles two-level:      ctx.author.       ->  AliasAuthor members
    Handles call args:      list(items).      ->  list members
    Handles chained args:   character().cc(n). -> AliasCustomCounter members
    """
    normalized = _normalize_calls(prefix)
    m = re.search(r'((?:\w+(?:\(\))?\.)*\w+(?:\(\))?)\.$', normalized)
    if not m:
        return None

    chain_str = m.group(1)
    parts = [p.rstrip("()") for p in chain_str.split(".")]

    type_name = _resolve_chain(parts)
    if type_name is None:
        return None

    return _class_completion_items(type_name)


def _unwrap_type(type_str: str) -> str:
    """Strip '| None' and unwrap list[X] → X so list properties chain correctly."""
    t = type_str.split("|")[0].strip()
    if t.startswith("list[") and t.endswith("]"):
        t = t[5:-1]
    return t


def _resolve_chain(parts: list[str]) -> str | None:
    """Walk a dotted chain and return the final resolved type name, or None."""
    if not parts:
        return None

    # Resolve the first identifier from global BUILTINS
    root = parts[0]
    if root not in BUILTINS:
        return None
    current_type = BUILTINS[root].return_type
    if not current_type:
        return None
    current_type = _unwrap_type(current_type)

    # Walk subsequent parts using CLASS_REGISTRY member return types
    for part in parts[1:]:
        cls_info = CLASS_REGISTRY.get(current_type)
        if cls_info is None:
            return None
        member_type = _find_member_type(cls_info, part)
        if member_type is None:
            return None
        current_type = _unwrap_type(member_type)

    return current_type if current_type in CLASS_REGISTRY else None


def _find_member_type(cls_info, name: str) -> str | None:
    """Return the return_type of a named method or property in a ClassInfo, following bases."""
    from wyvern.builtins.registry import ClassInfo
    visited: set[str] = set()

    def _search(info: ClassInfo) -> str | None:
        if info.name in visited:
            return None
        visited.add(info.name)

        for m in info.methods + info.properties:
            if m.name == name:
                return m.return_type

        for base_name in info.bases:
            base = CLASS_REGISTRY.get(base_name)
            if base:
                result = _search(base)
                if result is not None:
                    return result
        return None

    return _search(cls_info)


def _class_completion_items(type_name: str) -> list[types.CompletionItem]:
    """Return completion items for all members of `type_name`, including inherited ones."""
    items: list[types.CompletionItem] = []
    visited: set[str] = set()
    seen_names: set[str] = set()

    def _collect(name: str) -> None:
        if name in visited or name not in CLASS_REGISTRY:
            return
        visited.add(name)
        cls_info = CLASS_REGISTRY[name]
        for member in cls_info.methods + cls_info.properties:
            if member.name not in seen_names:
                seen_names.add(member.name)
                items.append(_builtin_item(member.name, member))
        for base in cls_info.bases:
            _collect(base)
        if cls_info.element_type:
            _collect(cls_info.element_type)

    _collect(type_name)
    return items


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
