# sync-core

The shared core of Wyvern Sync: compares a workspace's Avrae aliases, snippets and gvars with what's live on Avrae, and pushes the differences. The VS Code extension and the GitHub Action both build on it, so they always agree on what "changed" means.

It reads avrae-vscode's `collection.io` (alias and snippet names mapped to workshop ids) and works like avrae-aliases' `push_collection.py`:

- `<name>.alias` / `<name>.snippet` push as a new code version and become active, `<name>.md` updates the docs, `readme.md` the collection description.
- A collection's gvars are the gvar files in its folder (named after the gvar id: `.gvar`, `.gvar.yaml`, `.yaml`), plus every local gvar they and its code reach through `using()`, followed transitively. Dot folders such as `.wyvern/usings` are never searched.
- A gvar can only be pushed if the token's user owns or can edit it on Avrae.
- Anything identical to live (ignoring surrounding whitespace) is unchanged and isn't pushed unless forced.

```bash
npm install
npm run compile
npm test
```
