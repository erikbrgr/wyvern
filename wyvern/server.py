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


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    diagnostics.publish(ls, params.text_document.uri, params.text_document.text)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    text = params.content_changes[-1].text
    diagnostics.publish(ls, params.text_document.uri, text)


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: LanguageServer, params: types.DidCloseTextDocumentParams) -> None:
    ls.publish_diagnostics(params.text_document.uri, [])


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=[".", "("]),
)
def complete(ls: LanguageServer, params: types.CompletionParams) -> types.CompletionList:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return completion.get_completions(doc.source, params.position)


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover_handler(ls: LanguageServer, params: types.HoverParams) -> types.Hover | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return hover.get_hover(doc.source, params.position)


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: LanguageServer, params: types.DocumentSymbolParams
) -> list[types.DocumentSymbol]:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return symbols.get_symbols(doc.source)
