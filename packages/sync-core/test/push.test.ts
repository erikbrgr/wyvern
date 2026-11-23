import { describe, expect, it } from "vitest";
import { isPushable, pushEntry, SyncEntry } from "../src";
import { fakeClient, liveCollection } from "./helpers";

function entry(overrides: Partial<SyncEntry>): SyncEntry {
  return { kind: "alias", part: "code", label: "loot.alias", id: "a1", name: "loot", local: "new", live: "old", state: "modified", ...overrides };
}

describe("isPushable", () => {
  it("pushes modified entries, and unchanged ones only when forced", () => {
    expect(isPushable(entry({}))).toBe(true);
    expect(isPushable(entry({ state: "unchanged" }))).toBe(false);
    expect(isPushable(entry({ state: "unchanged" }), true)).toBe(true);
    expect(isPushable(entry({ state: "not-editable" }), true)).toBe(false);
    expect(isPushable(entry({ state: "live-only", local: undefined }), true)).toBe(false);
  });
});

describe("pushEntry", () => {
  it("pushes alias code as the active version", async () => {
    const { client, calls } = fakeClient({ "POST /workshop/alias/a1/code": { data: { version: 3 } }, "PUT /workshop/alias/a1/active-code": "" });

    expect(await pushEntry(client, entry({}))).toBe("code v3, now active");
    expect(calls.length).toBe(2);
  });

  it("pushes docs", async () => {
    const { client, calls } = fakeClient({ "PATCH /workshop/snippet/s1": "" });

    expect(await pushEntry(client, entry({ kind: "snippet", part: "docs", id: "s1", name: "adv" }))).toBe("docs");
    expect(calls[0].body).toEqual({ name: "adv", docs: "new" });
  });

  it("pushes the collection description", async () => {
    const { client, calls } = fakeClient({ "PATCH /workshop/collection/col1": "" });

    expect(await pushEntry(client, entry({ kind: "collection", part: "description" }), liveCollection())).toBe("collection description");
    expect(calls[0].body).toEqual({ name: "Loot", description: "new", image: "https://img.test/loot.png" });
  });

  it("needs the live collection for the description", async () => {
    const { client } = fakeClient({});

    await expect(pushEntry(client, entry({ kind: "collection", part: "description" }))).rejects.toThrow("needs the live collection");
  });

  it("pushes gvars", async () => {
    const { client } = fakeClient({ "GET /customizations/gvars/k": { key: "k", value: "old" }, "POST /customizations/gvars/k": "Gvar updated." });

    expect(await pushEntry(client, entry({ kind: "gvar", part: "value", id: "k", local: "x".repeat(1234) }))).toBe("1,234 chars");
  });

  it("refuses entries that aren't pushable", async () => {
    const { client, calls } = fakeClient({});

    await expect(pushEntry(client, entry({ state: "unchanged" }))).rejects.toThrow("loot.alias is unchanged, nothing to push");
    expect(calls).toEqual([]);
  });
});
