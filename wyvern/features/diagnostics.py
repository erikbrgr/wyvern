"""
Publishes Draconic diagnostics: syntax errors and use of forbidden Python constructs.
"""
from __future__ import annotations

import ast
import re

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from wyvern.builtins import CLASS_REGISTRY
from wyvern.parser.analysis import parse
from wyvern.parser.preprocessor import Region

# Method names whose return type is "None" in the registry.
# Assigning the result of these is always a bug.
_NONE_RETURNING_METHODS: frozenset[str] = frozenset(
    m.name
    for cls in CLASS_REGISTRY.values()
    for m in cls.methods
    if m.return_type == "None"
)


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

    ls.text_document_publish_diagnostics(types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics))


_DETECTED_AT_LINE_RE = re.compile(r"\(detected at line (\d+)\)")


def _syntax_error_diagnostic(error: SyntaxError, region: Region) -> types.Diagnostic:
    lineno = (error.lineno or 1) - 1 + region.line_offset
    end_lineno = (error.end_lineno or error.lineno or 1) - 1 + region.line_offset
    # For "unterminated X (detected at line N)" errors, extend the squiggly to line N
    # so the highlighted range covers the whole unclosed literal.
    if m := _DETECTED_AT_LINE_RE.search(error.msg or ""):
        end_lineno = int(m.group(1)) - 1 + region.line_offset
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

        if d := _check_none_assign(node, region):
            diagnostics.append(d)

    return diagnostics


def _check_none_assign(node: ast.AST, region: Region) -> types.Diagnostic | None:
    """Warn when the result of a known None-returning method is assigned to a variable."""
    if not isinstance(node, ast.Assign):
        return None
    call = node.value
    if not isinstance(call, ast.Call):
        return None
    if not isinstance(call.func, ast.Attribute):
        return None
    method = call.func.attr
    if method not in _NONE_RETURNING_METHODS:
        return None

    line = (call.lineno - 1) + region.line_offset
    end_line = (getattr(call, "end_lineno", call.lineno) - 1) + region.line_offset
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=line, character=call.col_offset),
            end=types.Position(line=end_line, character=getattr(call, "end_col_offset", call.col_offset + 1)),
        ),
        message=f"`{method}()` always returns None — assign the object before calling it, not after.",
        severity=types.DiagnosticSeverity.Warning,
        source="wyvern",
    )
