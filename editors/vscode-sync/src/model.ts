import * as vscode from "vscode";
import {
  allGvarStatus,
  AvraeClient,
  collectionStatus,
  CollectionStatus,
  findCollections,
  indexGvars,
  LiveCollection,
  LiveGvars,
  SyncEntry,
} from "@wyvern/sync-core";

/** Caches what's live, so saving a file re-diffs locally without asking Avrae again. Refresh and push clear it. */
export class CachedClient extends AvraeClient {
  private collections = new Map<string, Promise<LiveCollection>>();
  private gvarList?: Promise<LiveGvars>;

  collection(id: string): Promise<LiveCollection> {
    if (!this.collections.has(id)) {
      this.collections.set(id, super.collection(id));
    }
    return this.collections.get(id)!;
  }

  gvars(): Promise<LiveGvars> {
    this.gvarList ??= super.gvars();
    return this.gvarList;
  }

  clear(): void {
    this.collections.clear();
    this.gvarList = undefined;
  }
}

export interface RemoteCollection {
  id: string;
  name: string;
}

export interface Snapshot {
  /** Collections with a collection.io in the workspace. */
  local: CollectionStatus[];
  /** Collections the user owns on Avrae that no workspace folder holds yet. */
  remote: RemoteCollection[];
  gvars: SyncEntry[];
  /** Every entry with a local file, by file path: the gutter markers and diffs read from here. */
  byFile: Map<string, SyncEntry>;
}

export class SyncModel {
  private ownedIds?: Promise<string[]>;
  snapshot?: Snapshot;

  constructor(readonly client: CachedClient) {}

  clear(): void {
    this.client.clear();
    this.ownedIds = undefined;
  }

  async load(roots: string[], ignoredGvars: Set<string>): Promise<Snapshot> {
    this.ownedIds ??= this.client.ownedCollectionIds();
    const gvars = await this.client.gvars();

    const folders = (await Promise.all(roots.map(findCollections))).flat();
    const index = new Map<string, string>();
    for (const root of roots) {
      for (const [key, file] of await indexGvars(root)) {
        index.set(key, index.get(key) ?? file);
      }
    }

    const local = await Promise.all(folders.map((folder) => collectionStatus(this.client, folder, index, { gvars, ignoredGvars })));
    const localIds = new Set(local.map((status) => status.io.collection));
    const remote = await Promise.all(
      (await this.ownedIds)
        .filter((id) => !localIds.has(id))
        .map(async (id) => ({ id, name: (await this.client.collection(id)).name })),
    );
    const all = await allGvarStatus(gvars, index, ignoredGvars);

    const byFile = new Map<string, SyncEntry>();
    for (const entry of [...local.flatMap((status) => [...status.items, ...status.gvars]), ...all]) {
      if (entry.file) {
        byFile.set(vscode.Uri.file(entry.file).fsPath, entry);
      }
    }

    this.snapshot = {
      local: local.sort((a, b) => a.live.name.localeCompare(b.live.name)),
      remote: remote.sort((a, b) => a.name.localeCompare(b.name)),
      gvars: all,
      byFile,
    };
    return this.snapshot;
  }
}
