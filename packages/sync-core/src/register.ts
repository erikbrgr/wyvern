import { promises as fs } from "fs";
import * as path from "path";
import { ItemKind, LiveCollection } from "./api";
import { flattenAliases } from "./status";
import { CollectionIo, readText } from "./workspace";

export interface LiveItemRef {
  kind: ItemKind;
  /** The collection.io name: "parent child" for subcommands. */
  name: string;
  id: string;
}

export interface Registration {
  /** Every live alias and snippet, like avrae-vscode writes it. */
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

  for (const [name, alias] of flattenAliases(live.aliases)) {
    io.aliases[name] = alias._id;
    if (!local.delete(`${name}.alias`)) {
      unmatchedLive.push({ kind: "alias", name, id: alias._id });
    }
  }
  for (const snippet of live.snippets) {
    io.snippets[snippet.name] = snippet._id;
    if (!local.delete(`${snippet.name}.snippet`)) {
      unmatchedLive.push({ kind: "snippet", name: snippet.name, id: snippet._id });
    }
  }
  return { io, unmatchedLive, unmatchedLocal: [...local].sort() };
}

/** Writes the live code, docs and description into folder for every file that doesn't exist yet. Never overwrites. */
export async function pullMissing(live: LiveCollection, folder: string): Promise<string[]> {
  const files: [string, string][] = [["readme.md", live.description]];
  for (const [name, alias] of flattenAliases(live.aliases)) {
    files.push([`${name}.alias`, alias.code], [`${name}.md`, alias.docs]);
  }
  for (const snippet of live.snippets) {
    files.push([`${snippet.name}.snippet`, snippet.code], [`${snippet.name}.md`, snippet.docs]);
  }

  const written: string[] = [];
  for (const [name, content] of files) {
    const file = path.join(folder, name);
    if (content && (await readText(file)) === undefined) {
      await fs.writeFile(file, content, "utf-8");
      written.push(name);
    }
  }
  return written;
}
