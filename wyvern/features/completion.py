from __future__ import annotations

import re

from lsprotocol import types

from wyvern.builtins import BUILTINS, CLASS_REGISTRY, BuiltinInfo, find_member_type, unwrap_type
from wyvern.parser.analysis import DefinitionInfo, parse
from wyvern.parser.gvar_resolver import resolve_gvar_definitions


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


def get_completions(
    source: str,
    position: types.Position,
    workspace_paths: list[str] | None = None,
) -> types.CompletionList:
    lines = source.splitlines()
    line_text = lines[position.line] if position.line < len(lines) else ""
    prefix = line_text[: position.character]

    result = parse(source)

    # Check for attribute access (e.g. "character().", "ctx.author.", "Hunt.")
    members = _get_member_completions(
        prefix, result.using_imports, workspace_paths or [], result.inferred_types
    )
    if members is not None:
        return types.CompletionList(is_incomplete=False, items=members)

    items: list[types.CompletionItem] = []

    # Built-in completions
    for name, info in BUILTINS.items():
        items.append(_builtin_item(name, info))

    # User-defined symbol completions
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


def _get_member_completions(
    prefix: str,
    using_imports: dict[str, str],
    workspace_paths: list[str],
    inferred_types: dict[str, str] | None = None,
) -> list[types.CompletionItem] | None:
    """
    If `prefix` ends with an attribute-access chain, return completion items
    for the final type's members.  Returns None if no attribute access is detected.

    Handles single-level:   character().      ->  AliasCharacter members
    Handles two-level:      ctx.author.       ->  AliasAuthor members
    Handles call args:      list(items).      ->  list members
    Handles chained args:   character().cc(n). -> AliasCustomCounter members
    Handles using imports:  Hunt.             ->  symbols from the Hunt gvar
    Handles inferred vars:  char = character(); char. -> AliasCharacter members
    """
    normalized = _normalize_calls(prefix)
    m = re.search(r'((?:\w+(?:\(\))?\.)*\w+(?:\(\))?)\.$', normalized)
    if not m:
        return None

    chain_str = m.group(1)
    parts = [p.rstrip("()") for p in chain_str.split(".")]
    root = parts[0]

    # If the root is a using-imported gvar name, resolve its symbols directly.
    # Return [] (not None) when gvar isn't found so we don't fall through to the
    # default built-in list — an empty list is the right UX for an unloaded gvar.
    if root in using_imports and len(parts) == 1:
        uuid = using_imports[root]
        defs = resolve_gvar_definitions(uuid, workspace_paths)
        return [_gvar_def_item(name, info) for name, info in defs.items()]

    type_name = _resolve_chain(parts, inferred_types or {})
    if type_name is None:
        return None

    return _class_completion_items(type_name)


def _resolve_chain(parts: list[str], inferred_types: dict[str, str]) -> str | None:
    """Walk a dotted chain and return the final resolved type name, or None."""
    if not parts:
        return None

    # Resolve the first identifier from global BUILTINS, falling back to a
    # variable's inferred type (e.g. `char` after `char = character()`).
    root = parts[0]
    if root in BUILTINS:
        current_type = BUILTINS[root].return_type
        if not current_type:
            return None
        current_type = unwrap_type(current_type)
    elif root in inferred_types:
        current_type = inferred_types[root]
    else:
        return None

    # Walk subsequent parts using CLASS_REGISTRY member return types
    for part in parts[1:]:
        member_type = find_member_type(current_type, part)
        if member_type is None:
            return None
        current_type = member_type

    return current_type if current_type in CLASS_REGISTRY else None


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


def _gvar_def_item(name: str, info: DefinitionInfo) -> types.CompletionItem:
    kind = (
        types.CompletionItemKind.Function
        if info.kind == "function"
        else types.CompletionItemKind.Variable
    )
    insert_text = name
    insert_format = types.InsertTextFormat.PlainText
    detail = f"(gvar) {info.kind}"

    if info.kind == "function":
        detail = f"(gvar) {name}({', '.join(info.params)})"
        if info.params:
            placeholders = ", ".join(
                f"${{{i + 1}:{p}}}" for i, p in enumerate(info.params)
            )
            insert_text = f"{name}({placeholders})"
            insert_format = types.InsertTextFormat.Snippet

    return types.CompletionItem(
        label=name,
        kind=kind,
        detail=detail,
        documentation=types.MarkupContent(kind=types.MarkupKind.Markdown, value=info.doc)
        if info.doc
        else None,
        insert_text=insert_text,
        insert_text_format=insert_format,
    )


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
