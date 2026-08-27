import { useState } from "react";
import { nameOf } from "../lib/players.js";

function Card({ label }) {
  const isRed = label.includes("♥") || label.includes("♦");
  return (
    <div className={`card-face w-10 h-14 flex items-center justify-center font-bold text-lg ${isRed ? "text-red-600" : ""}`}>
      {label}
    </div>
  );
}

export default function Holdem({ state, players, you, send }) {
  const [raiseTo, setRaiseTo] = useState(0);
  const isBetting = ["preflop", "flop", "turn", "river"].includes(state.phase);
  const isYourTurn = isBetting && state.current_turn === you.id;
  const me = state.players.find((p) => p.id === you.id);
  const toCall = state.current_bet - (me?.committed_street || 0);
  const maxRaise = (me?.stack || 0) + (me?.committed_street || 0);
  const minRaiseTo = state.current_bet + state.min_raise;

  function act(action) {
    send({ type: "game_action", action });
  }

  function endGame() {
    if (window.confirm("End this game now for everyone? Any hand in progress will be refunded.")) {
      send({ type: "end_game" });
    }
  }

  return (
    <div className="felt-table rounded-2xl p-6 w-full max-w-3xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-amber-100">Texas Hold'em</h2>
        <div className="flex items-center gap-3">
          <span className="text-amber-100/50 text-sm">
            Hand #{state.hand_number} · Pot {state.pot}
          </span>
          {you.is_host && state.phase !== "game_over" && (
            <button
              onClick={endGame}
              className="text-amber-100/50 hover:text-amber-100 text-xs border border-amber-100/30 rounded px-2 py-1"
            >
              End Game
            </button>
          )}
        </div>
      </div>

      <div className="flex justify-center gap-2">
        {state.community.length === 0 && <p className="text-amber-100/30 text-sm">— pre-flop —</p>}
        {state.community.map((c, i) => (
          <Card key={i} label={c} />
        ))}
      </div>

      <div className="flex flex-wrap justify-center gap-3">
        {state.players.map((p) => (
          <PlayerSeat key={p.id} p={p} state={state} players={players} you={you} send={send} />
        ))}
      </div>

      <div className="flex flex-col items-center gap-2">
        <p className="text-amber-100/70 text-sm">Your hand</p>
        <div className="flex gap-2">
          {state.your_hole_cards.map((c, i) => (
            <Card key={i} label={c} />
          ))}
          {state.your_hole_cards.length === 0 && (
            <p className="text-amber-100/30 text-sm">not in this hand</p>
          )}
        </div>
      </div>

      {isYourTurn && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={() => act({ type: "fold" })}
            className="bg-black/50 hover:bg-black/70 border border-amber-100/40 transition text-amber-100 font-semibold px-4 py-2 rounded-lg"
          >
            Fold
          </button>
          <button
            onClick={() => act(toCall === 0 ? { type: "check" } : { type: "call" })}
            className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
          >
            {toCall === 0 ? "Check" : `Call ${toCall}`}
          </button>
          {maxRaise > state.current_bet && (
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={Math.min(minRaiseTo, maxRaise)}
                max={maxRaise}
                value={raiseTo || minRaiseTo}
                onChange={(e) => setRaiseTo(Number(e.target.value))}
                className="w-24 rounded px-2 py-2 bg-black/30 border border-amber-100/30 text-amber-100"
              />
              <button
                onClick={() => act({ type: "raise", to: Math.min(Math.max(raiseTo || minRaiseTo, minRaiseTo), maxRaise) })}
                className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
              >
                Raise
              </button>
              <button
                onClick={() => act({ type: "raise", to: maxRaise })}
                className="bg-black/50 hover:bg-black/70 border border-amber-100/40 transition text-amber-100 font-semibold px-4 py-2 rounded-lg"
              >
                All In
              </button>
            </div>
          )}
        </div>
      )}
      {isBetting && !isYourTurn && (
        <p className="text-center text-amber-100/60">
          Waiting for {nameOf(players, state.current_turn)}…
        </p>
      )}

      {state.phase === "hand_complete" && state.last_result && (
        <ResultPanel result={state.last_result} players={players} />
      )}

      {me?.busted && (
        <div className="text-center">
          {state.buyins_open ? (
            <button
              onClick={() => send({ type: "rebuy" })}
              className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
            >
              Rebuy (1000 chips)
            </button>
          ) : (
            <p className="text-amber-100/50 text-sm">You're out — buy-ins are closed.</p>
          )}
        </div>
      )}

      {state.phase === "hand_complete" && you.is_host && (
        <div className="flex justify-center gap-3">
          <button
            onClick={() => send({ type: "next_round" })}
            className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
          >
            Deal Next Hand
          </button>
          {state.buyins_open && (
            <button
              onClick={() => send({ type: "close_buyins" })}
              className="bg-black/50 hover:bg-black/70 border border-amber-100/40 transition text-amber-100 font-semibold px-4 py-2 rounded-lg"
            >
              Close Buy-ins
            </button>
          )}
        </div>
      )}

      {state.phase === "game_over" && (
        <ResultsPanel state={state} players={players} you={you} send={send} />
      )}
    </div>
  );
}

