import { promises as fs } from "fs";
import * as path from "path";

export const COLLECTION_IO = "collection.io";
export const GVAR_EXTENSIONS = [".gvar", ".gvar.yaml", ".yaml"];
const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const UUID_RE = new RegExp(UUID, "i");
const USING_RE = /using\s*\(([\s\S]*?)\)/g;

/** avrae-vscode's collection.io: alias names ("parent child" for subcommands) and snippet names mapped to workshop ids. */
export interface CollectionIo {
  name: string;
  collection: string;
  aliases: Record<string, string>;
  snippets: Record<string, string>;
}

export async function readText(file: string): Promise<string | undefined> {
  try {
    return await fs.readFile(file, "utf-8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return undefined;
    }
    throw error;
  }
}

export async function readCollectionIo(folder: string): Promise<CollectionIo> {
  const raw = JSON.parse((await readText(path.join(folder, COLLECTION_IO))) ?? "{}");
  return { name: raw.name ?? "", collection: raw.collection ?? "", aliases: raw.aliases ?? {}, snippets: raw.snippets ?? {} };
}

export async function writeCollectionIo(folder: string, io: CollectionIo): Promise<void> {
  await fs.writeFile(path.join(folder, COLLECTION_IO), JSON.stringify(io), "utf-8");
}

async function* walk(root: string): AsyncGenerator<string> {
  for (const entry of await fs.readdir(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      // Skipping dot folders also skips .wyvern/usings: someone else's gvars, pulled in by Wyvern LSP for completions.
      if (!entry.name.startsWith(".") && entry.name !== "node_modules" && entry.name !== "__pycache__") {
        yield* walk(full);
      }
    } else {
      yield full;
    }
  }
}

/** Every folder under root that holds a collection.io. */
export async function findCollections(root: string): Promise<string[]> {
  const folders: string[] = [];
  for await (const file of walk(root)) {
    if (path.basename(file) === COLLECTION_IO) {
      folders.push(path.dirname(file));
    }
  }
  return folders.sort();
}

export function gvarKeyFromPath(file: string): string | undefined {
  const name = path.basename(file);
  if (!GVAR_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return undefined;
  }
  return name.match(UUID_RE)?.[0].toLowerCase();
}

/** Local gvar files by key: files named after a gvar id. */
export async function indexGvars(root: string): Promise<Map<string, string>> {
  const index = new Map<string, string>();
  for await (const file of walk(root)) {
    const key = gvarKeyFromPath(file);
    if (key && !index.has(key)) {
      index.set(key, file);
    }
  }
  return index;
}

export function usedGvarKeys(code: string): string[] {
  return [...code.matchAll(USING_RE)].flatMap((block) => [...block[1].matchAll(new RegExp(UUID, "gi"))].map((m) => m[0].toLowerCase()));
}

export async function listGvarFiles(folder: string): Promise<string[]> {
  const names = await fs.readdir(folder);
  return names
    .filter((name) => gvarKeyFromPath(name))
    .sort()
    .map((name) => path.join(folder, name));
}

/**
 * The gvar files a collection pushes: the gvar files in its own folder, then every local gvar reachable
 * through using() from its aliases, snippets and those gvars, followed transitively.
 */
export async function collectionGvars(folder: string, io: CollectionIo, index: Map<string, string>): Promise<string[]> {
  const files = await listGvarFiles(folder);
  const seen = new Set(files.map((file) => gvarKeyFromPath(file)!));
  const queue: string[] = [];
  const sources = [
    ...Object.keys(io.aliases).map((name) => `${name}.alias`),
    ...Object.keys(io.snippets).map((name) => `${name}.snippet`),
  ];
  for (const source of sources) {
    queue.push(...usedGvarKeys((await readText(path.join(folder, source))) ?? ""));
  }
  for (const file of files) {
    queue.push(...usedGvarKeys((await readText(file)) ?? ""));
  }

  while (queue.length) {
    const key = queue.shift()!;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    const file = index.get(key);
    if (!file) {
      continue;
    }
    files.push(file);
    queue.push(...usedGvarKeys((await readText(file)) ?? ""));
  }
  return files;
}

/** Reads a '# <field>:' header line from gvar source, like '# Name: Core'. */
export function gvarHeader(source: string, field: string): string | undefined {
  const prefix = `# ${field}:`;
  return source
    .split("\n")
    .find((line) => line.startsWith(prefix))
    ?.slice(prefix.length)
    .trim();
}
