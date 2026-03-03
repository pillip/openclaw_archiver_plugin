import { describe, it, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { resolveServerUrl } from "./index.js";

// ---------- resolveServerUrl ----------

describe("resolveServerUrl", () => {
  const saved = process.env.OPENCLAW_ARCHIVER_URL;

  beforeEach(() => {
    delete process.env.OPENCLAW_ARCHIVER_URL;
  });

  after(() => {
    if (saved !== undefined) {
      process.env.OPENCLAW_ARCHIVER_URL = saved;
    } else {
      delete process.env.OPENCLAW_ARCHIVER_URL;
    }
  });

  it("returns default URL when no config or env", () => {
    const result = resolveServerUrl();
    assert.equal(result.url, "http://127.0.0.1:8201");
    assert.equal(result.source, "default");
  });

  it("returns default URL when config is undefined", () => {
    const result = resolveServerUrl(undefined);
    assert.equal(result.source, "default");
  });

  it("returns default URL when config has no serverUrl", () => {
    const result = resolveServerUrl({});
    assert.equal(result.source, "default");
  });

  it("uses config serverUrl when provided", () => {
    const result = resolveServerUrl({ serverUrl: "http://custom:9000" });
    assert.equal(result.url, "http://custom:9000");
    assert.equal(result.source, "config");
  });

  it("uses env var when no config serverUrl", () => {
    process.env.OPENCLAW_ARCHIVER_URL = "http://env-host:7777";
    const result = resolveServerUrl();
    assert.equal(result.url, "http://env-host:7777");
    assert.equal(result.source, "env");
  });

  it("config takes priority over env var", () => {
    process.env.OPENCLAW_ARCHIVER_URL = "http://env-host:7777";
    const result = resolveServerUrl({ serverUrl: "http://config-host:8888" });
    assert.equal(result.url, "http://config-host:8888");
    assert.equal(result.source, "config");
  });

  it("ignores empty string in config serverUrl", () => {
    const result = resolveServerUrl({ serverUrl: "" });
    assert.equal(result.source, "default");
  });
});

// ---------- plugin export ----------

describe("plugin export", () => {
  let plugin: any;

  before(async () => {
    const mod = await import("./index.js");
    plugin = mod.default;
  });

  it("has correct id and name", () => {
    assert.equal(plugin.id, "openclaw-archiver");
    assert.equal(plugin.name, "OpenClaw Archiver");
  });

  it("has a register function", () => {
    assert.equal(typeof plugin.register, "function");
  });

  it("registers /archive command via api.registerCommand", () => {
    let registered: any = null;
    const fakeApi = {
      config: {},
      logger: { info: () => {}, error: () => {} },
      registerCommand: (cmd: any) => {
        registered = cmd;
      },
    };

    plugin.register(fakeApi);

    assert.ok(registered, "registerCommand should have been called");
    assert.equal(registered.name, "archive");
    assert.equal(registered.acceptsArgs, true);
    assert.equal(typeof registered.handler, "function");
  });
});

// ---------- handler ----------

describe("handler", () => {
  let handler: (ctx: any) => Promise<{ text: string }>;

  before(async () => {
    const mod = await import("./index.js");
    let registered: any = null;
    const fakeApi = {
      config: { serverUrl: "http://127.0.0.1:19999" },
      logger: { info: () => {}, error: () => {} },
      registerCommand: (cmd: any) => {
        registered = cmd;
      },
    };
    mod.default.register(fakeApi);
    handler = registered.handler;
  });

  it("returns error message when server is unreachable", async () => {
    const result = await handler({ args: "help", senderId: "U123" });
    assert.ok(result.text.includes("Could not reach the Archiver server"));
  });

  it("uses 'unknown' when senderId is missing", async () => {
    // Should not throw — senderId falls back to "unknown"
    const result = await handler({ args: "list" });
    assert.ok(result.text.includes("Could not reach"));
  });
});
