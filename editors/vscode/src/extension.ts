import * as cp from "child_process";
import * as path from "path";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const pythonPath = await resolvePythonPath();
  if (!pythonPath) {
    vscode.window.showErrorMessage(
      "Wyvern: Could not find a Python interpreter. " +
        "Set 'wyvern.pythonPath' in settings or install the Python extension."
    );
    return;
  }

  const installed = await isWyvernInstalled(pythonPath);
  if (!installed) {
    // The extension never installs packages itself: it tells the user what to run
    // and links to the source, so nothing is downloaded or executed without them.
    const installCommand = `"${pythonPath}" -m pip install wyvern-lsp`;
    const choice = await vscode.window.showWarningMessage(
      "Wyvern: the wyvern-lsp language server is not installed for this Python interpreter. " +
        `Install it from PyPI with: ${installCommand}`,
      "Copy install command",
      "View source"
    );
    if (choice === "Copy install command") {
      await vscode.env.clipboard.writeText(installCommand);
    } else if (choice === "View source") {
      await vscode.env.openExternal(vscode.Uri.parse("https://github.com/erikbrgr/wyvern"));
    }
    return;
  }

  // If another extension (e.g. Croebh's) has claimed .gvar files, override the language
  // so Wyvern's grammar and LSP features apply correctly.
  const forceGvarLanguage = (doc: vscode.TextDocument) => {
    if (doc.uri.fsPath.endsWith(".gvar") && doc.languageId !== "draconic-gvar") {
      vscode.languages.setTextDocumentLanguage(doc, "draconic-gvar").then(
        undefined,
        () => {} // ignore — file may not be open in an editor yet
      );
    }
  };
  vscode.workspace.textDocuments.forEach(forceGvarLanguage);
  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(forceGvarLanguage));

  client = createClient(pythonPath);
  client.start();
  context.subscriptions.push(client);
}

export async function deactivate(): Promise<void> {
  if (client) {
    await client.stop();
  }
}

function createClient(pythonPath: string): LanguageClient {
  const config = vscode.workspace.getConfiguration("wyvern");
  const serverPath: string = config.get("serverPath") || "";

  const serverOptions: ServerOptions = serverPath
    ? { command: serverPath, args: [], transport: TransportKind.stdio }
    : {
        command: pythonPath,
        args: ["-m", "wyvern"],
        transport: TransportKind.stdio,
      };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: "file", language: "draconic" },
      { scheme: "file", language: "draconic-gvar" },
      { scheme: "file", pattern: "**/*.alias" },
      { scheme: "file", pattern: "**/*.snippet" },
      { scheme: "file", pattern: "**/*.gvar" },
    ],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher(
        "**/*.{alias,snippet,gvar,draconic}"
      ),
    },
    traceOutputChannel: vscode.window.createOutputChannel(
      "Wyvern LSP Trace",
      { log: true }
    ),
  };

  return new LanguageClient("wyvern", "Wyvern Draconic LSP", serverOptions, clientOptions);
}

async function resolvePythonPath(): Promise<string | undefined> {
  // 1. User's explicit setting takes priority
  const config = vscode.workspace.getConfiguration("wyvern");
  const explicit: string = config.get("pythonPath") || "";
  if (explicit) return explicit;

  // 2. Try the official Python extension's active interpreter
  const pythonExt = vscode.extensions.getExtension("ms-python.python");
  if (pythonExt) {
    if (!pythonExt.isActive) await pythonExt.activate();
    const api = pythonExt.exports as { environments?: { getActiveEnvironmentPath?: () => { path: string } } };
    const envPath = api?.environments?.getActiveEnvironmentPath?.()?.path;
    if (envPath) return envPath;
  }

  // 3. Fall back to PATH
  for (const candidate of ["python3", "python"]) {
    if (await commandExists(candidate)) return candidate;
  }

  return undefined;
}

function commandExists(cmd: string): Promise<boolean> {
  return new Promise((resolve) => {
    cp.exec(`${cmd} --version`, (err) => resolve(!err));
  });
}

function isWyvernInstalled(pythonPath: string): Promise<boolean> {
  return new Promise((resolve) => {
    cp.exec(`"${pythonPath}" -m wyvern --help`, (err) => resolve(!err));
  });
}
