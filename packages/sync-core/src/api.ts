export const API_BASE = "https://api.avrae.io";
export const MAX_GVAR_CHARS = 100_000;

export type ItemKind = "alias" | "snippet";

export interface LiveAlias {
  _id: string;
  name: string;
  code: string;
  docs: string;
  subcommands: LiveAlias[];
}

export interface LiveSnippet {
  _id: string;
  name: string;
  code: string;
  docs: string;
}

export interface LiveCollection {
  _id: string;
  name: string;
  description: string;
  image: string | null;
  aliases: LiveAlias[];
  snippets: LiveSnippet[];
}

export interface LiveGvar {
  key: string;
  owner: string;
  owner_name: string;
  value: string;
  editors: string[];
}

export interface LiveGvars {
  owned: LiveGvar[];
  editable: LiveGvar[];
}

export class AvraeApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "AvraeApiError";
  }
}

// Same header set as avrae-vscode: Avrae's API doesn't return real JSON to requests that don't look like a browser.
const HEADERS = {
  Accept: "application/json, text/plain, */*",
  "Content-Type": "application/json",
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
  "Sec-Fetch-Site": "same-site",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Dest": "empty",
};

export class AvraeClient {
  private readonly baseUrl: string;
  private readonly fetch: typeof fetch;

  constructor(
    private readonly token: string,
    options: { baseUrl?: string; fetch?: typeof fetch } = {},
  ) {
    this.baseUrl = options.baseUrl ?? API_BASE;
    this.fetch = options.fetch ?? globalThis.fetch;
  }

  async request(method: string, path: string, body?: unknown): Promise<string> {
    const response = await this.fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { ...HEADERS, Authorization: this.token },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    if (!response.ok) {
      throw new AvraeApiError(`${method} ${path} returned HTTP ${response.status}: ${text.slice(0, 300)}`, response.status);
    }
    return text;
  }

  async json<T>(method: string, path: string, body?: unknown): Promise<T> {
    const text = await this.request(method, path, body);
    try {
      return JSON.parse(text) as T;
    } catch {
      throw new AvraeApiError(`${method} ${path} returned a non-JSON body: ${text.slice(0, 300)}`, 200);
    }
  }

  async ownedCollectionIds(): Promise<string[]> {
    return (await this.json<{ data: string[] }>("GET", "/workshop/owned")).data;
  }

  async collection(id: string): Promise<LiveCollection> {
    return (await this.json<{ data: LiveCollection }>("GET", `/workshop/collection/${id}/full`)).data;
  }

  async gvars(): Promise<LiveGvars> {
    return this.json<LiveGvars>("GET", "/customizations/gvars");
  }

  async gvar(key: string): Promise<LiveGvar> {
    return this.json<LiveGvar>("GET", `/customizations/gvars/${key}`);
  }

  async pushCode(kind: ItemKind, id: string, name: string, code: string): Promise<number> {
    const result = await this.json<{ data: { version: number } }>("POST", `/workshop/${kind}/${id}/code`, { name, content: code });
    const version = result.data.version;
    await this.request("PUT", `/workshop/${kind}/${id}/active-code`, { version });
    return version;
  }

  async updateDocs(kind: ItemKind, id: string, name: string, docs: string): Promise<void> {
    await this.request("PATCH", `/workshop/${kind}/${id}`, { name, docs });
  }

  async updateCollectionDescription(collection: LiveCollection, description: string): Promise<void> {
    // PATCH replaces the name and image too, so the live values are carried over.
    await this.request("PATCH", `/workshop/collection/${collection._id}`, {
      name: collection.name,
      description,
      image: collection.image,
    });
  }

  async updateGvar(key: string, value: string): Promise<void> {
    if (value.length > MAX_GVAR_CHARS) {
      throw new Error(`${value.length.toLocaleString("en")} chars, over the ${MAX_GVAR_CHARS.toLocaleString("en")} gvar limit`);
    }
    const live = await this.gvar(key);
    await this.request("POST", `/customizations/gvars/${key}`, { ...live, value });
  }
}
