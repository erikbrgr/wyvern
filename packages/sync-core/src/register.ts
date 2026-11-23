import { ItemKind, LiveCollection } from "./api";
import { flattenAliases } from "./status";
import { CollectionIo } from "./workspace";

export interface LiveItemRef {
  kind: ItemKind;
  /** The collection.io name: "parent child" for subcommands. */
  name: string;
  id: string;
}

export interface Registration {
  io: CollectionIo;
  /** Live aliases and snippets with no local file of the same name. */
  unmatchedLive: LiveItemRef[];
  /** Local .alias and .snippet files that match no live item. */
  unmatchedLocal: string[];
}

/** Maps a live collection onto a folder's files by name, the way avrae-vscode names them when it pulls a collection. */
export function matchCollection(live: LiveCollection, files: string[]): Registration {
  const io: CollectionIo = { name: live.name, collection: live._id, aliases: {}, snippets: {} };
  const unmatchedLive: LiveItemRef[] = [];
  const local = new Set(files.filter((file) => file.endsWith(".alias") || file.endsWith(".snippet")));

  const liveItems: LiveItemRef[] = [
    ...[...flattenAliases(live.aliases)].map(([name, alias]) => ({ kind: "alias" as const, name, id: alias._id })),
    ...live.snippets.map((snippet) => ({ kind: "snippet" as const, name: snippet.name, id: snippet._id })),
  ];
  for (const item of liveItems) {
    const file = `${item.name}.${item.kind}`;
    if (local.delete(file)) {
      link(io, item);
    } else {
      unmatchedLive.push(item);
    }
  }
  return { io, unmatchedLive, unmatchedLocal: [...local].sort() };
}

export function link(io: CollectionIo, item: LiveItemRef): void {
  (item.kind === "alias" ? io.aliases : io.snippets)[item.name] = item.id;
}

