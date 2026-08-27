async function request(path, options) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function createRoom(hostName) {
  return request("/rooms", { method: "POST", body: JSON.stringify({ host_name: hostName }) });
}

export function joinRoom(code, name) {
  return request(`/rooms/${code}/join`, { method: "POST", body: JSON.stringify({ name }) });
}

export function roomInfo(code) {
  return request(`/rooms/${code}`);
}
