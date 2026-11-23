import { promises as fs } from "fs";
import * as path from "path";
import { describe, expect, it } from "vitest";
import { matchCollection, pullMissing, readText } from "../src";
import { liveCollection, workspace } from "./helpers";

describe("matchCollection", () => {
  it("maps every live item and reports what has no file on either side", () => {
    const result = matchCollection(liveCollection(), ["loot.alias", "loot.md", "old.alias", "adv.snippet", "readme.md"]);

    expect(result).toEqual({
      io: { name: "Loot", collection: "col1", aliases: { loot: "a1", "loot roll": "a2" }, snippets: { adv: "s1" } },
      unmatchedLive: [{ kind: "alias", name: "loot roll", id: "a2" }],
      unmatchedLocal: ["old.alias"],
    });
  });

  it("maps a collection into an empty folder", () => {
    const result = matchCollection(liveCollection(), []);

    expect(result.io.aliases).toEqual({ loot: "a1", "loot roll": "a2" });
    expect(result.unmatchedLive.map((item) => item.name)).toEqual(["loot", "loot roll", "adv"]);
  });
});

describe("pullMissing", () => {
  it("writes code, non-empty docs and the readme, keeping files that exist", async () => {
    const root = await workspace({ "loot.alias": "my local version" });

    expect(await pullMissing(liveCollection(), root)).toEqual(["readme.md", "loot.md", "loot roll.alias", "adv.snippet"]);
    expect(await readText(path.join(root, "loot.alias"))).toBe("my local version");
    expect(await readText(path.join(root, "loot roll.alias"))).toBe("roll code");
    expect((await fs.readdir(root)).sort()).toEqual(["adv.snippet", "loot roll.alias", "loot.alias", "loot.md", "readme.md"]);
  });
});