function ResultsPanel({ state, players, you, send }) {
  const ranked = [...state.players].sort((a, b) => b.stack - a.stack);
  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-amber-100 text-xl">
        {state.winner ? `🏆 ${nameOf(players, state.winner)} takes the table!` : "Game ended early"}
      </p>
      <div className="bg-black/30 rounded-xl p-4 w-full max-w-sm">
        <table className="w-full text-amber-100 text-sm">
          <thead>
            <tr className="text-amber-100/50 text-left">
              <th className="pb-2">Player</th>
              <th className="pb-2 text-center">Bought in</th>
              <th className="pb-2 text-center">Cashed out</th>
              <th className="pb-2 text-center">Net</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((p) => {
              const net = p.stack - p.total_buyin;
              return (
                <tr key={p.id}>
                  <td className="py-1">{nameOf(players, p.id)}</td>
                  <td className="py-1 text-center">{p.total_buyin}</td>
                  <td className="py-1 text-center">{p.stack}</td>
                  <td className={`py-1 text-center ${net > 0 ? "text-green-400" : net < 0 ? "text-chip-red" : ""}`}>
                    {net > 0 ? "+" : ""}
                    {net}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {you.is_host && (
        <button
          onClick={() => send({ type: "back_to_lobby" })}
          className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
        >
          Back to Game Picker
        </button>
      )}
    </div>
  );
}

function PlayerSeat({ p, state, players, you }) {
  const isTurn = state.current_turn === p.id;
  const isButton = state.button === p.id;
  const hole = state.hole_cards?.[p.id];
  return (
    <div
      className={`px-3 py-2 rounded-xl border text-center min-w-[110px] ${
        isTurn ? "border-chip-red bg-chip-red/20" : "border-amber-100/20"
      } ${p.folded ? "opacity-40" : ""}`}
    >
      <div className="text-amber-100 text-sm">
        {nameOf(players, p.id)} {isButton && "🔘"} {p.id === you.id && "(you)"}
      </div>
      <div className="text-amber-100/60 text-xs">
        {p.busted ? "busted" : `${p.stack} chips`}
      </div>
      {p.committed_street > 0 && (
        <div className="text-chip-red text-xs">bet {p.committed_street}</div>
      )}
      {p.folded && <div className="text-amber-100/40 text-xs">folded</div>}
      {p.all_in && !p.folded && <div className="text-amber-100/40 text-xs">all-in</div>}
      {hole && (
        <div className="flex gap-1 justify-center mt-1">
          {hole.map((c, i) => (
            <span key={i} className="text-amber-100 text-xs">
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultPanel({ result, players }) {
  return (
    <div className="bg-black/30 rounded-xl p-4 flex flex-col gap-2">
      <p className="text-amber-100/70 text-xs text-center uppercase tracking-wide">{result.reason}</p>
      {result.pots.map((pot, i) => (
        <p key={i} className="text-center text-amber-100">
          Pot {i + 1}: <b>{pot.amount}</b> to{" "}
          <b>{pot.winners.map((w) => nameOf(players, w)).join(" & ")}</b>
          {pot.hand && ` (${pot.hand})`}
        </p>
      ))}
    </div>
  );
}
