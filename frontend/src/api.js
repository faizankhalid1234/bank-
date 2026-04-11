const API_PREFIX = "/api";

const TOKEN_KEY = "alybank_auth_token";

let csrfToken = null;

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function parseJsonSafe(text) {
  const t = (text || "").trim();
  if (!t) return null;
  try {
    return JSON.parse(t);
  } catch {
    return null;
  }
}

/** Prefer field errors (e.g. login password) over generic detail. */
function errorMessageFromResponse(data) {
  if (!data) return "Request failed";
  if (typeof data.detail === "string" && data.detail) {
    const errs = data.errors;
    if (errs && typeof errs === "object" && !Array.isArray(errs)) {
      const keys = Object.keys(errs);
      for (const key of keys) {
        const v = errs[key];
        if (Array.isArray(v) && v.length && typeof v[0] === "string") return v[0];
        if (typeof v === "string") return v;
      }
    }
    return data.detail;
  }
  if (Array.isArray(data.detail) && data.detail[0]) return data.detail[0];
  if (typeof data.message === "string") return data.message;
  return "Request failed";
}

export async function ensureCsrf() {
  let r;
  try {
    r = await fetch(`${API_PREFIX}/csrf/`, { credentials: "include" });
  } catch {
    throw new Error(
      "Server tak pohnch nahi saka. Django chal raha hai? Terminal mein: python manage.py runserver (port 8000), phir frontend npm run dev."
    );
  }
  const text = await r.text();
  const j = parseJsonSafe(text);
  if (!r.ok) {
    const detail =
      (j && typeof j.detail === "string" && j.detail) ||
      (j && Array.isArray(j.detail) && j.detail[0]) ||
      text?.slice(0, 200) ||
      `HTTP ${r.status}`;
    throw new Error(detail);
  }
  if (!j || typeof j.csrfToken !== "string") {
    throw new Error(
      "CSRF token nahi mila — API ne JSON nahi bheja (khali jawab). Django runserver port 8000 check karein; Vite proxy /api → 127.0.0.1:8000 hona chahiye."
    );
  }
  csrfToken = j.csrfToken;
  return csrfToken;
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const t = getAuthToken();
  if (t) {
    headers.Authorization = `Token ${t}`;
  }
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    const csrf = csrfToken || (await ensureCsrf());
    headers["X-CSRFToken"] = csrf;
  }
  let r;
  try {
    r = await fetch(`${API_PREFIX}${path}`, {
      ...options,
      credentials: "include",
      headers,
    });
  } catch {
    throw new Error(
      "Network error — Django backend nahi mil raha. Pehle `python manage.py runserver` chalayein (8000), phir register/login try karein."
    );
  }
  const text = await r.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!r.ok) {
    const msg = errorMessageFromResponse(data);
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
