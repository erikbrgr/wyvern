from __future__ import annotations

import re

from lsprotocol import types

from src.builtins import BUILTINS, CLASS_REGISTRY
from src.parser.analysis import find_name_at, parse


def get_hover(source: str, position: types.Position) -> types.Hover | None:
    # Try attribute hover first (e.g. hovering "cc_str" in "character().cc_str")
    attr_hover = _get_attribute_hover(source, position)
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
    result = parse(source)
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


def _get_attribute_hover(source: str, position: types.Position) -> types.Hover | None:
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

    # Resolve type of the chain before the dot
    type_name = _resolve_chain(parts)
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


def _resolve_chain(parts: list[str]) -> str | None:
    """Walk a dotted identifier chain and return the final resolved type, or None."""
    if not parts:
        return None

    root = parts[0]
    if root not in BUILTINS:
        return None
    current_type = BUILTINS[root].return_type
    if not current_type:
        return None
    current_type = current_type.split("|")[0].strip()

    for part in parts[1:]:
        cls_info = CLASS_REGISTRY.get(current_type)
        if cls_info is None:
            return None
        member_type = _find_member_return_type(cls_info, part)
        if member_type is None:
            return None
        current_type = member_type.split("|")[0].strip()

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


def _find_member_return_type(cls_info, name: str) -> str | None:
    member = _find_member(cls_info, name)
    return member.return_type if member else None
