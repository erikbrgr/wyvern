# wyvern
An LSP for Draconic — providing diagnostics, hover docs, and code completion for Avrae alias scripting.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js / npm (`brew install node` on macOS)

### 1. Set up the Python server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Build the VS Code extension

```bash
cd editors/vscode
npm install
npm run compile
```

### 3. Run the extension in VS Code

Open `editors/vscode/` in VS Code and press **F5**. This launches an **Extension Development Host** — a second VS Code window with the extension loaded.

Open any `.alias`, `.snippet`, `.gvar`, or `.draconic` file in that window to activate the LSP.

> If the server doesn't start, set `wyvern.pythonPath` in VS Code settings to your `.venv/bin/python`.

### Verify the LSP is running

- Check `View → Output → Wyvern LSP` in the Extension Development Host window
- Or run `ps aux | grep wyvern` in a terminal
- For full LSP message tracing, add `"wyvern.trace.server": "verbose"` to your VS Code settings
