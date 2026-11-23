import * as vscode from "vscode";
import { CollectionStatus, isPushable, SyncEntry, SyncState } from "@wyvern/sync-core";
import { RemoteCollection, Snapshot } from "./model";

export type Node =
  | { type: "collection"; status: CollectionStatus }
  | { type: "remote"; collection: RemoteCollection }
  | { type: "gvars"; entries: SyncEntry[]; status?: CollectionStatus }
  | { type: "entry"; entry: SyncEntry; status?: CollectionStatus };

const STATE_LABELS: Record<SyncState, string> = {
  unchanged: "unchanged",
  modified: "changed",
  "local-only": "not on Avrae",
  "live-only": "only on Avrae",
  "not-editable": "not yours to edit",
};

const STATE_ICONS: Record<SyncState, vscode.ThemeIcon> = {
  unchanged: new vscode.ThemeIcon("check", new vscode.ThemeColor("disabledForeground")),
  modified: new vscode.ThemeIcon("diff-modified", new vscode.ThemeColor("gitDecoration.modifiedResourceForeground")),
  "local-only": new vscode.ThemeIcon("file-add", new vscode.ThemeColor("gitDecoration.untrackedResourceForeground")),
  "live-only": new vscode.ThemeIcon("cloud", new vscode.ThemeColor("disabledForeground")),
  "not-editable": new vscode.ThemeIcon("lock", new vscode.ThemeColor("disabledForeground")),
};

/** The entries a push would send: changed, and not in someone else's collection. */
export function changes(entries: SyncEntry[], readOnly: Set<SyncEntry>): SyncEntry[] {
  return entries.filter((entry) => isPushable(entry) && !readOnly.has(entry));
}

function countLabel(entries: SyncEntry[]): string {
  const n = entries.filter((entry) => entry.state === "modified").length;
  return n ? `${n} changed` : "in sync";
}

export class SyncTree implements vscode.TreeDataProvider<Node> {
  private readonly changed = new vscode.EventEmitter<Node | undefined>();
  readonly onDidChangeTreeData = this.changed.event;
  snapshot?: Snapshot;

  update(snapshot: Snapshot | undefined): void {
    this.snapshot = snapshot;
    this.changed.fire(undefined);
  }

  getChildren(node?: Node): Node[] {
    const snapshot = this.snapshot;
    if (!snapshot) {
      return [];
    }
    if (!node) {
      return [
        ...snapshot.local.map((status): Node => ({ type: "collection", status })),
        ...snapshot.remote.map((collection): Node => ({ type: "remote", collection })),
        { type: "gvars", entries: snapshot.gvars },
      ];
    }
    if (node.type === "collection") {
      const items = node.status.items.map((entry): Node => ({ type: "entry", entry, status: node.status }));
      return node.status.gvars.length ? [...items, { type: "gvars", entries: node.status.gvars, status: node.status }] : items;
    }
    if (node.type === "gvars") {
      return node.entries.map((entry): Node => ({ type: "entry", entry, status: node.status }));
    }
    return [];
  }

  getTreeItem(node: Node): vscode.TreeItem {
    const readOnly = this.snapshot?.readOnly ?? new Set<SyncEntry>();
    switch (node.type) {
      case "collection": {
        const { status } = node;
        const all = [...status.items, ...status.gvars];
        const item = new vscode.TreeItem(status.live.name, vscode.TreeItemCollapsibleState.Collapsed);
        const mine = !all.some((entry) => readOnly.has(entry));
        item.description = `${countLabel(all)} · ${mine ? "" : "not yours · "}${vscode.workspace.asRelativePath(status.folder)}`;
        item.iconPath = new vscode.ThemeIcon(mine ? "folder-library" : "lock");
        item.contextValue = changes(all, readOnly).length ? "collection-changed" : "collection";
        item.tooltip = `${status.live.name}\n${status.folder}`;
        return item;
      }
      case "remote": {
        const item = new vscode.TreeItem(node.collection.name, vscode.TreeItemCollapsibleState.None);
        item.description = "not in this workspace";
        item.iconPath = new vscode.ThemeIcon("cloud");
        item.contextValue = "collection-remote";
        item.tooltip = "Add this collection to the workspace to compare and push it.";
        return item;
      }
      case "gvars": {
        const item = new vscode.TreeItem("Gvars", vscode.TreeItemCollapsibleState.Collapsed);
        item.description = node.status ? `${countLabel(node.entries)} · used by this collection` : `${node.entries.length} · ${countLabel(node.entries)}`;
        item.iconPath = new vscode.ThemeIcon("symbol-variable");
        return item;
      }
      case "entry": {
        const { entry } = node;
        const item = new vscode.TreeItem(entry.label, vscode.TreeItemCollapsibleState.None);
        item.description = STATE_LABELS[entry.state];
        item.iconPath = STATE_ICONS[entry.state];
        item.contextValue = changes([entry], readOnly).length ? "entry-pushable" : `entry-${entry.state}`;
        item.tooltip = entry.file ? `${entry.file}\n${STATE_LABELS[entry.state]}` : STATE_LABELS[entry.state];
        if (entry.file) {
          item.resourceUri = vscode.Uri.file(entry.file);
        }
        item.command = { command: "wyvernSync.open", title: "Open", arguments: [node] };
        return item;
      }
    }
  }
}
