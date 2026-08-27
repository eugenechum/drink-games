import { useState } from "react";
import { nameOf } from "../lib/players.js";

function Die({ value, hidden }) {
  return (
    <div className="die-face w-9 h-9 flex items-center justify-center text-lg font-bold">
      {hidden ? "?" : value}
    </div>
  );
}

export default function LiarsDice({ state, players, you, send }) {
  const [qty, setQty] = useState(1);
  const [face, setFace] = useState(2);

  const isYourTurn = state.current_turn === you.id;
  const totalDice = state.players.reduce((sum, p) => sum + p.dice_count, 0);

  function bid(e) {
    e.preventDefault();
    send({ type: "game_action", action: { type: "bid", qty: Number(qty), face: Number(face) } });
  }

  function callLiar() {
    send({ type: "game_action", action: { type: "call_liar" } });
  }

  return (
    <div className="felt-table rounded-2xl p-6 w-full max-w-2xl flex flex-col gap-6">
      <h2 className="font-display text-2xl text-amber-100 text-center">Liar's Dice</h2>

      <div className="flex flex-wrap justify-center gap-3">
        {state.players.map((p) => (
          <div
            key={p.id}
            className={`px-4 py-2 rounded-xl border ${
              state.current_turn === p.id ? "border-chip-red bg-chip-red/20" : "border-amber-100/20"
            }`}
          >
            <div className="text-amber-100 text-sm mb-1">{nameOf(players, p.id)}</div>
            <div className="flex gap-1">
              {Array.from({ length: p.dice_count }).map((_, i) => (
                <Die key={i} hidden />
              ))}
              {p.dice_count === 0 && <span className="text-amber-100/30 text-xs">out</span>}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center text-amber-100">
        {state.current_bid ? (
          <p>
            Current bid: <b>{state.current_bid.qty}</b> × face <b>{state.current_bid.face}</b>
            {state.current_bid.face === 1 && " (wild)"}
          </p>
        ) : (
          <p className="text-amber-100/60">No bid yet — {nameOf(players, state.current_turn)} opens.</p>
        )}
        <p className="text-amber-100/50 text-sm">{totalDice} dice in play</p>
      </div>

      <div className="flex flex-col items-center gap-2">
        <p className="text-amber-100/70 text-sm">Your dice</p>
        <div className="flex gap-2">
          {state.your_dice.map((v, i) => (
            <Die key={i} value={v} />
          ))}
        </div>
      </div>

      {state.phase === "bidding" && isYourTurn && (
        <form onSubmit={bid} className="flex flex-wrap items-end justify-center gap-3">
          <div className="flex flex-col">
            <label className="text-amber-100/60 text-xs">Quantity</label>
            <input
              type="number"
              min={1}
              max={totalDice}
              value={qty}
              onChange={(e) => setQty(e.target.value)}
              className="w-20 rounded px-2 py-1 bg-black/30 border border-amber-100/30 text-amber-100"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-amber-100/60 text-xs">Face</label>
            <select
              value={face}
              onChange={(e) => setFace(e.target.value)}
              className="w-20 rounded px-2 py-1 bg-black/30 border border-amber-100/30 text-amber-100"
            >
              {[1, 2, 3, 4, 5, 6].map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
          <button className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg">
            Bid
          </button>
          {state.current_bid && (
            <button
              type="button"
              onClick={callLiar}
              className="bg-black/50 hover:bg-black/70 border border-amber-100/40 transition text-amber-100 font-semibold px-4 py-2 rounded-lg"
            >
              Call Liar!
            </button>
          )}
        </form>
      )}

      {state.phase === "bidding" && !isYourTurn && (
        <p className="text-center text-amber-100/60">
          Waiting for {nameOf(players, state.current_turn)}…
        </p>
      )}

      {state.phase !== "bidding" && state.last_result && (
        <RevealPanel result={state.last_result} players={players} />
      )}

      {state.winner && (
        <div className="text-center">
          <p className="text-amber-100 text-xl mb-3">🏆 {nameOf(players, state.winner)} wins!</p>
          {you.is_host && (
            <button
              onClick={() => send({ type: "back_to_lobby" })}
              className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
            >
              Back to Game Picker
            </button>
          )}
        </div>
      )}

      {state.phase === "revealed" && !state.winner && you.is_host && (
        <div className="text-center">
          <button
            onClick={() => send({ type: "next_round" })}
            className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-4 py-2 rounded-lg"
          >
            Next Round
          </button>
        </div>
      )}
    </div>
  );
}

function RevealPanel({ result, players }) {
  return (
    <div className="bg-black/30 rounded-xl p-4 flex flex-col gap-3">
      <p className="text-amber-100 text-center">
        Bid was <b>{result.bid_was_true ? "TRUE" : "a LIE"}</b> — actual count of {result.bid.face}s
        {result.bid.face !== 1 && " (incl. wild 1s)"}: <b>{result.actual_count}</b> vs bid{" "}
        <b>{result.bid.qty}</b>
      </p>
      <p className="text-center text-chip-red font-semibold">
        {nameOf(players, result.loser)} loses a die{result.eliminated && " and is eliminated!"}
      </p>
      <div className="flex flex-wrap justify-center gap-4">
        {Object.entries(result.reveal).map(([pid, dice]) => (
          <div key={pid} className="text-center">
            <div className="text-amber-100/70 text-xs mb-1">{nameOf(players, pid)}</div>
            <div className="flex gap-1">
              {dice.map((v, i) => (
                <Die key={i} value={v} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
