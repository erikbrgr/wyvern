import { promises as fs } from "fs";
import * as path from "path";
import { describe, expect, it } from "vitest";
import {
  collectionGvars,
  findCollections,
  gvarHeader,
  gvarKeyFromPath,
  indexGvars,
  readCollectionIo,
  readText,
  usedGvarKeys,
  writeCollectionIo,
} from "../src";
import { GVAR_A, GVAR_B, GVAR_C, workspace } from "./helpers";

const IO = JSON.stringify({ name: "Loot", collection: "col1", aliases: { loot: "a1" }, snippets: { adv: "s1" } });

describe("collections", () => {
  it("finds every collection.io folder, skipping dot folders and node_modules", async () => {
    const root = await workspace({
      "shared/loot/collection.io": IO,
      "eden/games/collection.io": IO,
      ".wyvern/x/collection.io": IO,
      "node_modules/y/collection.io": IO,
    });

    expect(await findCollections(root)).toEqual([path.join(root, "eden/games"), path.join(root, "shared/loot")]);
  });

  it("reads collection.io with missing sections defaulted", async () => {
    const root = await workspace({ "collection.io": JSON.stringify({ name: "X", collection: "c" }) });

    expect(await readCollectionIo(root)).toEqual({ name: "X", collection: "c", aliases: {}, snippets: {} });
  });

  it("writes collection.io as compact JSON, like avrae-vscode", async () => {
    const root = await workspace({});
    await writeCollectionIo(root, { name: "Loot", collection: "col1", aliases: { loot: "a1" }, snippets: {} });

    expect(await readText(path.join(root, "collection.io"))).toBe('{"name":"Loot","collection":"col1","aliases":{"loot":"a1"},"snippets":{}}');
  });

  it("returns undefined for a missing file and rethrows other errors", async () => {
    const root = await workspace({ "dir/x": "" });

    expect(await readText(path.join(root, "missing"))).toBe(undefined);
    await expect(readText(path.join(root, "dir"))).rejects.toThrow();
  });
});

describe("gvars", () => {
  it("takes the key from a gvar file name", () => {
    expect(gvarKeyFromPath(`/x/${GVAR_A.toUpperCase()}.gvar`)).toBe(GVAR_A);
    expect(gvarKeyFromPath(`/x/${GVAR_A}.gvar.yaml`)).toBe(GVAR_A);
    expect(gvarKeyFromPath(`/x/hazards-${GVAR_A}.yaml`)).toBe(GVAR_A);
    expect(gvarKeyFromPath(`/x/${GVAR_A}.alias`)).toBe(undefined);
    expect(gvarKeyFromPath("/x/notes.gvar")).toBe(undefined);
  });

  it("indexes gvar files outside dot folders", async () => {
    const root = await workspace({
      [`gvars/${GVAR_A}.gvar`]: "",
      [`shared/tower/${GVAR_B}.yaml`]: "",
      [`.wyvern/usings/${GVAR_C}.gvar`]: "",
    });

    expect(await indexGvars(root)).toEqual(
      new Map([
        [GVAR_A, path.join(root, `gvars/${GVAR_A}.gvar`)],
        [GVAR_B, path.join(root, `shared/tower/${GVAR_B}.yaml`)],
      ]),
    );
  });

  it("keeps the first file when a key appears twice", async () => {
    const root = await workspace({ [`a/${GVAR_A}.gvar`]: "", [`b/${GVAR_A}.gvar`]: "" });

    expect((await indexGvars(root)).get(GVAR_A)).toBe(path.join(root, `a/${GVAR_A}.gvar`));
  });

  it("finds gvar keys inside using() only", () => {
    const code = `using(\n  core="${GVAR_A.toUpperCase()}",\n  x="${GVAR_B}"\n)\nget_gvar("${GVAR_C}")`;

    expect(usedGvarKeys(code)).toEqual([GVAR_A, GVAR_B]);
  });

  it("reads gvar headers", () => {
    const source = "# Name: Core\n# Owner: erikbrgr\n\ncode";

    expect(gvarHeader(source, "Name")).toBe("Core");
    expect(gvarHeader(source, "Purpose")).toBe(undefined);
  });

  it("collects the folder's gvars and follows using() transitively", async () => {
    const root = await workspace({
      "shared/loot/collection.io": IO,
      "shared/loot/loot.alias": `using(core="${GVAR_A}")`,
      "shared/loot/adv.snippet": "no gvars",
      [`shared/loot/${GVAR_B}.yaml`]: "data: 1",
      [`gvars/${GVAR_A}.gvar`]: `using(lib="${GVAR_C}", missing="dddddddd-4444-4444-8444-444444444444")`,
      [`gvars/${GVAR_C}.gvar`]: `using(core="${GVAR_A}")`,
    });
    const folder = path.join(root, "shared/loot");

    expect(await collectionGvars(folder, await readCollectionIo(folder), await indexGvars(root))).toEqual([
      path.join(folder, `${GVAR_B}.yaml`),
      path.join(root, `gvars/${GVAR_A}.gvar`),
      path.join(root, `gvars/${GVAR_C}.gvar`),
    ]);
  });

  it("does not follow into gvars that only live in .wyvern/usings", async () => {
    const root = await workspace({
      "c/collection.io": IO,
      "c/loot.alias": `using(other="${GVAR_C}")`,
      [`.wyvern/usings/${GVAR_C}.gvar`]: "",
    });
    const folder = path.join(root, "c");

    expect(await collectionGvars(folder, await readCollectionIo(folder), await indexGvars(root))).toEqual([]);
  });

  it("ignores folder files without a gvar key", async () => {
    const root = await workspace({ "c/collection.io": IO, "c/notes.yaml": "" });
    await fs.mkdir(path.join(root, "c/sub"));

    expect(await collectionGvars(path.join(root, "c"), await readCollectionIo(path.join(root, "c")), new Map())).toEqual([]);
  });
});
