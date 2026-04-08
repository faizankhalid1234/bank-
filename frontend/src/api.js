const API_PREFIX = "/api";

let csrfToken = null;

export async function ensureCsrf() {
  const r = await fetch(`${API_PREFIX}/csrf/`, { credentials: "include" });
  const j = await r.json();
  csrfToken = j.csrfToken;
  return csrfToken;
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    const csrf = csrfToken || (await ensureCsrf());
    headers["X-CSRFToken"] = csrf;
  }
  const r = await fetch(`${API_PREFIX}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
  const text = await r.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!r.ok) {
    const msg =
      (typeof data?.detail === "string" && data.detail) ||
      data?.detail?.[0] ||
      data?.message ||
      "Request failed";
    const err = new Error(msg);
    err.status = r.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  get(path) {
    return apiFetch(path, { method: "GET" });
  },
  post(path, body) {
    return apiFetch(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : "{}",
    });
  },
};
