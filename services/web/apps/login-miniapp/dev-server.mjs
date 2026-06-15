const root = import.meta.dir;
const apiOrigin = process.env.API_ORIGIN ?? "http://localhost:3000";
const port = Number(process.env.PORT ?? 5173);

const mime = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
};

function resolvePath(pathname) {
  let path = pathname;
  if (path.startsWith("/miniapp/")) {
    path = path.slice("/miniapp".length);
  }
  if (path === "/" || path === "") {
    path = "/index.html";
  }
  return `${root}${path}`;
}

Bun.serve({
  port,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname.startsWith("/api/")) {
      const target = `${apiOrigin}${url.pathname}${url.search}`;
      const headers = new Headers(req.headers);
      return fetch(target, {
        method: req.method,
        headers,
        body: req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
      });
    }

    const filePath = resolvePath(url.pathname);
    const file = Bun.file(filePath);
    if (!(await file.exists())) {
      return new Response("Not found", { status: 404 });
    }

    const ext = filePath.slice(filePath.lastIndexOf("."));
    return new Response(file, {
      headers: { "Content-Type": mime[ext] ?? "application/octet-stream" },
    });
  },
});

console.log(`login-miniapp dev server: http://localhost:${port}/miniapp/`);
