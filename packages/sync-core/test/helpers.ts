import { promises as fs } from "fs";
import * as os from "os";
import * as path from "path";
import { AvraeClient, LiveCollection, LiveGvars } from "../src";

export interface Call {
  method: string;
  path: string;
  body?: unknown;
  headers: Record<string, string>;
}

type Route = (body: unknown) => { status?: number; body: unknown };

/** An AvraeClient backed by canned responses keyed by "METHOD /path", recording every call. */
export function fakeClient(routes: Record<string, Route | unknown>): { client: AvraeClient; calls: Call[] } {
  const calls: Call[] = [];
  const fakeFetch = async (url: string | URL | Request, init?: RequestInit) => {
    const pathname = String(url).replace("https://api.test", "");
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ method, path: pathname, body, headers: init?.headers as Record<string, string> });
    const route = routes[`${method} ${pathname}`];
    if (route === undefined) {
      return new Response(`no route for ${method} ${pathname}`, { status: 404 });
    }
    const result = typeof route === "function" ? (route as Route)(body) : { body: route };
    const text = typeof result.body === "string" ? result.body : JSON.stringify(result.body);
    return new Response(text, { status: result.status ?? 200 });
  };
  return { client: new AvraeClient("token-123", { baseUrl: "https://api.test", fetch: fakeFetch as typeof fetch }), calls };
}

/** A temporary folder holding the given files (paths relative to it). */
export async function workspace(files: Record<string, string>): Promise<string> {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "sync-core-"));
  for (const [name, content] of Object.entries(files)) {
    await fs.mkdir(path.dirname(path.join(root, name)), { recursive: true });
    await fs.writeFile(path.join(root, name), content);
  }
  return root;
}

export const GVAR_A = "aaaaaaaa-1111-4111-8111-111111111111";
export const GVAR_B = "bbbbbbbb-2222-4222-8222-222222222222";
export const GVAR_C = "cccccccc-3333-4333-8333-333333333333";

export function liveCollection(overrides: Partial<LiveCollection> = {}): LiveCollection {
  return {
    _id: "col1",
    name: "Loot",
    description: "Random loot.",
    image: "https://img.test/loot.png",
    aliases: [
      {
        _id: "a1",
        name: "loot",
        code: "<drac2>loot</drac2>",
        docs: "Loot docs",
        subcommands: [{ _id: "a2", name: "roll", code: "roll code", docs: "", subcommands: [] }],
      },
    ],
    snippets: [{ _id: "s1", name: "adv", code: "adv code", docs: "" }],
    ...overrides,
  };
}

export function liveGvars(values: Record<string, string>, editable: Record<string, string> = {}): LiveGvars {
  const gvar = (key: string, value: string) => ({ key, owner: "1", owner_name: "me#0", value, editors: [] });
  return {
    owned: Object.entries(values).map(([key, value]) => gvar(key, value)),
    editable: Object.entries(editable).map(([key, value]) => gvar(key, value)),
  };
}
