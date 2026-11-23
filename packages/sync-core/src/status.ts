import { promises as fs } from "fs";
import * as path from "path";
import { AvraeClient, LiveAlias, LiveCollection, LiveGvar, LiveGvars } from "./api";
import { collectionGvars, CollectionIo, gvarHeader, gvarKeyFromPath, readCollectionIo, readText } from "./workspace";

export type SyncState = "unchanged" | "modified" | "local-only" | "live-only" | "not-editable" | "ignored";

export interface SyncEntry {
  kind: "collection" | "alias" | "snippet" | "gvar";
  part: "description" | "code" | "docs" | "value";
  /** What the user sees: the file name, or "Name (1a2b3c4d)" for a gvar. */
  label: string;
  /** The local file, when there is one. */
  file?: string;
  /** Workshop id of the collection, alias or snippet, or the gvar key. */
  id: string;
  /** The alias's own name (not its "parent child" path), the snippet name, or the gvar's '# Name:' header. */
  name: string;
  local?: string;
  live?: string;
  state: SyncState;
}

export interface CollectionStatus {
  folder: string;
  io: CollectionIo;
  live: LiveCollection;
  /** The description, then aliases and snippets (code and docs), sorted by label. */
  items: SyncEntry[];
  /** The gvars this collection pushes: its own folder's, plus what they and its code reach through using(). */
  gvars: SyncEntry[];
}

export function compare(local: string | undefined, live: string | undefined): SyncState {
  if (local === undefined) {
    return "live-only";
  }
  if (live === undefined) {
    return "local-only";
  }
  return local.trim() === live.trim() ? "unchanged" : "modified";
}

/** Live aliases by their collection.io name: "parent child" for subcommands. */
export function flattenAliases(aliases: LiveAlias[], parent = ""): Map<string, LiveAlias> {
  const out = new Map<string, LiveAlias>();
  for (const alias of aliases) {
    const name = `${parent} ${alias.name}`.trim();
    out.set(name, alias);
    for (const [childName, child] of flattenAliases(alias.subcommands ?? [], name)) {
      out.set(childName, child);
    }
  }
  return out;
}

export function liveGvarsByKey(gvars: LiveGvars): Map<string, LiveGvar> {
  return new Map([...gvars.owned, ...gvars.editable].map((gvar) => [gvar.key.toLowerCase(), gvar]));
}

export function gvarEntry(key: string, file: string | undefined, local: string | undefined, live: LiveGvar | undefined, ignored: Set<string>): SyncEntry {
  const name = (local !== undefined ? gvarHeader(local, "Name") : undefined) ?? "";
  const entry: SyncEntry = {
    kind: "gvar",
    part: "value",
    label: name ? `${name} (${key.slice(0, 8)})` : key,
    file,
    id: key,
    name,
    local,
    live: live?.value,
    state: compare(local, live?.value),
  };
  if (ignored.has(key)) {
    entry.state = "ignored";
  } else if (local !== undefined && live === undefined) {
    entry.state = "not-editable";
  }
  return entry;
}

/** Every gvar the token's user owns or can edit, matched with a local file wherever the workspace has one. */
export async function allGvarStatus(gvars: LiveGvars, index: Map<string, string>, ignored = new Set<string>()): Promise<SyncEntry[]> {
  const entries: SyncEntry[] = [];
  for (const [key, live] of liveGvarsByKey(gvars)) {
    const file = index.get(key);
    entries.push(gvarEntry(key, file, file ? await readText(file) : undefined, live, ignored));
  }
  return entries.sort(byLabel);
}

function byLabel(a: SyncEntry, b: SyncEntry): number {
  return a.label.toLowerCase().localeCompare(b.label.toLowerCase());
}

async function itemEntries(folder: string, io: CollectionIo, live: LiveCollection): Promise<SyncEntry[]> {
  const entries: SyncEntry[] = [];
  const liveAliases = flattenAliases(live.aliases);
  const liveById = new Map<string, { name: string; code: string; docs: string }>(
    [...liveAliases.values(), ...live.snippets].map((item) => [item._id, item]),
  );
  const mappedIds = new Set<string>();

  for (const [kind, mapping, ext] of [
    ["alias", io.aliases, ".alias"],
    ["snippet", io.snippets, ".snippet"],
  ] as const) {
    for (const [base, id] of Object.entries(mapping)) {
      mappedIds.add(id);
      const item = liveById.get(id);
      // The API wants an alias's own name, not its "parent child" path.
      const name = kind === "alias" ? base.split(" ").pop()! : base;
      for (const [part, suffix] of [
        ["code", ext],
        ["docs", ".md"],
      ] as const) {
        const file = path.join(folder, base + suffix);
        const local = await readText(file);
        const liveText = part === "code" ? item?.code : item?.docs || undefined;
        if (local === undefined && liveText === undefined) {
          continue;
        }
        entries.push({ kind, part, label: base + suffix, file, id, name, local, live: liveText, state: compare(local, liveText) });
      }
    }
  }

  for (const [base, alias] of liveAliases) {
    if (!mappedIds.has(alias._id)) {
      entries.push({ kind: "alias", part: "code", label: `${base}.alias`, id: alias._id, name: alias.name, live: alias.code, state: "live-only" });
    }
  }
  for (const snippet of live.snippets) {
    if (!mappedIds.has(snippet._id)) {
      entries.push({ kind: "snippet", part: "code", label: `${snippet.name}.snippet`, id: snippet._id, name: snippet.name, live: snippet.code, state: "live-only" });
    }
  }

  const mappedFiles = new Set([...Object.keys(io.aliases).map((n) => `${n}.alias`), ...Object.keys(io.snippets).map((n) => `${n}.snippet`)]);
  for (const name of await fs.readdir(folder)) {
    const kind = name.endsWith(".alias") ? "alias" : name.endsWith(".snippet") ? "snippet" : undefined;
    if (kind && !mappedFiles.has(name)) {
      const file = path.join(folder, name);
      const base = name.slice(0, name.lastIndexOf("."));
      entries.push({ kind, part: "code", label: name, file, id: "", name: base, local: await readText(file), state: "local-only" });
    }
  }
  return entries.sort(byLabel);
}

/** Compares a collection folder with the live collection it names, and with the gvars it pushes. */
export async function collectionStatus(
  client: AvraeClient,
  folder: string,
  index: Map<string, string>,
  options: { gvars?: LiveGvars; ignoredGvars?: Set<string> } = {},
): Promise<CollectionStatus> {
  const io = await readCollectionIo(folder);
  const [live, gvars] = await Promise.all([client.collection(io.collection), options.gvars ?? client.gvars()]);
  const ignored = options.ignoredGvars ?? new Set<string>();

  const items = await itemEntries(folder, io, live);
  const readme = path.join(folder, "readme.md");
  const local = await readText(readme);
  if (local !== undefined || live.description) {
    items.unshift({
      kind: "collection",
      part: "description",
      label: "readme.md",
      file: readme,
      id: live._id,
      name: live.name,
      local,
      live: live.description || undefined,
      state: compare(local, live.description || undefined),
    });
  }

  const liveGvars = liveGvarsByKey(gvars);
  const gvarEntries: SyncEntry[] = [];
  for (const file of await collectionGvars(folder, io, index)) {
    const key = gvarKeyFromPath(file)!;
    gvarEntries.push(gvarEntry(key, file, await readText(file), liveGvars.get(key), ignored));
  }

  return { folder, io, live, items, gvars: gvarEntries.sort(byLabel) };
}
