import * as path from "path";
import { describe, expect, it } from "vitest";
import { allGvarStatus, collectionStatus, compare, flattenAliases, indexGvars, SyncEntry } from "../src";
import { fakeClient, GVAR_A, GVAR_B, GVAR_C, liveCollection, liveGvars, workspace } from "./helpers";

const IO = JSON.stringify({ name: "Loot", collection: "col1", aliases: { loot: "a1", "loot roll": "a2" }, snippets: { adv: "s1" } });

function summary(entries: SyncEntry[]) {
  return entries.map((e) => [e.label, e.state]);
}

describe("compare", () => {
  it("ignores surrounding whitespace", () => {
    expect(compare("code\n", "code")).toBe("unchanged");
    expect(compare("code", "other")).toBe("modified");
    expect(compare(undefined, "code")).toBe("live-only");
    expect(compare("code", undefined)).toBe("local-only");
  });
});

describe("flattenAliases", () => {
  it("names subcommands by their path", () => {
    expect([...flattenAliases(liveCollection().aliases).keys()]).toEqual(["loot", "loot roll"]);
  });
});

describe("collectionStatus", () => {
  async function status(files: Record<string, string>, gvars = liveGvars({})) {
    const root = await workspace({ "loot/collection.io": IO, ...files });
    const { client, calls } = fakeClient({
      "GET /workshop/collection/col1/full": { data: liveCollection() },
      "GET /customizations/gvars": gvars,
    });
    const result = await collectionStatus(client, path.join(root, "loot"), await indexGvars(root));
    return { root, result, calls };
  }

  it("marks each mapped file unchanged or modified", async () => {
    const { result } = await status({
      "loot/readme.md": "Random loot.\n",
      "loot/loot.alias": "<drac2>loot</drac2>",
      "loot/loot.md": "Changed docs",
      "loot/loot roll.alias": "roll code v2",
      "loot/adv.snippet": "adv code",
    });

    expect(summary(result.items)).toEqual([
      ["readme.md", "unchanged"],
      ["adv.snippet", "unchanged"],
      ["loot roll.alias", "modified"],
      ["loot.alias", "unchanged"],
      ["loot.md", "modified"],
    ]);
  });

  it("uses an alias's own name and the workshop id", async () => {
    const { result } = await status({ "loot/loot roll.alias": "x" });
    const roll = result.items.find((e) => e.label === "loot roll.alias")!;

    expect([roll.kind, roll.part, roll.id, roll.name, roll.live]).toEqual(["alias", "code", "a2", "roll", "roll code"]);
  });

  it("shows live-only and local-only items", async () => {
    const root = await workspace({
      "loot/collection.io": JSON.stringify({ name: "Loot", collection: "col1", aliases: { loot: "a1", gone: "zz" }, snippets: {} }),
      "loot/gone.alias": "deleted live",
      "loot/new.alias": "not in collection.io",
      "loot/notes.txt": "",
    });
    const { client } = fakeClient({ "GET /workshop/collection/col1/full": { data: liveCollection({ description: "" }) } });
    const result = await collectionStatus(client, path.join(root, "loot"), new Map(), { gvars: liveGvars({}) });

    expect(summary(result.items)).toEqual([
      ["adv.snippet", "live-only"],
      ["gone.alias", "local-only"],
      ["loot roll.alias", "live-only"],
      ["loot.alias", "live-only"],
      ["loot.md", "live-only"],
      ["new.alias", "local-only"],
    ]);
  });

  it("leaves out docs and readme when neither side has them", async () => {
    const root = await workspace({ "loot/collection.io": JSON.stringify({ name: "Loot", collection: "col1", aliases: { "loot roll": "a2" }, snippets: {} }), "loot/loot roll.alias": "roll code" });
    const { client } = fakeClient({ "GET /workshop/collection/col1/full": { data: liveCollection({ description: "", aliases: [], snippets: [] }) } });
    const result = await collectionStatus(client, path.join(root, "loot"), new Map(), { gvars: liveGvars({}) });

    expect(summary(result.items)).toEqual([["loot roll.alias", "local-only"]]);
  });

  it("compares the collection's gvars with the live ones it can edit", async () => {
    const { result } = await status(
      {
        "loot/loot.alias": `using(a="${GVAR_A}", b="${GVAR_B}", c="${GVAR_C}")`,
        [`gvars/${GVAR_A}.gvar`]: "# Name: Core\nsame",
        [`gvars/${GVAR_B}.gvar`]: "someone else's",
        [`gvars/${GVAR_C}.gvar`]: "# Name: Shared\nnew",
      },
      liveGvars({ [GVAR_A]: "# Name: Core\nsame" }, { [GVAR_C]: "old" }),
    );

    expect(summary(result.gvars)).toEqual([
      [GVAR_B, "not-editable"],
      [`Core (${GVAR_A.slice(0, 8)})`, "unchanged"],
      [`Shared (${GVAR_C.slice(0, 8)})`, "modified"],
    ]);
  });

  it("fetches the collection and gvars once each", async () => {
    const { calls } = await status({});

    expect(calls.map((c) => c.path).sort()).toEqual(["/customizations/gvars", "/workshop/collection/col1/full"]);
  });
});

describe("allGvarStatus", () => {
  it("lists every editable live gvar with its local status", async () => {
    const root = await workspace({ [`gvars/${GVAR_A}.gvar`]: "# Name: Core\nnew", [`x/${GVAR_C}.gvar`]: "not mine" });
    const entries = await allGvarStatus(liveGvars({ [GVAR_A]: "old", [GVAR_B]: "live" }), await indexGvars(root));

    expect(summary(entries)).toEqual([
      [GVAR_B, "live-only"],
      [`Core (${GVAR_A.slice(0, 8)})`, "modified"],
    ]);
  });
});
