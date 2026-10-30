const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export { API_BASE_URL };

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();
      if (body?.detail) {
        message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // The response did not contain JSON; keep the generic message.
    }

    throw new Error(message);
  }

  return response.json();
}

export function getCounter() {
  return request("/api/counter");
}

export function incrementCounter() {
  return request("/api/counter/increment", { method: "POST" });
}

export function decrementCounter() {
  return request("/api/counter/decrement", { method: "POST" });
}
