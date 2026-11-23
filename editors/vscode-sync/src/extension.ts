import { promises as fs } from "fs";
import * as path from "path";
import * as vscode from "vscode";
import {
  AvraeApiError,
  COLLECTION_IO,
  LiveCollection,
  matchCollection,
  pullMissing,
  pushEntry,
  readCollectionIo,
  SyncEntry,
  writeCollectionIo,
} from "@wyvern/sync-core";
import { CachedClient, SyncModel } from "./model";
import { changes, Node, SyncTree } from "./tree";

const TOKEN_KEY = "avrae-token";
const LIVE_SCHEME = "avrae-live";
const WATCHED = /\.(alias|snippet|md|gvar|ya?ml)$|collection\.io$/;
// How often coming back to the window may re-read Avrae, for changes made elsewhere (dashboard, another machine).
const AVRAE_RECHECK_MS = 60_000;

class LiveDocuments implements vscode.TextDocumentContentProvider {
  private readonly changed = new vscode.EventEmitter<vscode.Uri>();
  readonly onDidChange = this.changed.event;
  private docs = new Map<string, string>();

  static uri(entry: SyncEntry): vscode.Uri {
    return vscode.Uri.from({ scheme: LIVE_SCHEME, path: `/${entry.label}`, query: `${entry.kind}/${entry.id}/${entry.part}` });
  }

  update(entries: SyncEntry[]): void {
    const old = [...this.docs.keys()];
    this.docs = new Map(entries.filter((e) => e.live !== undefined).map((e) => [LiveDocuments.uri(e).toString(), e.live!]));
    for (const uri of new Set([...old, ...this.docs.keys()])) {
      this.changed.fire(vscode.Uri.parse(uri));
    }
  }

  provideTextDocumentContent(uri: vscode.Uri): string {
    return this.docs.get(uri.toString()) ?? "";
  }
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const tree = new SyncTree();
  const live = new LiveDocuments();
  let model: SyncModel | undefined;

  const view = vscode.window.createTreeView("wyvernSync.live", { treeDataProvider: tree, showCollapseAll: true });
  context.subscriptions.push(view, vscode.workspace.registerTextDocumentContentProvider(LIVE_SCHEME, live));

  async function connect(): Promise<void> {
    const token = await context.secrets.get(TOKEN_KEY);
    await vscode.commands.executeCommand("setContext", "wyvernSync.hasToken", Boolean(token));
    model = token ? new SyncModel(new CachedClient(token)) : undefined;
    tree.update(undefined);
    await refresh();
  }

  let pending: NodeJS.Timeout | undefined;
  let lastAvraeRead = Date.now();

  /** Re-diffs after local changes, batching bursts like a whole folder being added or deleted. */
  function refreshSoon(): void {
    clearTimeout(pending);
    pending = setTimeout(() => refresh(), 300);
  }

  async function refresh(fromAvrae = false): Promise<void> {
    if (!model) {
      return;
    }
    if (fromAvrae) {
      model.clear();
      lastAvraeRead = Date.now();
    }
    const roots = (vscode.workspace.workspaceFolders ?? []).filter((f) => f.uri.scheme === "file").map((f) => f.uri.fsPath);
    try {
      const snapshot = await vscode.window.withProgress({ location: { viewId: "wyvernSync.live" } }, () => model!.load(roots));
      tree.update(snapshot);
      live.update([...snapshot.byFile.values(), ...snapshot.local.flatMap((s) => s.items), ...snapshot.gvars]);
      const count = changes([...snapshot.byFile.values()], snapshot.readOnly).length;
      view.badge = count ? { value: count, tooltip: `${count} changed vs live Avrae` } : undefined;
    } catch (error) {
      await showError(error);
    }
  }

  async function showError(error: unknown): Promise<void> {
    if (error instanceof AvraeApiError && (error.status === 401 || error.status === 403)) {
      const choice = await vscode.window.showErrorMessage("Wyvern Sync: Avrae rejected the token. It may have expired.", "Set Avrae Token");
      if (choice) {
        await vscode.commands.executeCommand("wyvernSync.setToken");
      }
      return;
    }
    vscode.window.showErrorMessage(`Wyvern Sync: ${error instanceof Error ? error.message : String(error)}`);
  }

