import { useEffect, useState } from "react";
import Die from "../components/Die.jsx";
import { nameOf } from "../lib/players.js";

export default function PokerDice({ state, players, you, send }) {
  const [held, setHeld] = useState([false, false, false, false, false]);
  const you_ = state.players.find((p) => p.id === you.id);
  const rollsUsed = state.your_rolls_used;
  const done = you_?.done;
  const gameOver = state.phase === "game_over";

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

  function endGame() {
    if (window.confirm("End this game now for everyone?")) {
      send({ type: "end_game" });
    }
  }

  return (
    <div className="felt-table rounded-2xl p-6 w-full max-w-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-amber-100">Poker Dice</h2>
        {you.is_host && !gameOver && (
          <button
            onClick={endGame}
            className="text-amber-100/50 hover:text-amber-100 text-xs border border-amber-100/30 rounded px-2 py-1"
          >
            End Game
          </button>
        )}
      </div>

      {!gameOver && (
        <div className="flex flex-wrap justify-center gap-3">
          {state.players.map((p) => (
            <div key={p.id} className="px-4 py-2 rounded-xl border border-amber-100/20 text-center">
              <div className="text-amber-100 text-sm">{nameOf(players, p.id)}</div>
              <div className="text-amber-100/50 text-xs">
                {p.done ? "done" : `${p.rolls_used}/3 rolls`}
              </div>
              <div className="text-amber-100/40 text-xs">
                {p.wins}W - {p.losses}L
              </div>
            </div>
          ))}
        </div>
      )}

      {state.phase === "rolling" && (
        <div className="flex flex-col items-center gap-4">
          <div className="flex gap-3">
            {state.your_dice.map((v, i) =>
              rollsUsed === 0 ? (
                <div key={i} className="flex flex-col items-center gap-1">
                  <div className="die-face w-14 h-14 flex items-center justify-center text-lg opacity-30">
                    ?
                  </div>
                  <span className="h-4" />
                </div>
              ) : (
                <div key={i} className="flex flex-col items-center gap-1">
                  <Die value={v} held={held[i]} onClick={() => toggleHold(i)} size="w-14 h-14" />
                  <span className={`h-4 text-[11px] font-bold ${held[i] ? "text-chip-red" : "text-transparent"}`}>
                    HELD
                  </span>
                </div>
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

      {gameOver && <ResultsPanel state={state} players={players} you={you} send={send} />}

      {state.phase === "revealed" && !gameOver && you.is_host && (
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
              <div className="flex gap-2 mb-1">
                {dice.map((v, i) => (
                  <Die key={i} value={v} size="w-12 h-12" />
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

function ResultsPanel({ state, players, you, send }) {
  const ranked = [...state.players].sort((a, b) => b.wins - a.wins || a.losses - b.losses);
  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-amber-100 text-xl">Game ended</p>
      <div className="bg-black/30 rounded-xl p-4 w-full max-w-sm">
        <table className="w-full text-amber-100 text-sm">
          <thead>
            <tr className="text-amber-100/50 text-left">
              <th className="pb-2">Player</th>
              <th className="pb-2 text-center">Wins</th>
              <th className="pb-2 text-center">Losses</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((p) => (
              <tr key={p.id}>
                <td className="py-1">{nameOf(players, p.id)}</td>
                <td className="py-1 text-center">{p.wins}</td>
                <td className="py-1 text-center">{p.losses}</td>
              </tr>
            ))}
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
