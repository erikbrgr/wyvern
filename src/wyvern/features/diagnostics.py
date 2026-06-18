"""
Publishes Draconic diagnostics: syntax errors and use of forbidden Python constructs.
"""
from __future__ import annotations

import ast

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from wyvern.parser.analysis import parse
from wyvern.parser.preprocessor import Region


# AST node types that are not supported in Draconic, with user-friendly messages.
_FORBIDDEN: dict[type[ast.AST], str] = {
    ast.Import: "Draconic does not support `import` statements.",
    ast.ImportFrom: "Draconic does not support `from ... import` statements.",
    ast.ClassDef: "Draconic does not support `class` definitions.",
    ast.AsyncFunctionDef: "Draconic does not support `async def`. Use `def` instead.",
    ast.AsyncFor: "Draconic does not support `async for`.",
    ast.AsyncWith: "Draconic does not support `async with`.",
    ast.With: "Draconic does not support `with` statements.",
    ast.Global: "Draconic does not support `global` declarations.",
    ast.Nonlocal: "Draconic does not support `nonlocal` declarations.",
    ast.Raise: "Draconic does not support `raise`. Use `err(message)` instead.",
    ast.Assert: "Draconic does not support `assert` statements.",
    ast.Delete: "Draconic does not support `del` statements.",
    ast.Yield: "Draconic does not support `yield`.",
    ast.YieldFrom: "Draconic does not support `yield from`.",
    ast.Await: "Draconic does not support `await`.",
}


def publish(ls: LanguageServer, uri: str, source: str) -> None:
    result = parse(source, uri)
    diagnostics: list[types.Diagnostic] = []

    for region, error in result.syntax_errors:
        diagnostics.append(_syntax_error_diagnostic(error, region))

    for region, tree in result.trees:
        diagnostics.extend(_lint_tree(tree, region))

    ls.publish_diagnostics(uri, diagnostics)


def _syntax_error_diagnostic(error: SyntaxError, region: Region) -> types.Diagnostic:
    lineno = (error.lineno or 1) - 1 + region.line_offset
    end_lineno = (error.end_lineno or error.lineno or 1) - 1 + region.line_offset
    col = error.offset or 0
    end_col = error.end_offset or col + 1
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=lineno, character=col),
            end=types.Position(line=end_lineno, character=end_col),
        ),
        message=str(error.msg),
        severity=types.DiagnosticSeverity.Error,
        source="wyvern",
    )


def _lint_tree(tree: ast.Module, region: Region) -> list[types.Diagnostic]:
    diagnostics: list[types.Diagnostic] = []
    for node in ast.walk(tree):
        for forbidden_type, message in _FORBIDDEN.items():
            if isinstance(node, forbidden_type) and hasattr(node, "lineno"):
                line = (node.lineno - 1) + region.line_offset
                col = node.col_offset
                end_line = (getattr(node, "end_lineno", node.lineno) - 1) + region.line_offset
                end_col = getattr(node, "end_col_offset", col + 1)
                diagnostics.append(
                    types.Diagnostic(
                        range=types.Range(
                            start=types.Position(line=line, character=col),
                            end=types.Position(line=end_line, character=end_col),
                        ),
                        message=message,
                        severity=types.DiagnosticSeverity.Warning,
                        source="wyvern",
                    )
                )
                break
    return diagnostics
