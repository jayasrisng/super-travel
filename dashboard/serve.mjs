// Advisor dashboard server (no dependencies): node dashboard/serve.mjs [port]
//
// - Serves the advisor dashboard (/), the customer app (/app/) and onboarding (/onboarding/).
// - Proxies /api/* to the control API's /v1/*, adding the bearer token server-side so it
//   never reaches the browser. Token: WONDER_API_TOKEN from the environment or the repo .env.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { extname, join, normalize, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const dashboardRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = dirname(dashboardRoot);
const port = Number(process.argv[2] || process.env.PORT || 5180);
const apiBase = (process.env.WONDER_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png" };
const mounts = [
  ["/onboarding/", join(repoRoot, "super_travel", "onboarding")],
  ["/app/", join(repoRoot, "customer")],
  ["/", dashboardRoot],
];
const forwardHeaders = ["content-type", "idempotency-key", "if-match"];
const MAX_BODY = 32 * 1024;

function readToken() {
  if (process.env.WONDER_API_TOKEN) return process.env.WONDER_API_TOKEN;
  try {
    const line = readFileSync(join(repoRoot, ".env"), "utf8").split("\n").find((l) => l.startsWith("WONDER_API_TOKEN="));
    return line ? line.slice("WONDER_API_TOKEN=".length).trim() : "";
  } catch {
    return "";
  }
}
const token = readToken();

async function proxy(req, res, path) {
  if (!token) {
    res.writeHead(503, { "content-type": "application/json" })
      .end(JSON.stringify({ error: { code: "proxy_not_configured", message: "Set WONDER_API_TOKEN in .env", details: [], retryable: false } }));
    return;
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) { res.writeHead(413).end(); return; }
    chunks.push(chunk);
  }
  const headers = { authorization: `Bearer ${token}` };
  for (const name of forwardHeaders) if (req.headers[name]) headers[name] = req.headers[name];
  try {
    const upstream = await fetch(apiBase + "/v1" + path, {
      method: req.method,
      headers,
      body: ["GET", "HEAD"].includes(req.method) ? undefined : Buffer.concat(chunks),
    });
    const out = { "content-type": upstream.headers.get("content-type") || "application/json", "cache-control": "no-store" };
    const etag = upstream.headers.get("etag");
    if (etag) out.etag = etag;
    res.writeHead(upstream.status, out).end(Buffer.from(await upstream.arrayBuffer()));
  } catch {
    res.writeHead(502, { "content-type": "application/json" })
      .end(JSON.stringify({ error: { code: "api_unreachable", message: `Control API not reachable at ${apiBase}`, details: [], retryable: true } }));
  }
}

createServer(async (req, res) => {
  let url;
  try {
    url = new URL(req.url, "http://x");
    decodeURIComponent(url.pathname);
  } catch {
    res.writeHead(400, { "content-type": "text/plain" }).end("Invalid URL");
    return;
  }
  if (url.pathname.startsWith("/api/")) {
    await proxy(req, res, url.pathname.slice(4) + url.search);
    return;
  }
  const path = normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, "");
  const [prefix, root] = mounts.find(([p]) => path.startsWith(p) || path + "/" === p);
  const relative = path.slice(prefix.length - 1) || "/";
  const file = join(root, relative.endsWith("/") ? relative + "index.html" : relative);
  if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(file);
    res.writeHead(200, { "content-type": types[extname(file)] || "application/octet-stream", "cache-control": "no-store" }).end(body);
  } catch {
    res.writeHead(404, { "content-type": "text/plain" }).end("Not found");
  }
}).listen(port, "127.0.0.1", () => console.log(`Dashboard on http://localhost:${port} (API ${apiBase}${token ? "" : ", no token"})`));
