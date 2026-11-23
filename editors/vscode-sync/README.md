# Wyvern Sync for Avrae

See how your Avrae aliases, snippets and gvars differ from what's live, compare them side by side, and push what changed. Works on its own: you don't need the Wyvern LSP, Python or anything else installed.

## What it does

- **A Wyvern Sync view in the activity bar** with every workshop collection you own. Collections in your workspace show each file as unchanged, changed, only on Avrae, or not on Avrae yet. Collections you own but don't have locally can be added to the workspace from the view.
- **A Gvars node** with every gvar you own or can edit, matched with a local file wherever the workspace has one (named after the gvar id: `.gvar`, `.gvar.yaml` or `.yaml`).
- **Compare with live**: click a changed file to open a diff against what's on Avrae. The editor gutter also marks lines that differ from live.
- **Push**: per file, or all changes in a collection at once. Pushing a collection also pushes the gvars it uses through `using()`, if they're yours. Nothing is ever pushed on save.

Files map to Avrae through `collection.io`, the same file [avrae-vscode](https://github.com/Croebh/avrae-vscode) writes: `<name>.alias` and `<name>.snippet` push their code as the new active version, `<name>.md` their docs, and `readme.md` the collection description.

## Token

The extension needs your Avrae token to read your collections and gvars. It's the `avrae-token` value in the Avrae dashboard's local storage. Run **Wyvern Sync: Set Avrae Token**; it's kept in VS Code's secret storage, never in settings. Treat it like a password.

