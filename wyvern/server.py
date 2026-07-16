import os

from pygls.lsp.server import LanguageServer
from lsprotocol import types

from wyvern import __version__
from wyvern.features import completion, diagnostics, hover, symbols

server = LanguageServer("wyvern", __version__)

DRACONIC_LANGUAGE_IDS = {"draconic", "alias", "snippet", "gvar"}


def _is_draconic(params: object) -> bool:
    uri = getattr(getattr(params, "text_document", None), "uri", None)
    if uri is None:
        return True
    return any(uri.endswith(ext) for ext in (".alias", ".snippet", ".gvar", ".draconic"))


def _workspace_paths(ls: LanguageServer, doc_uri: str | None = None) -> list[str]:
    paths = [f.uri.replace("file://", "") for f in ls.workspace.folders.values()]
    if not paths and ls.workspace.root_path:
        paths = [ls.workspace.root_path]
    if doc_uri:
        doc_dir = os.path.dirname(doc_uri.replace("file://", ""))
        if doc_dir not in paths:
            paths = paths + [doc_dir]
    return paths


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    diagnostics.publish(ls, params.text_document.uri, params.text_document.text, _workspace_paths(ls, params.text_document.uri))


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    text = ls.workspace.get_text_document(params.text_document.uri).source
    diagnostics.publish(ls, params.text_document.uri, text, _workspace_paths(ls, params.text_document.uri))


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: LanguageServer, params: types.DidCloseTextDocumentParams) -> None:
    ls.text_document_publish_diagnostics(types.PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=[]))


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["."]),
)
def complete(ls: LanguageServer, params: types.CompletionParams) -> types.CompletionList:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return completion.get_completions(doc.source, params.position, _workspace_paths(ls, params.text_document.uri))


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover_handler(ls: LanguageServer, params: types.HoverParams) -> types.Hover | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return hover.get_hover(doc.source, params.position, _workspace_paths(ls, params.text_document.uri))


@server.feature(
    types.TEXT_DOCUMENT_SIGNATURE_HELP,
    types.SignatureHelpOptions(trigger_characters=["(", ","]),
)
def signature_help(
    ls: LanguageServer, params: types.SignatureHelpParams
) -> types.SignatureHelp | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return hover.get_signature_help(doc.source, params.position, _workspace_paths(ls, params.text_document.uri))


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: LanguageServer, params: types.DocumentSymbolParams
) -> list[types.DocumentSymbol]:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return symbols.get_symbols(doc.source)
