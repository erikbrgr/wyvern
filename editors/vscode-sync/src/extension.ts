import { promises as fs } from "fs";
import * as path from "path";
import * as vscode from "vscode";
import { AvraeApiError, COLLECTION_IO, link, matchCollection, pushEntry, SyncEntry, writeCollectionIo } from "@wyvern/sync-core";
import { CachedClient, SyncModel } from "./model";
import { changes, Node, SyncTree } from "./tree";

const TOKEN_KEY = "avrae-token";
const LIVE_SCHEME = "avrae-live";
const WATCHED = /\.(alias|snippet|md|gvar|ya?ml)$|collection\.io$/;

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
  const scm = vscode.scm.createSourceControl("wyvernSync", "Avrae (live)");
  scm.quickDiffProvider = {
    provideOriginalResource(uri: vscode.Uri) {
      const entry = model?.snapshot?.byFile.get(uri.fsPath);
      return entry?.live !== undefined ? LiveDocuments.uri(entry) : undefined;
    },
  };
  context.subscriptions.push(view, scm, vscode.workspace.registerTextDocumentContentProvider(LIVE_SCHEME, live));

  async function connect(): Promise<void> {
    const token = await context.secrets.get(TOKEN_KEY);
    await vscode.commands.executeCommand("setContext", "wyvernSync.hasToken", Boolean(token));
    model = token ? new SyncModel(new CachedClient(token)) : undefined;
    tree.update(undefined);
    await refresh();
  }

  async function refresh(fromAvrae = false): Promise<void> {
    if (!model) {
      return;
    }
    if (fromAvrae) {
      model.clear();
    }
    const roots = (vscode.workspace.workspaceFolders ?? []).filter((f) => f.uri.scheme === "file").map((f) => f.uri.fsPath);
    const ignored = new Set(vscode.workspace.getConfiguration("wyvernSync").get<string[]>("ignoredGvars", []).map((key) => key.toLowerCase()));
    try {
      const snapshot = await vscode.window.withProgress({ location: { viewId: "wyvernSync.live" } }, () => model!.load(roots, ignored));
      tree.update(snapshot);
      live.update([...snapshot.byFile.values(), ...snapshot.local.flatMap((s) => s.items), ...snapshot.gvars]);
      const count = changes([...snapshot.byFile.values()]).length;
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
    const pending = changes([...status.items, ...status.gvars]);
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

    const registration = matchCollection(await model.client.collection(collection.id), files);
    const leftover = [...registration.unmatchedLocal];
    for (const item of registration.unmatchedLive) {
      const candidates = leftover.filter((file) => file.endsWith(`.${item.kind}`));
      if (!candidates.length) {
        continue;
      }
      const target = `${item.name}.${item.kind}`;
      const choice = await vscode.window.showQuickPick(
        [
          { label: "Leave it only on Avrae", file: undefined },
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
        link(registration.io, item);
      }
    }

    await writeCollectionIo(folder, registration.io);
    const linked = Object.keys(registration.io.aliases).length + Object.keys(registration.io.snippets).length;
    vscode.window.showInformationMessage(`Added ${collection.name}: ${linked} linked to Avrae.`);
    await refresh();
  }

  context.subscriptions.push(
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
    context.secrets.onDidChange((e) => e.key === TOKEN_KEY && connect()),
    vscode.workspace.onDidSaveTextDocument((doc) => WATCHED.test(doc.fileName) && refresh()),
    vscode.workspace.onDidChangeWorkspaceFolders(() => refresh()),
    vscode.workspace.onDidChangeConfiguration((e) => e.affectsConfiguration("wyvernSync") && refresh()),
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
