from __future__ import annotations

import re

from lsprotocol import types

from wyvern.builtins import BUILTINS, CLASS_REGISTRY, find_member_type, unwrap_type
from wyvern.features.completion import _normalize_calls
from wyvern.parser.analysis import DefinitionInfo, find_name_at, parse
from wyvern.parser.gvar_resolver import resolve_gvar_definitions


def get_hover(
    source: str,
    position: types.Position,
    workspace_paths: list[str] | None = None,
) -> types.Hover | None:
    result = parse(source)

    # Try attribute hover first (e.g. hovering "cc_str" in "character().cc_str")
    attr_hover = _get_attribute_hover(
        source, position, result.using_imports, workspace_paths or [], result.inferred_types
    )
    if attr_hover is not None:
        return attr_hover

    name = find_name_at(source, position)
    if not name:
        return None

    # Check built-in registry
    if name in BUILTINS:
        info = BUILTINS[name]
        md = f"```draconic\n{info.signature}\n```\n\n{info.doc}"
        if info.return_type:
            md += f"\n\n**Returns:** `{info.return_type}`"
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
        )

    # Check CLASS_REGISTRY (hovering a type name itself)
    if name in CLASS_REGISTRY:
        cls_info = CLASS_REGISTRY[name]
        md = f"```draconic\n(class) {name}\n```\n\n{cls_info.doc}"
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
        )

    # Fall back to user-defined symbols
    if name in result.definitions:
        defn = result.definitions[name]
        kind_label = {
            "function": "function",
            "variable": "variable",
            "argument": "parameter",
            "for_target": "variable",
        }[defn.kind]
        md = f"```draconic\n({kind_label}) {name}\n```\n\nDefined at line {defn.line + 1}."
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
        )

    return None


def _get_attribute_hover(
    source: str,
    position: types.Position,
    using_imports: dict[str, str],
    workspace_paths: list[str],
    inferred_types: dict[str, str] | None = None,
) -> types.Hover | None:
    """
    If the cursor is on an attribute name (e.g. `cc_str` in `character().cc_str`),
    resolve the owner type and return hover info for that member.
    """
    lines = source.splitlines()
    if position.line >= len(lines):
        return None
    line = lines[position.line]
    col = position.character

    # Find the word under the cursor
    word_match = re.search(r'\b(\w+)\b', line)
    # Walk all word matches to find the one under the cursor
    member_name: str | None = None
    for m in re.finditer(r'\b(\w+)\b', line):
        if m.start() <= col <= m.end():
            member_name = m.group(1)
            break
    if not member_name:
        return None

    # Check if there is a dot immediately before this word
    # e.g. "character().cc_str" or "ctx.author.name"
    dot_pos = line.rfind(".", 0, line.find(member_name, max(0, col - len(member_name))))
    if dot_pos < 0:
        return None

    # Extract the chain before the dot
    prefix_up_to_dot = line[: dot_pos + 1]
    m2 = re.search(r'((?:\w+(?:\(\))?\.)*\w+(?:\(\))?)\.$', prefix_up_to_dot)
    if not m2:
        return None

    chain_str = m2.group(1)
    parts = [p.rstrip("()") for p in chain_str.split(".")]

    # If the chain root is a using-imported gvar name, resolve the member from
    # the gvar's own definitions (e.g. hovering "write" in "Log.write(").
    if parts[0] in using_imports and len(parts) == 1:
        uuid = using_imports[parts[0]]
        defs = resolve_gvar_definitions(uuid, workspace_paths)
        defn = defs.get(member_name)
        if defn is None:
            return None
        return _gvar_def_hover(member_name, defn)

    # Resolve type of the chain before the dot
    type_name = _resolve_chain(parts, inferred_types or {})
    if type_name is None:
        return None

    # Find the member in that type
    cls_info = CLASS_REGISTRY.get(type_name)
    if cls_info is None:
        return None

    member_info = _find_member(cls_info, member_name)
    if member_info is None:
        return None

    md = f"```draconic\n{member_info.signature}\n```\n\n{member_info.doc}"
    if member_info.return_type:
        md += f"\n\n**Returns:** `{member_info.return_type}`"
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
    )


