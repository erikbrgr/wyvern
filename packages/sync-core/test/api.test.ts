import { describe, expect, it } from "vitest";
import { AvraeApiError, AvraeClient, MAX_GVAR_CHARS } from "../src";
import { fakeClient, liveCollection } from "./helpers";

describe("AvraeClient", () => {
  it("sends the token and browser-like headers", async () => {
    const { client, calls } = fakeClient({ "GET /workshop/owned": { data: ["c1", "c2"] } });

    expect(await client.ownedCollectionIds()).toEqual(["c1", "c2"]);
    expect(calls[0].headers.Authorization).toBe("token-123");
    expect(calls[0].headers["Sec-Fetch-Mode"]).toBe("cors");
  });

  it("reads the full collection", async () => {
    const { client, calls } = fakeClient({ "GET /workshop/collection/col1/full": { data: liveCollection() } });

    expect((await client.collection("col1")).name).toBe("Loot");
    expect(calls[0].path).toBe("/workshop/collection/col1/full");
  });

  it("reads gvars", async () => {
    const { client } = fakeClient({ "GET /customizations/gvars": { owned: [], editable: [] } });

    expect(await client.gvars()).toEqual({ owned: [], editable: [] });
  });

  it("raises an AvraeApiError with the status on HTTP errors", async () => {
    const { client } = fakeClient({ "GET /workshop/owned": () => ({ status: 403, body: "Forbidden" }) });

    const error = await client.ownedCollectionIds().catch((e) => e);
    expect(error).toBeInstanceOf(AvraeApiError);
    expect(error.status).toBe(403);
    expect(error.message).toBe("GET /workshop/owned returned HTTP 403: Forbidden");
  });

  it("raises on a non-JSON body", async () => {
    const { client } = fakeClient({ "GET /workshop/owned": "<html>" });

    await expect(client.ownedCollectionIds()).rejects.toThrow("GET /workshop/owned returned a non-JSON body: <html>");
  });

  it("pushes code as a new version and makes it active", async () => {
    const { client, calls } = fakeClient({
      "POST /workshop/alias/a1/code": { data: { version: 7 } },
      "PUT /workshop/alias/a1/active-code": "ok",
    });

    expect(await client.pushCode("alias", "a1", "loot", "new code")).toBe(7);
    expect(calls.map((c) => [c.method, c.path, c.body])).toEqual([
      ["POST", "/workshop/alias/a1/code", { name: "loot", content: "new code" }],
      ["PUT", "/workshop/alias/a1/active-code", { version: 7 }],
    ]);
  });

  it("updates docs", async () => {
    const { client, calls } = fakeClient({ "PATCH /workshop/snippet/s1": "ok" });

    await client.updateDocs("snippet", "s1", "adv", "docs");
    expect(calls[0].body).toEqual({ name: "adv", docs: "docs" });
  });

  it("keeps the live name and image when updating the description", async () => {
    const { client, calls } = fakeClient({ "PATCH /workshop/collection/col1": "ok" });

    await client.updateCollectionDescription(liveCollection(), "New readme");
    expect(calls[0].body).toEqual({ name: "Loot", description: "New readme", image: "https://img.test/loot.png" });
  });

  it("updates a gvar by posting the live gvar with the new value", async () => {
    const live = { key: "k", owner: "1", owner_name: "me#0", value: "old", editors: ["2"] };
    const { client, calls } = fakeClient({ "GET /customizations/gvars/k": live, "POST /customizations/gvars/k": "Gvar updated." });

    await client.updateGvar("k", "new");
    expect(calls[1].body).toEqual({ ...live, value: "new" });
  });

  it("refuses a gvar over the size limit without calling the API", async () => {
    const { client, calls } = fakeClient({});

    await expect(client.updateGvar("k", "x".repeat(MAX_GVAR_CHARS + 1))).rejects.toThrow("100,001 chars, over the 100,000 gvar limit");
    expect(calls).toEqual([]);
  });

  it("defaults to the real API and global fetch", () => {
    expect(new AvraeClient("t")).toBeInstanceOf(AvraeClient);
  });
});
