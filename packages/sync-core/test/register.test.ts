import { describe, expect, it } from "vitest";
import { link, matchCollection } from "../src";
import { liveCollection } from "./helpers";

describe("matchCollection", () => {
  it("maps live items to files of the same name and reports the rest", () => {
    const result = matchCollection(liveCollection(), ["loot.alias", "loot.md", "old.alias", "adv.snippet", "readme.md"]);

    expect(result).toEqual({
      io: { name: "Loot", collection: "col1", aliases: { loot: "a1" }, snippets: { adv: "s1" } },
      unmatchedLive: [{ kind: "alias", name: "loot roll", id: "a2" }],
      unmatchedLocal: ["old.alias"],
    });
  });

  it("links an unmatched item by hand", () => {
    const { io } = matchCollection(liveCollection(), []);
    link(io, { kind: "alias", name: "loot roll", id: "a2" });
    link(io, { kind: "snippet", name: "adv", id: "s1" });

    expect(io).toEqual({ name: "Loot", collection: "col1", aliases: { "loot roll": "a2" }, snippets: { adv: "s1" } });
  });
});
