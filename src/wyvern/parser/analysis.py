"""
AST parsing and symbol table construction for Draconic source files.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Literal

from lsprotocol import types

from wyvern.parser.preprocessor import Region, extract_regions


@dataclass
class DefinitionInfo:
    name: str
    kind: Literal["function", "variable", "argument", "for_target"]
    line: int  # 0-indexed, in original document
    col: int
    end_line: int
    end_col: int


@dataclass
class ParseResult:
    regions: list[Region] = field(default_factory=list)
    trees: list[tuple[Region, ast.Module]] = field(default_factory=list)
    syntax_errors: list[tuple[Region, SyntaxError]] = field(default_factory=list)
    definitions: dict[str, DefinitionInfo] = field(default_factory=dict)


def parse(source: str, uri: str = "") -> ParseResult:
    result = ParseResult()
    result.regions = extract_regions(source, uri)

    for region in result.regions:
        try:
            tree = ast.parse(region.code, mode="exec")
            result.trees.append((region, tree))
            _collect_definitions(tree, region, result.definitions)
        except SyntaxError as e:
            result.syntax_errors.append((region, e))

    return result


def _collect_definitions(
    tree: ast.AST, region: Region, defs: dict[str, DefinitionInfo]
) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            _add_def(defs, node.name, "function", node, region)
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                _add_def_at(defs, arg.arg, "argument", arg.lineno, arg.col_offset, region)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                _collect_assign_targets(target, defs, region)
        elif isinstance(node, ast.AugAssign):
            _collect_assign_targets(node.target, defs, region)
        elif isinstance(node, ast.NamedExpr):
            _add_def_at(defs, node.target.id, "variable", node.lineno, node.col_offset, region)
        elif isinstance(node, ast.For):
            _collect_assign_targets(node.target, defs, region)


def _collect_assign_targets(
    target: ast.expr, defs: dict[str, DefinitionInfo], region: Region
) -> None:
    if isinstance(target, ast.Name):
        _add_def_at(defs, target.id, "variable", target.lineno, target.col_offset, region)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            _collect_assign_targets(elt, defs, region)
    elif isinstance(target, ast.Starred):
        _collect_assign_targets(target.value, defs, region)


def _add_def(
    defs: dict[str, DefinitionInfo],
    name: str,
    kind: Literal["function", "variable", "argument", "for_target"],
    node: ast.stmt,
    region: Region,
) -> None:
    line = (node.lineno - 1) + region.line_offset
    end_line = (getattr(node, "end_lineno", node.lineno) - 1) + region.line_offset
    col = node.col_offset + (region.col_offset if node.lineno == 1 else 0)
    end_col = getattr(node, "end_col_offset", col + len(name))
    defs[name] = DefinitionInfo(name, kind, line, col, end_line, end_col)


def _add_def_at(
    defs: dict[str, DefinitionInfo],
    name: str,
    kind: Literal["function", "variable", "argument", "for_target"],
    lineno: int,
    col_offset: int,
    region: Region,
) -> None:
    line = (lineno - 1) + region.line_offset
    col = col_offset + (region.col_offset if lineno == 1 else 0)
    defs[name] = DefinitionInfo(name, kind, line, col, line, col + len(name))


def find_name_at(source: str, position: types.Position) -> str | None:
    """Extract the identifier word at the given LSP position."""
    lines = source.splitlines()
    if position.line >= len(lines):
        return None
    line = lines[position.line]
    col = position.character
    start = col
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
        start -= 1
    end = col
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1
    word = line[start:end]
    return word if word else None
