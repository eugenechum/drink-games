export function nameOf(players, id) {
  if (!id) return "";
  const p = players.find((p) => p.id === id);
  return p ? p.name : "?";
}
