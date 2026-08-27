export function savePlayer(code, player) {
  localStorage.setItem(`dg_player_${code}`, JSON.stringify(player));
}

export function loadPlayer(code) {
  const raw = localStorage.getItem(`dg_player_${code}`);
  return raw ? JSON.parse(raw) : null;
}
