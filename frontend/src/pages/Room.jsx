import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import QrCode from "../components/QrCode.jsx";
import LiarsDice from "../games/LiarsDice.jsx";
import PokerDice from "../games/PokerDice.jsx";
import Holdem from "../games/Holdem.jsx";
import { useRoomSocket } from "../lib/ws.js";
import { loadPlayer } from "../lib/storage.js";

const GAME_LABELS = {
  liars_dice: "Liar's Dice",
  poker_dice: "Poker Dice",
  holdem: "Texas Hold'em",
};

export default function Room() {
  const { code } = useParams();
  const navigate = useNavigate();
  const player = loadPlayer(code);

  useEffect(() => {
    if (!player) navigate(`/join/${code}`);
  }, [player, code, navigate]);

  const { state, error, connected, send } = useRoomSocket(code, player?.id);

  if (!player) return null;
  if (!state) {
    return (
      <Centered>
        <p className="text-amber-100/70">{connected ? "Loading room…" : "Connecting…"}</p>
      </Centered>
    );
  }

  const you = state.you;
  const players = state.room.players;
  const isHost = you?.is_host;
  const gameType = state.room.game_type;

  return (
    <div className="min-h-screen px-4 py-8 flex flex-col items-center">
      <div className="w-full max-w-2xl flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl text-amber-100">🎲 Drink Games</h1>
        <div className="text-amber-100/60 text-sm">Room {code}</div>
      </div>

      {error && (
        <div className="w-full max-w-2xl bg-chip-redDark text-white text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      {!gameType && (
        <Waiting code={code} players={players} isHost={isHost} send={send} you={you} />
      )}

      {gameType === "liars_dice" && (
        <LiarsDice state={state.game} players={players} you={you} send={send} />
      )}
      {gameType === "poker_dice" && (
        <PokerDice state={state.game} players={players} you={you} send={send} />
      )}
      {gameType === "holdem" && <Holdem state={state.game} players={players} you={you} send={send} />}
    </div>
  );
}

function Waiting({ code, players, isHost, send }) {
  const joinUrl = `${window.location.origin}/join/${code}`;
  const canStart = players.length >= 2;

  return (
    <div className="felt-table rounded-2xl p-8 w-full max-w-2xl flex flex-col items-center gap-6">
      <div className="flex flex-col items-center gap-3">
        <QrCode value={joinUrl} />
        <div className="text-amber-100/70 text-sm">or enter code</div>
        <div className="text-5xl font-display tracking-[0.3em] text-amber-100">{code}</div>
      </div>

      <div className="w-full">
        <h2 className="text-amber-100/70 text-sm mb-2 uppercase tracking-wide">
          Players ({players.length}/8)
        </h2>
        <ul className="flex flex-wrap gap-2">
          {players.map((p) => (
            <li
              key={p.id}
              className={`px-3 py-1.5 rounded-full text-sm border ${
                p.connected ? "border-amber-100/40 text-amber-100" : "border-amber-100/10 text-amber-100/30"
              }`}
            >
              {p.name}
              {p.is_host && " 👑"}
              {!p.connected && " (away)"}
            </li>
          ))}
        </ul>
      </div>

      {isHost ? (
        <div className="w-full flex flex-col gap-3">
          <h2 className="text-amber-100/70 text-sm uppercase tracking-wide">Choose a game</h2>
          {!canStart && (
            <p className="text-amber-100/50 text-sm">Need at least 2 players to start.</p>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {Object.entries(GAME_LABELS).map(([key, label]) => (
              <button
                key={key}
                disabled={!canStart}
                onClick={() => send({ type: "start_game", game: key })}
                className="bg-chip-red hover:bg-chip-redDark disabled:opacity-40 disabled:hover:bg-chip-red transition text-white font-semibold py-4 rounded-lg"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-amber-100/60">Waiting for the host to start a game…</p>
      )}
    </div>
  );
}

function Centered({ children }) {
  return <div className="min-h-screen flex items-center justify-center">{children}</div>;
}
