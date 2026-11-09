# Wyvern LSP

Wyvern is a Language Server Protocol (LSP) implementation for Draconic, the scripting language used by the [Avrae](https://avrae.io) Discord bot. It brings real IDE features to your editor: errors underlined as you type, hover documentation for Avrae's API, and autocomplete for the functions you actually use.

## Features

- **Diagnostics** - syntax errors and forbidden constructs (like `import` or `class`) are flagged before you ever run the alias
- **Hover documentation** - hover over `vroll()`, `character()`, or any Avrae built-in to see its signature and description inline
- **Code completion** - autocomplete Avrae's API, Draconic built-ins, and your own variables as you type
- **Document outline** - jump between functions and variables in the sidebar
- **Syntax highlighting** - visually distinguishes dice expressions `{1d20+5}`, inline code `{{expr}}`, and variable substitutions `<target>`

## Requirements

This extension is a thin client. The language features come from `wyvern-lsp`, a Python language server published to [PyPI](https://pypi.org/project/wyvern-lsp/) from the same open source repository ([github.com/erikbrgr/wyvern](https://github.com/erikbrgr/wyvern)). You need Python 3.11 or newer.

Install the server yourself before using the extension:

```bash
pip install wyvern-lsp
```

The extension never installs or downloads anything on its own. If it can't find the server, it shows the install command for your interpreter and stops. Run the command, then reload the window.

## Extension Settings

- `wyvern.pythonPath` - path to the Python executable to use. Leave empty to auto-detect.
- `wyvern.serverPath` - path to the wyvern module or script. Leave empty to use the installed `wyvern-lsp` package.
- `wyvern.trace.server` - enable tracing of LSP communication between VS Code and the Wyvern server.

## Works great with Avrae Utilities

Wyvern pairs naturally with [Croebh's Avrae Utilities](https://github.com/Croebh/avrae-vscode) extension, which handles GVAR push/pull and collection management. The two extensions cover different ground and are designed to be used together.

## Source & Issues

Wyvern is open source under the MIT license. Source code, issue tracker, and contribution guide: [github.com/erikbrgr/wyvern](https://github.com/erikbrgr/wyvern).

## Credits

Wyvern icon by [Lorc](https://lorcblog.blogspot.com) via [game-icons.net](https://game-icons.net), used under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