  async function open(node: Node): Promise<void> {
    if (node.type !== "entry") {
      return;
    }
    const { entry } = node;
    const file = entry.file && entry.local !== undefined ? vscode.Uri.file(entry.file) : undefined;
    if (file && entry.live !== undefined) {
      await vscode.commands.executeCommand("vscode.diff", LiveDocuments.uri(entry), file, `${entry.label} (Avrae ↔ local)`);
    } else if (file) {
      await vscode.window.showTextDocument(file);
    } else if (entry.live !== undefined) {
      await vscode.window.showTextDocument(LiveDocuments.uri(entry));
    }
  }

  async function push(node: Node): Promise<void> {
    if (node.type !== "entry" || !model) {
      return;
    }
    try {
      const result = await pushEntry(model.client, node.entry, node.status?.live);
      vscode.window.showInformationMessage(`Pushed ${node.entry.label}: ${result}`);
    } catch (error) {
      await showError(error);
    }
    await refresh(true);
  }

  async function pushAll(node: Node): Promise<void> {
    if (node.type !== "collection" || !model) {
      return;
    }
    const { status } = node;
    const pending = changes([...status.items, ...status.gvars], model.snapshot?.readOnly ?? new Set());
    const confirm = await vscode.window.showWarningMessage(
      `Push ${pending.length} change${pending.length === 1 ? "" : "s"} in ${status.live.name} to Avrae?`,
      { modal: true, detail: pending.map((e) => e.label).join("\n") },
      "Push",
    );
    if (confirm !== "Push") {
      return;
    }
    const failed: string[] = [];
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `Pushing ${status.live.name}` }, async (progress) => {
      for (const entry of pending) {
        progress.report({ message: entry.label, increment: 100 / pending.length });
        try {
          await pushEntry(model!.client, entry, status.live);
        } catch (error) {
          failed.push(`${entry.label}: ${error instanceof Error ? error.message : String(error)}`);
        }
      }
    });
    if (failed.length) {
      vscode.window.showErrorMessage(`Wyvern Sync: ${failed.length} of ${pending.length} failed`, { modal: true, detail: failed.join("\n") });
    } else {
      vscode.window.showInformationMessage(`Pushed ${pending.length} change${pending.length === 1 ? "" : "s"} in ${status.live.name}.`);
    }
    await refresh(true);
  }

  async function register(node: Node): Promise<void> {
    if (node.type !== "remote" || !model) {
      return;
    }
    const { collection } = node;
    const picked = await vscode.window.showOpenDialog({
      canSelectFolders: true,
      canSelectFiles: false,
      defaultUri: vscode.workspace.workspaceFolders?.[0]?.uri,
      openLabel: `Use for ${collection.name}`,
      title: `Choose the folder that holds ${collection.name}`,
    });
    const folder = picked?.[0]?.fsPath;
    if (!folder) {
      return;
    }
    const files = await fs.readdir(folder);
    if (files.includes(COLLECTION_IO)) {
      vscode.window.showErrorMessage(`Wyvern Sync: ${path.basename(folder)} already has a ${COLLECTION_IO}.`);
      return;
    }

    const live = await model.client.collection(collection.id);
    const registration = matchCollection(live, files);
    const leftover = [...registration.unmatchedLocal];
    for (const item of registration.unmatchedLive) {
      const candidates = leftover.filter((file) => file.endsWith(`.${item.kind}`));
      if (!candidates.length) {
        continue;
      }
      const target = `${item.name}.${item.kind}`;
      const choice = await vscode.window.showQuickPick(
        [
          { label: "None of these", file: undefined },
          ...candidates.map((file) => ({ label: file, description: `rename to ${target}`, file })),
        ],
        { title: `${collection.name}: no local file for ${target}`, placeHolder: `Which local file is ${target}?`, ignoreFocusOut: true },
      );
      if (!choice) {
        return;
      }
      if (choice.file) {
        await renameWithDocs(folder, choice.file, item.name);
        leftover.splice(leftover.indexOf(choice.file), 1);
      }
    }

    await writeCollectionIo(folder, registration.io);
    const written = await askToDownload(live, folder);
    vscode.window.showInformationMessage(`Added ${collection.name}${written ? `, downloaded ${written} file${written === 1 ? "" : "s"}` : ""}.`);
    await refresh();
  }

  async function askToDownload(live: LiveCollection, folder: string): Promise<number> {
    const choice = await vscode.window.showInformationMessage(
      `Download the files from ${live.name} that aren't in ${path.basename(folder)} yet?`,
      { modal: true, detail: "Files that already exist are never overwritten." },
      "Download",
    );
    if (choice !== "Download") {
      return 0;
    }
    // Map live items that collection.io doesn't list yet, so the downloaded files are linked too.
    const io = await readCollectionIo(folder);
    const known = new Set([...Object.values(io.aliases), ...Object.values(io.snippets)]);
    const fresh = matchCollection(live, []).io;
    for (const kind of ["aliases", "snippets"] as const) {
      for (const [name, id] of Object.entries(fresh[kind])) {
        if (!known.has(id)) {
          io[kind][name] = id;
        }
      }
    }
    await writeCollectionIo(folder, { ...io, name: io.name || live.name, collection: live._id });
    return (await pullMissing(live, folder)).length;
  }

  async function download(node: Node): Promise<void> {
    if (node.type !== "collection" || !model) {
      return;
    }
    const written = await askToDownload(node.status.live, node.status.folder);
    if (written) {
      vscode.window.showInformationMessage(`Downloaded ${written} file${written === 1 ? "" : "s"} from ${node.status.live.name}.`);
    }
    await refresh();
  }

  // Any create or delete: a deleted folder only reports the folder itself, not the collection.io inside it.
  const watcher = vscode.workspace.createFileSystemWatcher("**/*", false, true, false);
  watcher.onDidCreate(refreshSoon);
  watcher.onDidDelete(refreshSoon);
  const collections = vscode.workspace.createFileSystemWatcher("**/collection.io", true, false, true);
  collections.onDidChange(refreshSoon);
  context.subscriptions.push(
    watcher,
    collections,
    vscode.window.onDidChangeWindowState((state) => state.focused && Date.now() - lastAvraeRead > AVRAE_RECHECK_MS && refresh(true)),
    vscode.commands.registerCommand("wyvernSync.setToken", async () => {
      const token = await vscode.window.showInputBox({
        title: "Avrae token",
        prompt: "The 'avrae-token' value from the Avrae dashboard's local storage. Stored in VS Code's secret storage.",
        password: true,
        ignoreFocusOut: true,
      });
      if (token) {
        await context.secrets.store(TOKEN_KEY, token.trim());
      }
    }),
    vscode.commands.registerCommand("wyvernSync.clearToken", () => context.secrets.delete(TOKEN_KEY)),
    vscode.commands.registerCommand("wyvernSync.refresh", () => refresh(true)),
    vscode.commands.registerCommand("wyvernSync.open", (node: Node) => open(node)),
    vscode.commands.registerCommand("wyvernSync.showDiff", (node: Node) => open(node)),
    vscode.commands.registerCommand("wyvernSync.push", push),
    vscode.commands.registerCommand("wyvernSync.pushAll", pushAll),
    vscode.commands.registerCommand("wyvernSync.register", register),
    vscode.commands.registerCommand("wyvernSync.download", download),
    context.secrets.onDidChange((e) => e.key === TOKEN_KEY && connect()),
    vscode.workspace.onDidSaveTextDocument((doc) => WATCHED.test(doc.fileName) && refreshSoon()),
    vscode.workspace.onDidChangeWorkspaceFolders(() => refresh()),
  );

  await connect();
}

async function renameWithDocs(folder: string, file: string, name: string): Promise<void> {
  const ext = path.extname(file);
  const base = file.slice(0, -ext.length);
  await vscode.workspace.fs.rename(vscode.Uri.file(path.join(folder, file)), vscode.Uri.file(path.join(folder, `${name}${ext}`)));
  const docs = vscode.Uri.file(path.join(folder, `${base}.md`));
  const target = vscode.Uri.file(path.join(folder, `${name}.md`));
  if ((await exists(docs)) && !(await exists(target))) {
    await vscode.workspace.fs.rename(docs, target);
  }
}

async function exists(uri: vscode.Uri): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(uri);
    return true;
  } catch {
    return false;
  }
}

export function deactivate(): void {}
