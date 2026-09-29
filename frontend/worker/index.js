// Serves the static Next.js export and proxies /api/* to the FastAPI backend.
// The backend only accepts requests carrying INTERNAL_API_TOKEN, so the API is
// reachable solely through this Worker (which sits behind Cloudflare Access).
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      const target = new URL(url.pathname + url.search, env.BACKEND_URL);
      const headers = new Headers(request.headers);
      headers.set("X-Internal-Token", env.INTERNAL_API_TOKEN);
      // Don't leak the Access session cookie/JWT to the backend.
      headers.delete("cookie");
      headers.delete("cf-access-jwt-assertion");

      return fetch(target, {
        method: request.method,
        headers,
        body: request.body,
        redirect: "manual"
      });
    }

    return env.ASSETS.fetch(request);
  }
};
