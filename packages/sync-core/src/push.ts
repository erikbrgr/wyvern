import { AvraeClient, LiveCollection } from "./api";
import { SyncEntry } from "./status";

export function isPushable(entry: SyncEntry, force = false): boolean {
  return entry.local !== undefined && (entry.state === "modified" || (force && entry.state === "unchanged"));
}

/** Pushes one entry to Avrae and returns what changed, like "code v12, now active". */
export async function pushEntry(client: AvraeClient, entry: SyncEntry, collection?: LiveCollection, force = false): Promise<string> {
  if (!isPushable(entry, force)) {
    throw new Error(`${entry.label} is ${entry.state}, nothing to push`);
  }
  const local = entry.local!;
  switch (entry.kind) {
    case "collection":
      if (!collection) {
        throw new Error("Pushing the collection description needs the live collection");
      }
      await client.updateCollectionDescription(collection, local);
      return "collection description";
    case "gvar":
      await client.updateGvar(entry.id, local);
      return `${local.length.toLocaleString("en")} chars`;
    default:
      if (entry.part === "docs") {
        await client.updateDocs(entry.kind, entry.id, entry.name, local);
        return "docs";
      }
      return `code v${await client.pushCode(entry.kind, entry.id, entry.name, local)}, now active`;
  }
}
