# Wyvern

[![PyPI version](https://img.shields.io/pypi/v/wyvern-lsp.svg)](https://pypi.org/project/wyvern-lsp/)

Wyvern is a Language Server Protocol (LSP) implementation for Draconic, the scripting language used by the [Avrae](https://avrae.io) Discord bot. It brings real IDE features to your editor: errors underlined as you type, hover documentation for Avrae's API, and autocomplete for the functions you actually use.

## Features

- **Diagnostics** - syntax errors and forbidden constructs (like `import` or `class`) are flagged before you ever run the alias
- **Hover documentation** - hover over `vroll()`, `character()`, or any Avrae built-in to see its signature and description inline
- **Code completion** - autocomplete Avrae's API, Draconic built-ins, and your own variables as you type

![Screenshot showing code completion for character class](/docs/media/cc-avrae.png)

- **Document outline** - jump between functions and variables in the sidebar
- **Syntax highlighting** - visually distinguishes dice expressions `{1d20+5}`, inline code `{{expr}}`, and variable substitutions `<target>`

## Installation

**VSCode** - install the [Wyvern LSP](https://marketplace.visualstudio.com/...) extension from the marketplace. It will detect your Python interpreter and install the language server automatically.

**Other editors (Neovim, Emacs, Helix, etc.)** - install the [wyvern-lsp](https://pypi.org/project/wyvern-lsp/) language server directly:

```bash
pip install wyvern-lsp
```

Then configure your editor to use `wyvern-lsp` as the language server for `.alias`, `.snippet`, and `.gvar` files.

## Works great with Avrae Utilities

Wyvern pairs naturally with [Croebh's Avrae Utilities](https://github.com/Croebh/avrae-vscode) extension, which handles GVAR push/pull and collection management. The two extensions cover different ground and are designed to be used together.

## Contributing

Wyvern is open source under the MIT license. Issues and pull requests are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

Wyvern icon by [Lorc](https://lorcblog.blogspot.com) via [game-icons.net](https://game-icons.net), used under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
