from __future__ import annotations

import ast

from lsprotocol import types

from src.parser.analysis import parse
from src.parser.preprocessor import Region


def get_symbols(source: str, uri: str = "") -> list[types.DocumentSymbol]:
    result = parse(source, uri)
    symbols: list[types.DocumentSymbol] = []

    for region, tree in result.trees:
        for node in ast.iter_child_nodes(tree):
            sym = _node_to_symbol(node, region)
            if sym:
                symbols.append(sym)

    return symbols


def _node_to_symbol(node: ast.AST, region: Region) -> types.DocumentSymbol | None:
    if isinstance(node, ast.FunctionDef):
        line = (node.lineno - 1) + region.line_offset
        end_line = (getattr(node, "end_lineno", node.lineno) - 1) + region.line_offset
        r = _range(line, node.col_offset, end_line, getattr(node, "end_col_offset", 0))
        name_range = _range(line, node.col_offset, line, node.col_offset + len(node.name))
        children: list[types.DocumentSymbol] = []
        for child in ast.iter_child_nodes(node):
            child_sym = _node_to_symbol(child, region)
            if child_sym:
                children.append(child_sym)
        return types.DocumentSymbol(
            name=node.name,
            kind=types.SymbolKind.Function,
            range=r,
            selection_range=name_range,
            children=children,
        )
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                line = (target.lineno - 1) + region.line_offset
                r = _range(line, target.col_offset, line, target.col_offset + len(target.id))
                return types.DocumentSymbol(
                    name=target.id,
                    kind=types.SymbolKind.Variable,
                    range=r,
                    selection_range=r,
                )
    return None


def _range(start_line: int, start_col: int, end_line: int, end_col: int) -> types.Range:
    return types.Range(
        start=types.Position(line=start_line, character=start_col),
        end=types.Position(line=end_line, character=end_col),
    )
