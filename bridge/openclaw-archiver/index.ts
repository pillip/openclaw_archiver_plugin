/**
 * OpenClaw bridge plugin — forwards /archive commands to the Python HTTP server.
 *
 * Uses Node built-in `fetch` (Node 18+). Zero npm runtime dependencies.
 *
 * URL resolution order:
 *   1. Plugin config `serverUrl` (from openclaw.plugin.json / gateway config)
 *   2. Environment variable `OPENCLAW_ARCHIVER_URL`
 *   3. Default: http://127.0.0.1:8201
 */

const DEFAULT_URL = "http://127.0.0.1:8201";

interface PluginResponse {
  response: string | null;
}

export function resolveServerUrl(config?: { serverUrl?: string }): {
  url: string;
  source: "config" | "env" | "default";
} {
  if (config?.serverUrl) {
    return { url: config.serverUrl, source: "config" };
  }
  if (process.env.OPENCLAW_ARCHIVER_URL) {
    return { url: process.env.OPENCLAW_ARCHIVER_URL, source: "env" };
  }
  return { url: DEFAULT_URL, source: "default" };
}

export default {
  id: "openclaw-archiver",
  name: "OpenClaw Archiver",

  register(api: any) {
    const { url: archiverUrl, source } = resolveServerUrl(api.config);
    api.logger?.info?.(`server URL: ${archiverUrl} (source: ${source})`);

    api.registerCommand({
      name: "archive",
      description: "Manage saved Slack message links — save, list, search, edit, remove, project",
      acceptsArgs: true,
      handler: async (ctx: any) => {
        const text = `/archive ${ctx.args ?? ""}`.trim();
        const senderId = ctx.senderId ?? ctx.from ?? "unknown";

        try {
          const res = await fetch(`${archiverUrl}/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, user_id: senderId }),
          });

          if (!res.ok) {
            return {
              text: `Archiver server returned an error (${res.status}). Please try again later.`,
            };
          }

          const data: PluginResponse = await res.json();
          return { text: data.response ?? "" };
        } catch (err) {
          api.logger?.error?.(`fetch failed: ${err instanceof Error ? err.message : String(err)}`);
          return {
            text: "Could not reach the Archiver server. Is it running?",
          };
        }
      },
    });
  },
};
