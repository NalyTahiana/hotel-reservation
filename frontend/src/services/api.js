const API = import.meta.env.VITE_API_URL || "/api";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : null;
}

function parseErrors(data, status) {
  const fields = {};
  let message = "";
  if (!data || typeof data !== "object") {
    return { message: status >= 500 ? "Erreur du serveur. Réessayez plus tard." : "Une erreur est survenue.", fields };
  }
  if (Array.isArray(data)) return { message: data.join(" "), fields };
  if (data.detail) message = String(data.detail);
  for (const [key, value] of Object.entries(data)) {
    if (key === "detail") continue;
    const text = Array.isArray(value) ? value.join(" ") : String(value);
    if (key === "non_field_errors") message = message ? `${message} ${text}` : text;
    else fields[key] = text;
  }
  if (!message) message = Object.keys(fields).length ? "Veuillez corriger les champs indiqués." : "Une erreur est survenue.";
  return { message, fields };
}

export class ApiError extends Error {
  constructor(status, data) {
    const { message, fields } = parseErrors(data, status);
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

export async function request(path, { method = "GET", body, params } = {}) {
  const url = new URL(API + path, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const headers = { Accept: "application/json" };
  const options = { method, headers, credentials: "include" };
  if (body !== undefined) {
    if (body instanceof FormData) options.body = body;
    else {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
  }
  if (method !== "GET") headers["X-CSRFToken"] = getCookie("csrftoken") || "";

  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ApiError(0, { detail: "Impossible de joindre le serveur. Vérifiez que le backend Django est démarré." });
  }
  if (response.status === 204) return null;
  let data = null;
  try {
    data = await response.json();
  } catch {
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

export const get = (path, params) => request(path, { params });
export const post = (path, body) => request(path, { method: "POST", body });
export const patch = (path, body) => request(path, { method: "PATCH", body });
export const del = (path) => request(path, { method: "DELETE" });
