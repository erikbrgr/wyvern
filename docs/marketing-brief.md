# Wyvern — Marketing Brief

Use this document as context when chatting with Claude (or anyone else) about marketing, copywriting, community outreach, or promotion for the Wyvern project.

---

## What is Wyvern?

Wyvern is an open-source developer tool that brings professional IDE features to Draconic — the scripting language used inside **Avrae**, a popular D&D automation bot for Discord.

It is a **Language Server Protocol (LSP)** implementation, meaning it plugs into any modern code editor and provides:

- **Diagnostics** — underlines syntax errors and forbidden constructs (like `import` or `class`) before you ever run the alias in Discord
- **Hover documentation** — hover over `vroll()`, `character()`, or any Avrae function to see its signature and description inline
- **Code completion** — autocomplete Avrae's API, your own variables, and all Draconic built-ins as you type
- **Document outline** — jump between functions and variables in the sidebar
- **Improved syntax highlighting** — visually distinguishes dice expressions like `{1d20+5}` from inline code blocks like `{{expr}}` and variable substitutions like `<target>`

---

## The product, concretely

There are three installable pieces:

| What | How to get it | Who it's for |
|---|---|---|
| **wyvern-lsp** Python package | `pip install wyvern-lsp` | Anyone using a non-VSCode LSP editor (Neovim, Emacs, Helix, etc.) |
| **Wyvern LSP** VSCode extension | Install from VS Code Marketplace | VSCode users — auto-installs the Python package for you |
| **Avrae Developer Pack** VSCode extension pack | Install from VS Code Marketplace | New users who want everything in one click (installs both Wyvern and Croebh's Avrae Utilities) |

The VSCode extension handles the Python setup automatically: it detects your Python interpreter, and if `wyvern-lsp` isn't installed, it asks to install it for you.

---

## The problem it solves

Writing Avrae aliases today means:

1. Writing Draconic code in a plain text editor with no intelligence
2. Uploading or pasting it into Discord
3. Running `!alias` and seeing it fail with a cryptic error
4. Fixing the error and repeating

There is no feedback loop. You find out your code is broken only at runtime, inside Discord. For complex aliases with hundreds of lines, this is painful.

Wyvern closes that loop entirely. Errors are underlined in your editor the moment you type them. The Avrae API is documented right there in tooltips. You never have to open the Avrae docs just to remember what `argparse()` returns.

---

## Who uses Avrae?

Avrae is one of the most widely-used D&D bots on Discord. It is used by:

- **Dungeon Masters** running campaigns on Discord
- **Players** who automate character actions, spell lookups, and combat tracking
- **Alias authors** — a dedicated community that writes sophisticated Draconic scripts to share with others (published as Workshop items on Avrae's platform)
- **Server admins** who maintain shared aliases for their D&D communities

The alias-writing community is the primary target. These are people who already write code (or are learning to) and would immediately appreciate IDE tooling.

There is an active community on the **Avrae Discord server** (tens of thousands of members) and the **r/avrae** subreddit, as well as GitHub and the Avrae Workshop.

---

## Competitive landscape

- **Croebh's Avrae Utilities** (VSCode extension) — the existing tool. Provides syntax highlighting and the ability to push/pull GVARs (global variables stored on Avrae's server). No language intelligence at all. Wyvern is designed to work *alongside* this extension, not replace it. The **Avrae Developer Pack** bundles both.
- **No other Draconic LSP exists.** Wyvern is the first.

---

## Tone and positioning

- **For the community, by the community.** This is a hobby/open-source project by an Avrae user, not a corporate product.
- **It just works.** The auto-install and Python detection mean most users will never touch a terminal.
- **Respects Croebh's work.** Wyvern complements rather than competes with the existing ecosystem.
- **Open source** under GPL v3. Contributions welcome.

---

## Key messages (pick and adapt)

- *"Stop debugging your aliases in Discord."*
- *"Autocomplete for Avrae's entire API, right in your editor."*
- *"Hover over `vroll()` and see exactly what it returns."*
- *"The first LSP for Draconic. Works with VSCode, Neovim, Emacs, and more."*
- *"Catch errors before you paste them into Discord."*
- *"One-click setup: install the Avrae Developer Pack and you're done."*

---

## Current state (June 2026)

The project is functional but pre-release:

- Core LSP server is implemented (diagnostics, hover, completion, symbols)
- VSCode extension with improved syntax highlighting and auto-install is built
- Not yet published to PyPI or the VS Code Marketplace
- No public announcement has been made

**Immediate marketing needs:**
- Write copy for the VS Code Marketplace listing
- Write copy for the PyPI package description
- Draft an announcement post for the Avrae Discord server
- Write a README that explains the project to new visitors on GitHub
- Think about how to reach the alias-writing community specifically

---

## Links

- GitHub: https://github.com/erikbrgr/wyvern
- Avrae docs: https://avrae.readthedocs.io/en/latest/
- Croebh's extension: https://github.com/Croebh/avrae-vscode
- Avrae Discord: https://avrae.io (has a #aliases channel)
