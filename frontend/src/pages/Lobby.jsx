import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createRoom, joinRoom } from "../lib/api.js";
import { savePlayer } from "../lib/storage.js";

export default function Lobby() {
  const { code: codeFromUrl } = useParams();
  const navigate = useNavigate();
  const [mode, setMode] = useState(codeFromUrl ? "join" : null);
  const [name, setName] = useState("");
  const [code, setCode] = useState(codeFromUrl || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleHost(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await createRoom(name);
      savePlayer(res.code, { id: res.player_id, name: res.player_name });
      navigate(`/room/${res.code}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  async function handleJoin(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const cleanCode = code.trim();
      const res = await joinRoom(cleanCode, name);
      savePlayer(res.code, { id: res.player_id, name: res.player_name });
      navigate(`/room/${res.code}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <h1 className="font-display text-4xl md:text-5xl text-amber-100 mb-2 tracking-wide">
        🎲 Drink Games
      </h1>
      <p className="text-amber-100/60 mb-10">Liar's Dice · Poker Dice · Texas Hold'em</p>

      <div className="felt-table rounded-2xl p-8 w-full max-w-sm">
        {mode === null && (
          <div className="flex flex-col gap-4">
            <button
              onClick={() => setMode("host")}
              className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold py-3 rounded-lg text-lg"
            >
              Host a Game
            </button>
            <button
              onClick={() => setMode("join")}
              className="bg-black/40 hover:bg-black/60 border border-amber-100/30 transition text-amber-100 font-semibold py-3 rounded-lg text-lg"
            >
              Join a Game
            </button>
          </div>
        )}

        {mode === "host" && (
          <form onSubmit={handleHost} className="flex flex-col gap-4">
            <label className="text-amber-100/80 text-sm">Your name</label>
            <input
              autoFocus
              required
              maxLength={24}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Host name"
              className="rounded-lg px-4 py-3 bg-black/30 border border-amber-100/30 text-amber-100 placeholder:text-amber-100/40 outline-none focus:border-chip-red"
            />
            <button
              disabled={busy}
              className="bg-chip-red hover:bg-chip-redDark disabled:opacity-50 transition text-white font-semibold py-3 rounded-lg"
            >
              {busy ? "Creating room…" : "Create Room"}
            </button>
            <button type="button" onClick={() => setMode(null)} className="text-amber-100/50 text-sm">
              ← back
            </button>
          </form>
        )}

        {mode === "join" && (
          <form onSubmit={handleJoin} className="flex flex-col gap-4">
            <label className="text-amber-100/80 text-sm">Room code</label>
            <input
              autoFocus={!codeFromUrl}
              required
              pattern="[0-9]{4}"
              maxLength={4}
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="0000"
              className="rounded-lg px-4 py-3 bg-black/30 border border-amber-100/30 text-amber-100 text-center text-2xl tracking-[0.5em] placeholder:text-amber-100/30 outline-none focus:border-chip-red"
            />
            <label className="text-amber-100/80 text-sm">Your name</label>
            <input
              required
              maxLength={24}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="rounded-lg px-4 py-3 bg-black/30 border border-amber-100/30 text-amber-100 placeholder:text-amber-100/40 outline-none focus:border-chip-red"
            />
            <button
              disabled={busy}
              className="bg-chip-red hover:bg-chip-redDark disabled:opacity-50 transition text-white font-semibold py-3 rounded-lg"
            >
              {busy ? "Joining…" : "Join Room"}
            </button>
            {!codeFromUrl && (
              <button type="button" onClick={() => setMode(null)} className="text-amber-100/50 text-sm">
                ← back
              </button>
            )}
          </form>
        )}

        {error && <p className="text-red-300 text-sm mt-4 text-center">{error}</p>}
      </div>
    </div>
  );
}
