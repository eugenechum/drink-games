import { useEffect, useState } from "react";
import { nameOf } from "../lib/players.js";

const FACE_LABEL = { 1: "9", 2: "10", 3: "J", 4: "Q", 5: "K", 6: "A" };

function Die({ value, held, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`die-face w-12 h-12 flex items-center justify-center text-xl font-bold ${
        held ? "ring-4 ring-chip-red" : ""
      } ${onClick ? "cursor-pointer" : "cursor-default"}`}
    >
      {FACE_LABEL[value] ?? "?"}
    </button>
  );
}

export default function PokerDice({ state, players, you, send }) {
  const [held, setHeld] = useState([false, false, false, false, false]);
  const you_ = state.players.find((p) => p.id === you.id);
  const rollsUsed = state.your_rolls_used;
  const done = you_?.done;

  useEffect(() => {
    if (rollsUsed === 0) setHeld([false, false, false, false, false]);
  }, [rollsUsed]);

  function toggleHold(i) {
    if (rollsUsed === 0 || done) return;
    setHeld((h) => h.map((v, idx) => (idx === i ? !v : v)));
  }

  function roll() {
    send({ type: "game_action", action: { type: "roll", keep: held } });
  }

  function stand() {
    send({ type: "game_action", action: { type: "stand" } });
  }

  return (
    <div className="felt-table rounded-2xl p-6 w-full max-w-2xl flex flex-col gap-6">
      <h2 className="font-display text-2xl text-amber-100 text-center">Poker Dice</h2>

      <div className="flex flex-wrap justify-center gap-3">
        {state.players.map((p) => (
          <div key={p.id} className="px-4 py-2 rounded-xl border border-amber-100/20 text-center">
            <div className="text-amber-100 text-sm">{nameOf(players, p.id)}</div>
            <div className="text-amber-100/50 text-xs">
              {p.done ? "done" : `${p.rolls_used}/3 rolls`}
            </div>
          </div>
        ))}
      </div>

      {state.phase === "rolling" && (
        <div className="flex flex-col items-center gap-4">
          <div className="flex gap-2">
            {state.your_dice.map((v, i) =>
              rollsUsed === 0 ? (
                <div key={i} className="die-face w-12 h-12 flex items-center justify-center text-xl font-bold opacity-30">
                  ?
                </div>
              ) : (
                <Die key={i} value={v} held={held[i]} onClick={() => toggleHold(i)} />
              )
            )}
          </div>
          {!done && (
            <p className="text-amber-100/50 text-xs">
              {rollsUsed > 0 && "Tap dice to hold them, then roll the rest."}
            </p>
          )}
          {!done ? (
            <div className="flex gap-3">
              <button
                onClick={roll}
                className="bg-chip-red hover:bg-chip-redDark transition text-white font-semibold px-5 py-2 rounded-lg"
              >
                {rollsUsed === 0 ? "Roll" : `Reroll (${3 - rollsUsed} left)`}
              </button>
              {rollsUsed > 0 && (
                <button
                  onClick={stand}
                  className="bg-black/50 hover:bg-black/70 border border-amber-100/40 transition text-amber-100 font-semibold px-5 py-2 rounded-lg"
                >
                  Stand
                </button>
              )}
            </div>
          ) : (
            <p className="text-amber-100/60">Waiting for other players…</p>
          )}
        </div>
      )}

      {state.phase === "revealed" && state.last_result && (
        <RevealPanel result={state.last_result} players={players} />
      )}

      {state.phase === "revealed" && you.is_host && (
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
    <div className="bg-black/30 rounded-xl p-4 flex flex-col gap-4">
      <div className="flex flex-wrap justify-center gap-4">
        {Object.entries(result.dice).map(([pid, dice]) => {
          const isWinner = result.winners.includes(pid);
          const isLoser = result.losers.includes(pid) && !isWinner;
          return (
            <div
              key={pid}
              className={`text-center rounded-lg p-2 ${isWinner ? "bg-chip-red/20 ring-2 ring-chip-red" : ""}`}
            >
              <div className="text-amber-100 text-sm mb-1">
                {nameOf(players, pid)} {isWinner && "🏆"} {isLoser && "💧"}
              </div>
              <div className="flex gap-1 mb-1">
                {dice.map((v, i) => (
                  <div
                    key={i}
                    className="die-face w-9 h-9 flex items-center justify-center text-base font-bold"
                  >
                    {FACE_LABEL[v]}
                  </div>
                ))}
              </div>
              <div className="text-amber-100/60 text-xs">{result.scores[pid].category}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