def get_signature_help(
    source: str,
    position: types.Position,
    workspace_paths: list[str] | None = None,
) -> types.SignatureHelp | None:
    """Return parameter-hint info for the call the cursor is currently inside."""
    lines = source.splitlines()
    if position.line >= len(lines):
        return None
    prefix = lines[position.line][: position.character]

    # Find the innermost unclosed "(" — the call the cursor is currently inside.
    # Brackets before it are guaranteed balanced, so it's safe to normalize that part.
    depth = 0
    open_idx = None
    open_char = None
    for i in range(len(prefix) - 1, -1, -1):
        ch = prefix[i]
        if ch in ")]}":
            depth += 1
        elif ch in "([{":
            if depth == 0:
                open_idx, open_char = i, ch
                break
            depth -= 1
    if open_idx is None or open_char != "(":
        return None

    normalized = _normalize_calls(prefix[:open_idx])
    m = re.search(r'((?:\w+(?:\(\))?\.)*\w+)$', normalized)
    if not m:
        return None
    parts = [p.rstrip("()") for p in m.group(1).split(".")]
    active_parameter = _count_top_level_commas(prefix[open_idx + 1 :])

    result = parse(source)
    resolved = _resolve_signature(
        parts, result.using_imports, workspace_paths or [], result.inferred_types
    )
    if resolved is None:
        return None
    label, params, doc = resolved

    signature = types.SignatureInformation(
        label=label,
        documentation=types.MarkupContent(kind=types.MarkupKind.Markdown, value=doc)
        if doc
        else None,
        parameters=[types.ParameterInformation(label=p) for p in params],
    )
    return types.SignatureHelp(
        signatures=[signature], active_signature=0, active_parameter=active_parameter
    )


def _count_top_level_commas(s: str) -> int:
    """Count commas not nested inside any bracket, string, or char literal."""
    depth = 0
    count = 0
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            count += 1
    return count


def _resolve_signature(
    parts: list[str],
    using_imports: dict[str, str],
    workspace_paths: list[str],
    inferred_types: dict[str, str] | None = None,
) -> tuple[str, list[str], str] | None:
    """Resolve a dotted call chain (root stripped of its own trailing call) to
    (label, params, doc) for the function being called, or None."""
    if not parts:
        return None

    if len(parts) == 1:
        root = parts[0]
        if root in BUILTINS and BUILTINS[root].kind == "function":
            info = BUILTINS[root]
            return info.signature, info.params or [], info.doc
        return None

    root, member_name = parts[0], parts[-1]

    if root in using_imports and len(parts) == 2:
        defs = resolve_gvar_definitions(using_imports[root], workspace_paths)
        defn = defs.get(member_name)
        if defn is None or defn.kind != "function":
            return None
        return f"{member_name}({', '.join(defn.params)})", defn.params, defn.doc

    type_name = _resolve_chain(parts[:-1], inferred_types or {})
    if type_name is None:
        return None
    cls_info = CLASS_REGISTRY.get(type_name)
    if cls_info is None:
        return None
    member_info = _find_member(cls_info, member_name)
    if member_info is None or member_info.kind != "function":
        return None
    return member_info.signature, member_info.params or [], member_info.doc


def _gvar_def_hover(name: str, defn: DefinitionInfo) -> types.Hover:
    if defn.kind == "function":
        signature = f"{name}({', '.join(defn.params)})"
        md = f"```draconic\n{signature}\n```"
        if defn.doc:
            md += f"\n\n{defn.doc}"
    else:
        md = f"```draconic\n({defn.kind}) {name}\n```"
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=md)
    )


def _resolve_chain(parts: list[str], inferred_types: dict[str, str]) -> str | None:
    """Walk a dotted identifier chain and return the final resolved type, or None."""
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

    for part in parts[1:]:
        member_type = find_member_type(current_type, part)
        if member_type is None:
            return None
        current_type = member_type

    return current_type if current_type in CLASS_REGISTRY else None


def _find_member(cls_info, name: str):
    """Return the BuiltinInfo for a named member in a ClassInfo, following bases."""
    visited: set[str] = set()

    def _search(info):
        if info.name in visited:
            return None
        visited.add(info.name)
        for m in info.methods + info.properties:
            if m.name == name:
                return m
        for base_name in info.bases:
            base = CLASS_REGISTRY.get(base_name)
            if base:
                result = _search(base)
                if result is not None:
                    return result
        return None

    return _search(cls_info)
